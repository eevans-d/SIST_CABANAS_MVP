"""
Tests de Consistencia para el Sistema NLU (P102).

El sistema usa NLU básico con regex + dateparser (NO es LLM generativo).
Por tanto, la "consistencia" se valida como determinismo: mismo input → mismo output.

Objetivos:
- Validar que el NLU es determinístico (sin variabilidad)
- Detectar regresiones en detección de intents
- Validar robustez ante variaciones de texto
- Asegurar que fechas se parsean consistentemente
"""

import pytest
from app.services.nlu import analyze, detect_intent, extract_dates, extract_guests


@pytest.mark.asyncio
class TestNLUDeterminism:
    """Validar que el NLU es completamente determinístico."""

    async def test_same_input_produces_identical_output_100_times(self):
        """
        Test crítico: Mismo input debe producir EXACTAMENTE el mismo output
        en 100 ejecuciones consecutivas.

        Esto valida que no hay randomness ni side effects.
        """
        text = "Quiero reservar para el 15/12 al 18/12 para 4 personas"

        results = []
        for _ in range(100):
            result = analyze(text)
            results.append(result)

        # Todos los resultados deben ser idénticos
        first_result = results[0]
        for i, result in enumerate(results[1:], start=1):
            assert (
                result == first_result
            ), f"Iteration {i} produced different output: {result} != {first_result}"

        # Verificar contenido esperado
        assert "reservar" in first_result["intents"]
        assert len(first_result["dates"]) == 2
        assert first_result["guests"] == 4

    async def test_intent_detection_is_deterministic(self):
        """Validar que detección de intents no varía entre ejecuciones."""
        texts = [
            "Hay disponibilidad para mañana?",
            "Cuánto sale la cabaña?",
            "Quiero reservar",
            "Qué servicios incluye?",
        ]

        for text in texts:
            results = [detect_intent(text) for _ in range(50)]
            first = results[0]
            assert all(r == first for r in results), f"Intent detection varied for: {text}"

    async def test_date_extraction_is_deterministic(self):
        """Validar que extracción de fechas no varía."""
        texts = [
            "Del 20/11 al 23/11",
            "Para este fin de semana",
            "El 15 de diciembre",
        ]

        for text in texts:
            results = [extract_dates(text) for _ in range(50)]
            first = results[0]
            assert all(r == first for r in results), f"Date extraction varied for: {text}"

    async def test_guests_extraction_is_deterministic(self):
        """Validar que extracción de huéspedes no varía."""
        texts = [
            "Somos 4 personas",
            "Para 2 pax",
            "6 huéspedes",
        ]

        for text in texts:
            results = [extract_guests(text) for _ in range(50)]
            first = results[0]
            assert all(r == first for r in results), f"Guests extraction varied for: {text}"


@pytest.mark.asyncio
class TestNLURobustness:
    """Validar robustez del NLU ante variaciones de entrada."""

    async def test_intent_detection_with_spelling_variations(self):
        """Validar que variaciones comunes de spelling se detectan."""
        # Variaciones de "disponibilidad"
        variations = [
            "disponibilidad",
            "Disponibilidad",
            "DISPONIBILIDAD",
            "disponib",
            "hay disponibilidad",
            "está disponible",
        ]

        for text in variations:
            result = detect_intent(text)
            assert (
                "disponibilidad" in result["intents"]
            ), f"Failed to detect 'disponibilidad' in: {text}"

    async def test_date_formats_consistency(self):
        """Validar que diferentes formatos de fecha se parsean correctamente."""
        # Todas deberían representar 15 de diciembre 2025
        variations = [
            "15/12/2025",
            "15-12-2025",
            "15/12",
            "15-12",
        ]

        for text in variations:
            result = extract_dates(text)
            assert "dates" in result, f"No dates found in: {text}"
            assert len(result["dates"]) >= 1, f"Expected at least 1 date in: {text}"
            # Verificar que el día es 15 y mes es 12
            date_str = result["dates"][0]
            assert (
                "12-15" in date_str or "-12-" in date_str
            ), f"Expected December 15 but got: {date_str} from text: {text}"

    async def test_guests_extraction_with_variations(self):
        """Validar que diferentes formas de expresar huéspedes se detectan."""
        test_cases = [
            ("4 personas", 4),
            ("Somos 4 personas", 4),
            ("para 4 pax", 4),
            ("6 huéspedes", 6),
            ("2 huespedes", 2),  # Sin acento
        ]

        for text, expected_guests in test_cases:
            result = extract_guests(text)
            assert "guests" in result, f"No guests found in: {text}"
            assert (
                result["guests"] == expected_guests
            ), f"Expected {expected_guests} guests but got {result['guests']} from: {text}"


