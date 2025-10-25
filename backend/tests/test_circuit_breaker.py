"""
Tests para Circuit Breaker Pattern

Verificaciones incluidas:
- Estados del circuit breaker (CLOSED, OPEN, HALF_OPEN)
- Transiciones de estado según threshold
- Recovery timeout funciona correctamente
- Métricas Prometheus registradas
- Requests rechazados cuando está OPEN
- Success threshold en HALF_OPEN
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpen,
    CircuitState,
    circuit_breaker,
)


class TestCircuitBreakerStates:
    """Tests para estados del circuit breaker"""

    @pytest.mark.asyncio
    async def test_circuit_starts_closed(self):
        """Circuit breaker inicia en estado CLOSED"""
        cb = CircuitBreaker("test_circuit")
        assert cb._state.state == CircuitState.CLOSED
        assert cb._state.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold_failures(self):
        """Circuit breaker abre después de alcanzar failure threshold"""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test_threshold", config)

        async def failing_func():
            raise ConnectionError("Fail")

        # Fallar 3 veces
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await cb.call(failing_func)

        # Debe estar OPEN
        assert cb._state.state == CircuitState.OPEN
        assert cb._state.failure_count == 3

    @pytest.mark.asyncio
    async def test_circuit_rejects_calls_when_open(self):
        """Circuit breaker rechaza llamadas cuando está OPEN"""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker("test_reject", config)

        async def failing_func():
            raise ConnectionError("Fail")

        # Abrir el circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await cb.call(failing_func)

        # Intentar llamar cuando está OPEN
        async def should_not_execute():
            return "executed"

        with pytest.raises(CircuitBreakerOpen):
            await cb.call(should_not_execute)

    @pytest.mark.asyncio
    async def test_circuit_transitions_to_half_open_after_timeout(self):
        """Circuit breaker pasa a HALF_OPEN después de recovery timeout"""
        config = CircuitBreakerConfig(
            failure_threshold=2, recovery_timeout=0.1  # 100ms para tests rápidos
        )
        cb = CircuitBreaker("test_half_open", config)

        async def failing_func():
            raise ConnectionError("Fail")

        # Abrir circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await cb.call(failing_func)

        assert cb._state.state == CircuitState.OPEN

        # Esperar recovery timeout
        await asyncio.sleep(0.15)

        # Verificar estado (llamando a _check_state)
        await cb._check_state()
        assert cb._state.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_circuit_closes_after_success_threshold_in_half_open(self):
        """Circuit breaker cierra después de success threshold en HALF_OPEN"""
        config = CircuitBreakerConfig(
            failure_threshold=2, recovery_timeout=0.1, success_threshold=2
        )
        cb = CircuitBreaker("test_close", config)

        call_count = 0

        async def sometimes_failing():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ConnectionError("Fail")
            return "success"

        # Abrir circuit (2 fallos)
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await cb.call(sometimes_failing)

        assert cb._state.state == CircuitState.OPEN

        # Esperar recovery
        await asyncio.sleep(0.15)
        await cb._check_state()
        assert cb._state.state == CircuitState.HALF_OPEN

        # 2 éxitos para cerrar
        result1 = await cb.call(sometimes_failing)
        assert result1 == "success"

        result2 = await cb.call(sometimes_failing)
        assert result2 == "success"

        # Debe estar CLOSED
        assert cb._state.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_reopens_on_failure_in_half_open(self):
        """Circuit breaker reabre si falla en estado HALF_OPEN"""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        cb = CircuitBreaker("test_reopen", config)

        async def failing_func():
            raise ConnectionError("Fail")

        # Abrir circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await cb.call(failing_func)

        # Esperar recovery
        await asyncio.sleep(0.15)
        await cb._check_state()
        assert cb._state.state == CircuitState.HALF_OPEN

        # Fallar en half-open
        with pytest.raises(ConnectionError):
            await cb.call(failing_func)

        # Debe volver a OPEN
        assert cb._state.state == CircuitState.OPEN


class TestCircuitBreakerMetrics:
    """Tests para métricas Prometheus del circuit breaker"""

    @pytest.mark.asyncio
    @patch("app.utils.circuit_breaker.CIRCUIT_BREAKER_FAILURES")
    async def test_failure_counter_increments(self, mock_counter):
        """Counter de fallos se incrementa correctamente"""
        mock_labels = MagicMock()
        mock_counter.labels.return_value = mock_labels

        cb = CircuitBreaker("test_metrics_fail")

        async def failing_func():
            raise ConnectionError("Fail")

        with pytest.raises(ConnectionError):
            await cb.call(failing_func)

        # Verificar que se llamó el counter
        mock_counter.labels.assert_called_with(circuit_name="test_metrics_fail")
        mock_labels.inc.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.utils.circuit_breaker.CIRCUIT_BREAKER_SUCCESSES")
    async def test_success_counter_increments(self, mock_counter):
        """Counter de éxitos se incrementa correctamente"""
        mock_labels = MagicMock()
        mock_counter.labels.return_value = mock_labels

        cb = CircuitBreaker("test_metrics_success")

        async def success_func():
            return "ok"

        await cb.call(success_func)

        mock_counter.labels.assert_called_with(circuit_name="test_metrics_success")
        mock_labels.inc.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.utils.circuit_breaker.CIRCUIT_BREAKER_REJECTIONS")
    async def test_rejection_counter_increments(self, mock_counter):
        """Counter de rechazos se incrementa cuando circuit está OPEN"""
        mock_labels = MagicMock()
        mock_counter.labels.return_value = mock_labels

        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker("test_metrics_reject", config)

        # Abrir circuit
        async def failing_func():
            raise ConnectionError("Fail")

        with pytest.raises(ConnectionError):
            await cb.call(failing_func)

        # Intentar llamar cuando está OPEN
        async def should_not_run():
            return "ok"

        with pytest.raises(CircuitBreakerOpen):
            await cb.call(should_not_run)

        # Verificar rejection counter
        mock_counter.labels.assert_called_with(circuit_name="test_metrics_reject")
        mock_labels.inc.assert_called()

    @pytest.mark.asyncio
    @patch("app.utils.circuit_breaker.CIRCUIT_BREAKER_STATE_CHANGES")
    async def test_state_change_counter_increments(self, mock_counter):
        """Counter de cambios de estado se incrementa en transiciones"""
        mock_labels = MagicMock()
        mock_counter.labels.return_value = mock_labels

        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker("test_metrics_state_change", config)

        # Provocar cambio de estado CLOSED → OPEN
        async def failing_func():
            raise ConnectionError("Fail")

        for _ in range(2):
            with pytest.raises(ConnectionError):
                await cb.call(failing_func)

        # Verificar que se registró cambio de estado
        mock_counter.labels.assert_called()
        mock_labels.inc.assert_called()


class TestCircuitBreakerDecorator:
    """Tests para decorador @circuit_breaker"""

    @pytest.mark.asyncio
    async def test_decorator_works_on_success(self):
        """Decorador funciona correctamente en operaciones exitosas"""

        @circuit_breaker(name="test_decorator_success", failure_threshold=3)
        async def successful_operation():
            return "ok"

        result = await successful_operation()
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_decorator_opens_circuit_on_failures(self):
        """Decorador abre circuit después de threshold"""
        call_count = 0

        @circuit_breaker(name="test_decorator_open", failure_threshold=2)
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Fail")

        # Fallar 2 veces
        with pytest.raises(ConnectionError):
            await failing_operation()

        with pytest.raises(ConnectionError):
            await failing_operation()

        # Tercera llamada debe ser rechazada (circuit OPEN)
        with pytest.raises(CircuitBreakerOpen):
            await failing_operation()

        # Solo se ejecutó 2 veces (no 3)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_decorator_respects_recovery_timeout(self):
        """Decorador respeta recovery timeout"""
        call_count = 0

        @circuit_breaker(name="test_decorator_recovery", failure_threshold=1, recovery_timeout=0.1)
        async def operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                raise ConnectionError("Fail")
            return "recovered"

        # Abrir circuit
        with pytest.raises(ConnectionError):
            await operation()

        # Inmediatamente rechazado
        with pytest.raises(CircuitBreakerOpen):
            await operation()

        # Esperar recovery
        await asyncio.sleep(0.15)

        # Debe permitir intento (HALF_OPEN)
        result = await operation()
        assert result == "recovered"


class TestCircuitBreakerThreadSafety:
    """Tests para verificar thread-safety con asyncio"""

    @pytest.mark.asyncio
    async def test_concurrent_calls_are_safe(self):
        """Llamadas concurrentes son manejadas correctamente"""
        cb = CircuitBreaker("test_concurrent")
        call_count = 0

        async def tracked_operation():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return "ok"

        # Ejecutar 10 llamadas concurrentes
        tasks = [cb.call(tracked_operation) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r == "ok" for r in results)
        assert call_count == 10

    @pytest.mark.asyncio
    async def test_concurrent_failures_tracked_correctly(self):
        """Fallos concurrentes son contados correctamente"""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker("test_concurrent_fail", config)

        async def failing_operation():
            raise ConnectionError("Fail")

        # 5 fallos concurrentes
        tasks = [cb.call(failing_operation) for _ in range(5)]

        with pytest.raises(ConnectionError):
            await asyncio.gather(*tasks, return_exceptions=False)

        # Circuit debe estar OPEN
        assert cb._state.state == CircuitState.OPEN
