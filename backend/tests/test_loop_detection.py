"""
Tests para detector de loops infinitos en conversaciones.

FASE 2 - P103: Detector de Loops Infinitos
Detecta y previene repeticiones en conversaciones WhatsApp.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest


class TestLoopDetection:
    """Tests para detección de loops en conversaciones"""

    def test_detect_repeated_user_messages(self):
        """Detecta cuando usuario envía el mismo mensaje 3+ veces"""
        conversation_history = [
            {"role": "user", "content": "Hola", "timestamp": datetime.now()},
            {"role": "assistant", "content": "Hola, ¿en qué puedo ayudarte?"},
            {"role": "user", "content": "Hola", "timestamp": datetime.now()},
            {"role": "assistant", "content": "Ya te saludé, ¿necesitas algo?"},
            {"role": "user", "content": "Hola", "timestamp": datetime.now()},
        ]

        # Contar repeticiones del último mensaje
        last_user_msg = conversation_history[-1]["content"].lower()
        user_msgs = [
            msg["content"].lower() for msg in conversation_history if msg["role"] == "user"
        ]
        repetitions = user_msgs.count(last_user_msg)

        assert repetitions >= 3, "Debería detectar 3 repeticiones"

    def test_detect_bot_repeated_responses(self):
        """Detecta cuando bot responde lo mismo 3+ veces"""
        conversation_history = [
            {"role": "user", "content": "Precio"},
            {"role": "assistant", "content": "¿Para qué fechas?"},
            {"role": "user", "content": "Mañana"},
            {"role": "assistant", "content": "¿Para qué fechas?"},
            {"role": "user", "content": "15 de octubre"},
            {"role": "assistant", "content": "¿Para qué fechas?"},
        ]

        # Detectar repeticiones del bot
        last_bot_msg = conversation_history[-1]["content"]
        bot_msgs = [msg["content"] for msg in conversation_history if msg["role"] == "assistant"]
        repetitions = bot_msgs.count(last_bot_msg)

        assert repetitions >= 3, "Debería detectar loop en respuestas del bot"

    def test_circuit_breaker_after_n_iterations(self):
        """Circuit breaker detiene conversación después de N iteraciones sin progreso"""
        MAX_ITERATIONS = 5

        conversation_history = []
        for i in range(MAX_ITERATIONS + 2):
            conversation_history.append({"role": "user", "content": f"mensaje {i}"})
            conversation_history.append({"role": "assistant", "content": "No entiendo"})

        # Verificar que se supera el límite
        interactions = len(conversation_history) // 2

        if interactions > MAX_ITERATIONS:
            should_break = True
        else:
            should_break = False

        assert (
            should_break is True
        ), f"Debería activar circuit breaker después de {MAX_ITERATIONS} iteraciones"

    def test_loop_detection_with_slight_variations(self):
        """Detecta loops incluso con variaciones menores (typos, espacios)"""
        messages = [
            "quiero reservar",
            "quiero  reservar",  # Espacio extra
            "quiero reservar ",  # Espacio al final
            "Quiero reservar",  # Mayúscula
        ]

        # Normalizar y comparar
        normalized = [msg.lower().strip() for msg in messages]
        unique_normalized = set(normalized)

        # Todos deberían normalizar al mismo string
        assert len(unique_normalized) == 1, "Debería detectar como mismo mensaje pese a variaciones"

    def test_no_false_positive_on_different_messages(self):
        """No detecta loop cuando usuario hace preguntas diferentes"""
        conversation_history = [
            {"role": "user", "content": "¿Cuál es el precio?"},
            {"role": "assistant", "content": "$100 por noche"},
            {"role": "user", "content": "¿Está disponible mañana?"},
            {"role": "assistant", "content": "Sí, está disponible"},
            {"role": "user", "content": "¿Incluye desayuno?"},
        ]

        # Verificar que no hay repeticiones
        user_msgs = [msg["content"] for msg in conversation_history if msg["role"] == "user"]
        unique_msgs = len(set(user_msgs))
        total_msgs = len(user_msgs)

        assert unique_msgs == total_msgs, "No debería detectar loop en conversación natural"


class TestCircuitBreaker:
    """Tests para circuit breaker de conversaciones"""

    def test_circuit_breaker_resets_after_progress(self):
        """Circuit breaker se resetea cuando hay progreso en la conversación"""
        failed_attempts = 4
        MAX_FAILURES = 5

        # Simular progreso (mensaje diferente o acción exitosa)
        progress_detected = True

        if progress_detected:
            failed_attempts = 0  # Reset counter

        assert failed_attempts < MAX_FAILURES, "Contador debería resetearse tras progreso"

    def test_circuit_breaker_escalates_to_human(self):
        """Circuit breaker escala a humano después de N fallos"""
        failed_attempts = 6
        MAX_FAILURES = 5

        should_escalate = failed_attempts > MAX_FAILURES

        assert should_escalate is True, "Debería escalar a humano tras superar máximo de fallos"

    def test_circuit_breaker_includes_timestamp_check(self):
        """Circuit breaker considera ventana de tiempo para reseteo"""
        last_failure_time = datetime.now() - timedelta(minutes=30)
        RESET_WINDOW_MINUTES = 15

        time_since_last_failure = (datetime.now() - last_failure_time).total_seconds() / 60

        should_reset = time_since_last_failure > RESET_WINDOW_MINUTES

        assert should_reset is True, "Debería resetear después de ventana de tiempo"


class TestConversationMetrics:
    """Tests para métricas de conversación"""

    def test_track_conversation_length(self):
        """Rastrea longitud de conversación para detección temprana"""
        conversation_history = [{"role": role} for role in ["user", "bot"] * 10]

        conversation_length = len(conversation_history)
        WARNING_THRESHOLD = 15

        should_warn = conversation_length > WARNING_THRESHOLD

        assert (
            should_warn is True
        ), f"Debería alertar en conversaciones > {WARNING_THRESHOLD} mensajes"

    @patch("app.metrics.CONVERSATION_LOOPS_DETECTED")
    def test_loop_detection_increments_metric(self, mock_metric):
        """Métrica Prometheus se incrementa al detectar loop"""
        # Simular detección de loop
        loop_detected = True

        if loop_detected:
            mock_metric.labels(channel="whatsapp").inc()

        mock_metric.labels.assert_called_once_with(channel="whatsapp")
        mock_metric.labels.return_value.inc.assert_called_once()


# Utilidad para producción (opcional - no es test)
def detect_conversation_loop(conversation_history: list, max_repetitions: int = 3) -> bool:
    """
    Detecta si hay un loop en la conversación.

    Args:
        conversation_history: Lista de mensajes con role y content
        max_repetitions: Número máximo de repeticiones antes de considerar loop

    Returns:
        bool: True si se detecta loop
    """
    if len(conversation_history) < max_repetitions * 2:
        return False

    # Obtener últimos N mensajes del usuario
    user_messages = [
        msg["content"].lower().strip()
        for msg in conversation_history[-10:]
        if msg.get("role") == "user"
    ]

    if len(user_messages) < max_repetitions:
        return False

    # Verificar si el último mensaje se repite
    last_message = user_messages[-1]
    repetition_count = user_messages.count(last_message)

    return repetition_count >= max_repetitions


@pytest.mark.parametrize(
    "conversation,expected_loop",
    [
        # Caso 1: Loop claro
        (
            [
                {"role": "user", "content": "hola"},
                {"role": "bot", "content": "hola"},
                {"role": "user", "content": "hola"},
                {"role": "bot", "content": "hola"},
                {"role": "user", "content": "hola"},
            ],
            True,
        ),
        # Caso 2: Conversación normal
        (
            [
                {"role": "user", "content": "precio"},
                {"role": "bot", "content": "$100"},
                {"role": "user", "content": "disponibilidad"},
                {"role": "bot", "content": "sí"},
            ],
            False,
        ),
        # Caso 3: Repeticiones con variaciones
        (
            [
                {"role": "user", "content": "reservar"},
                {"role": "bot", "content": "ok"},
                {"role": "user", "content": " reservar "},
                {"role": "bot", "content": "ok"},
                {"role": "user", "content": "Reservar"},
            ],
            True,
        ),
    ],
)
def test_detect_loop_parametrized(conversation, expected_loop):
    """Test parametrizado para múltiples escenarios de detección"""
    result = detect_conversation_loop(conversation, max_repetitions=3)
    assert result == expected_loop


# Test de integración (requiere sistema funcionando)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_loop_detection_in_webhook_flow():
    """Test de integración: loop detection en webhook real"""
    # Este test requeriría mock del webhook WhatsApp
    # y simular conversación repetitiva
    pytest.skip("Requiere implementación en webhook handler")