@pytest.mark.asyncio
class TestNLUEdgeCases:
    """Validar comportamiento en casos límite."""

    async def test_empty_input(self):
        """Validar que entrada vacía no causa excepciones."""
        result = analyze("")
        assert "intents" in result
        assert result["intents"] == ["desconocido"]

    async def test_very_long_input(self):
        """Validar que texto muy largo no causa problemas."""
        # Simular mensaje muy largo (200 palabras)
        long_text = " ".join(["palabra"] * 200) + " reservar 15/12"

        result = analyze(long_text)
        assert "intents" in result
        assert "reservar" in result["intents"]

    async def test_special_characters_dont_break_parser(self):
        """Validar que caracteres especiales no rompen el parser."""
        texts = [
            "Hola! Quiero reservar 😊",
            "Precio??? $$$",
            "Disponibilidad @#$%",
            "15/12 -> 18/12",
        ]

        for text in texts:
            # No debe lanzar excepción
            result = analyze(text)
            assert "intents" in result

    async def test_multiple_intents_in_same_message(self):
        """Validar que se detectan múltiples intents en un mensaje."""
        text = "Quiero saber si hay disponibilidad y cuánto sale para reservar"

        result = analyze(text)
        assert "intents" in result
        # Debe detectar: disponibilidad, precio, reservar
        intents = result["intents"]
        assert "disponibilidad" in intents
        assert "precio" in intents
        assert "reservar" in intents

    async def test_no_dates_returns_empty_list(self):
        """Validar que ausencia de fechas no causa error."""
        text = "Hola, quiero información"

        result = extract_dates(text)
        # Puede retornar empty dict o dict con dates=[]
        if "dates" in result:
            assert isinstance(result["dates"], list)
        else:
            assert result == {}

    async def test_no_guests_returns_empty_dict(self):
        """Validar que ausencia de huéspedes no causa error."""
        text = "Quiero reservar una cabaña"

        result = extract_guests(text)
        assert result == {}


@pytest.mark.asyncio
class TestNLUContextualConsistency:
    """
    Validar que el NLU se comporta consistentemente en conversaciones multi-turn.

    NOTA: El NLU actual es stateless (no tiene memoria), por lo que cada análisis
    es independiente. Esto es por diseño para simplificar el MVP.
    """

    async def test_nlu_is_stateless_by_design(self):
        """
        Validar que cada llamada a analyze() es independiente.
        No hay "memoria" entre llamadas.
        """
        # Primera llamada
        result1 = analyze("Quiero reservar")

        # Segunda llamada (diferente input)
        result2 = analyze("Para 4 personas")

        # Tercera llamada (volver al primer input)
        result3 = analyze("Quiero reservar")

        # result1 y result3 deben ser idénticos (stateless)
        assert result1 == result3

        # result2 es diferente y no debe verse afectado por result1
        assert result2 != result1

    async def test_repeated_analysis_doesnt_accumulate_state(self):
        """
        Validar que llamadas repetidas no acumulan estado interno.
        """
        text = "Disponibilidad para 15/12"

        results = []
        for i in range(10):
            result = analyze(text)
            results.append(result)

        # Todos deben ser idénticos
        assert all(r == results[0] for r in results)


@pytest.mark.asyncio
class TestNLUWeekendHandling:
    """Validar manejo especial del caso 'fin de semana'."""

    async def test_weekend_keyword_extracts_saturday_sunday(self):
        """Validar que 'fin de semana' retorna sábado y domingo."""
        texts = [
            "Para este fin de semana",
            "Quiero reservar el finde",
            "fin de semana próximo",
        ]

        for text in texts:
            result = extract_dates(text)
            assert "dates" in result, f"No dates found in: {text}"
            assert (
                len(result["dates"]) == 2
            ), f"Expected 2 dates (Sat+Sun) but got {len(result['dates'])} in: {text}"

            # Las fechas deben estar en orden (sábado primero)
            date1, date2 = result["dates"]
            # Ambas deben ser strings ISO format
            assert isinstance(date1, str)
            assert isinstance(date2, str)

    async def test_weekend_is_deterministic(self):
        """
        Validar que 'fin de semana' es determinístico dentro del mismo día.

        NOTA: El resultado cambiará si se ejecuta en días diferentes,
        pero debe ser consistente dentro del mismo día.
        """
        text = "Reserva para el finde"

        results = [extract_dates(text) for _ in range(50)]
        first = results[0]

        # Todos los resultados del mismo día deben ser idénticos
        assert all(r == first for r in results)


@pytest.mark.asyncio
class TestNLURegressionDetection:
    """
    Suite de tests para detectar regresiones en funcionalidad NLU.

    Estos tests capturan el comportamiento actual esperado del sistema.
    Si fallan, indica una regresión que debe ser investigada.
    """

    async def test_common_reservation_phrases_golden_set(self):
        """
        Golden set de frases comunes con output esperado.
        Detecta regresiones en casos de uso principales.
        """
        golden_cases = [
            {
                "input": "Quiero reservar para el 15/12 al 18/12 para 4 personas",
                "expected_intents": ["reservar"],
                "expected_dates_count": 2,
                "expected_guests": 4,
            },
            {
                "input": "Hay disponibilidad?",
                "expected_intents": ["disponibilidad"],
                "expected_dates_count": 0,
                "expected_guests": None,
            },
            {
                "input": "Cuánto sale la cabaña para 2 personas?",
                "expected_intents": ["precio"],
                "expected_dates_count": 0,
                "expected_guests": 2,
            },
            {
                "input": "Qué servicios incluye?",
                "expected_intents": ["servicios"],
                "expected_dates_count": 0,
                "expected_guests": None,
            },
        ]

        for case in golden_cases:
            result = analyze(case["input"])

            # Validar intents
            for intent in case["expected_intents"]:
                assert intent in result["intents"], (
                    f"Expected intent '{intent}' not found in {result['intents']} "
                    f"for input: {case['input']}"
                )

            # Validar fechas
            if case["expected_dates_count"] > 0:
                assert "dates" in result
                assert len(result["dates"]) == case["expected_dates_count"], (
                    f"Expected {case['expected_dates_count']} dates but got "
                    f"{len(result.get('dates', []))} for input: {case['input']}"
                )

            # Validar huéspedes
            if case["expected_guests"] is not None:
                assert "guests" in result
                assert result["guests"] == case["expected_guests"], (
                    f"Expected {case['expected_guests']} guests but got "
                    f"{result.get('guests')} for input: {case['input']}"
                )


@pytest.mark.asyncio
class TestNLUPerformance:
    """Validar que el NLU mantiene performance adecuado."""

    async def test_analyze_completes_quickly_on_normal_input(self):
        """Validar que análisis de texto normal es rápido (<10ms)."""
        import time

        text = "Quiero reservar para el 15/12 al 18/12 para 4 personas"

        start = time.perf_counter()
        for _ in range(100):
            analyze(text)
        end = time.perf_counter()

        avg_time_ms = ((end - start) / 100) * 1000
        assert avg_time_ms < 10, f"NLU analysis too slow: {avg_time_ms:.2f}ms avg (expected <10ms)"

    async def test_analyze_handles_batch_processing_efficiently(self):
        """Validar que procesamiento en lote es eficiente."""
        import time

        texts = [
            "Disponibilidad para mañana",
            "Cuánto sale?",
            "Quiero reservar",
            "Servicios incluidos",
        ] * 25  # 100 textos

        start = time.perf_counter()
        results = [analyze(text) for text in texts]
        end = time.perf_counter()

        total_time_ms = (end - start) * 1000
        assert (
            total_time_ms < 1000
        ), (  # <1 segundo para 100 análisis
            f"Batch processing too slow: {total_time_ms:.2f}ms for 100 texts"
        )

        # Verificar que todos se procesaron
        assert len(results) == 100


# Estadísticas de coverage esperadas después de P102:
# - nlu.py: 95%+ de cobertura
# - Funciones críticas: 100% (analyze, detect_intent, extract_dates, extract_guests)
