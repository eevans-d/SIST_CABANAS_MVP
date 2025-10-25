"""
Tests para métricas Prometheus de retry logic

Verificaciones incluidas:
- Métricas se declaran correctamente sin errores
- Decoradores funcionan con métricas habilitadas
- No hay regresiones en funcionalidad de retry
- Métricas exportables en /metrics endpoint
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.utils.retry import (
    RETRY_ATTEMPTS,
    RETRY_DELAYS,
    RETRY_EXHAUSTED,
    RetryExhausted,
    retry_async,
    retry_sync,
)
from prometheus_client import REGISTRY


class TestRetryMetricsDeclaration:
    """Tests para verificar que métricas están declaradas correctamente"""

    def test_retry_attempts_counter_exists(self):
        """Counter retry_attempts_total existe y es accesible"""
        assert RETRY_ATTEMPTS is not None
        # Prometheus añade _total automáticamente, el objeto usa el nombre base
        assert RETRY_ATTEMPTS._name in ["retry_attempts", "retry_attempts_total"]
        assert "operation" in RETRY_ATTEMPTS._labelnames
        assert "attempt_number" in RETRY_ATTEMPTS._labelnames
        assert "result" in RETRY_ATTEMPTS._labelnames

    def test_retry_delays_histogram_exists(self):
        """Histogram retry_delay_seconds existe y es accesible"""
        assert RETRY_DELAYS is not None
        assert RETRY_DELAYS._name == "retry_delay_seconds"
        assert "operation" in RETRY_DELAYS._labelnames

    def test_retry_exhausted_counter_exists(self):
        """Counter retry_exhausted_total existe y es accesible"""
        assert RETRY_EXHAUSTED is not None
        # Prometheus añade _total automáticamente, el objeto usa el nombre base
        assert RETRY_EXHAUSTED._name in ["retry_exhausted", "retry_exhausted_total"]
        assert "operation" in RETRY_EXHAUSTED._labelnames
        assert "error_type" in RETRY_EXHAUSTED._labelnames

    def test_metrics_are_registered_in_prometheus(self):
        """Métricas están registradas en el registry de Prometheus"""
        metric_names = []
        for m in REGISTRY.collect():
            metric_names.append(m.name)
            # También incluir nombres de samples (que tienen sufijos)
            for sample in m.samples:
                if sample.name not in metric_names:
                    # Extraer nombre base del sample
                    base_name = (
                        sample.name.replace("_total", "")
                        .replace("_count", "")
                        .replace("_bucket", "")
                        .replace("_sum", "")
                    )
                    if base_name not in metric_names:
                        metric_names.append(base_name)

        # Verificar que nuestras métricas están presentes (nombre base o con sufijo)
        assert any(
            "retry_attempts" in name for name in metric_names
        ), f"retry_attempts not found in {metric_names}"
        assert any(
            "retry_delay" in name for name in metric_names
        ), f"retry_delay not found in {metric_names}"
        assert any(
            "retry_exhausted" in name for name in metric_names
        ), f"retry_exhausted not found in {metric_names}"


class TestRetryWithMetricsEnabled:
    """Tests para verificar que retry funciona correctamente con métricas"""

    @pytest.mark.asyncio
    async def test_async_retry_with_metrics_succeeds_first_attempt(self):
        """Decorador async con métricas funciona en primer intento"""

        @retry_async(max_attempts=3, base_delay=0.1, operation_name="test_async_success")
        async def successful_operation():
            return "ok"

        result = await successful_operation()
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_async_retry_with_metrics_succeeds_after_retries(self):
        """Decorador async con métricas funciona tras reintentos"""
        call_count = 0

        @retry_async(max_attempts=3, base_delay=0.1, operation_name="test_async_retry")
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient error")
            return "ok"

        result = await failing_then_success()
        assert result == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_retry_with_metrics_fails_on_permanent_error(self):
        """Decorador async con métricas falla correctamente en errores permanentes"""

        @retry_async(max_attempts=3, base_delay=0.1, operation_name="test_async_permanent")
        async def permanent_failure():
            raise ValueError("Permanent error")

        with pytest.raises(ValueError, match="Permanent error"):
            await permanent_failure()

    @pytest.mark.asyncio
    async def test_async_retry_with_metrics_exhausts_retries(self):
        """Decorador async con métricas agota reintentos correctamente"""

        @retry_async(max_attempts=2, base_delay=0.1, operation_name="test_async_exhausted")
        async def always_fails():
            raise ConnectionError("Always fails")

        with pytest.raises(RetryExhausted):
            await always_fails()

    def test_sync_retry_with_metrics_succeeds(self):
        """Decorador sync con métricas funciona correctamente"""

        @retry_sync(max_attempts=3, base_delay=0.1, operation_name="test_sync_success")
        def sync_operation():
            return "sync_ok"

        result = sync_operation()
        assert result == "sync_ok"

    def test_sync_retry_with_metrics_retries_correctly(self):
        """Decorador sync con métricas reintenta correctamente"""
        call_count = 0

        @retry_sync(max_attempts=3, base_delay=0.1, operation_name="test_sync_retry")
        def sync_failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Transient")
            return "ok"

        result = sync_failing_then_success()
        assert result == "ok"
        assert call_count == 2


class TestMetricsCanBeIncremented:
    """Tests para verificar que métricas pueden ser incrementadas sin errores"""

    def test_retry_attempts_counter_can_increment(self):
        """Counter retry_attempts_total se puede incrementar"""
        # No debe lanzar excepción
        RETRY_ATTEMPTS.labels(operation="test_op", attempt_number="1", result="success").inc()

    def test_retry_delays_histogram_can_observe(self):
        """Histogram retry_delay_seconds puede registrar valores"""
        # No debe lanzar excepción
        RETRY_DELAYS.labels(operation="test_op").observe(1.5)

    def test_retry_exhausted_counter_can_increment(self):
        """Counter retry_exhausted_total se puede incrementar"""
        # No debe lanzar excepción
        RETRY_EXHAUSTED.labels(operation="test_op", error_type="ConnectionError").inc()


class TestMetricsIntegrationSmokeTest:
    """Smoke tests de integración con métricas"""

    @pytest.mark.asyncio
    @patch("app.utils.retry.RETRY_ATTEMPTS")
    async def test_metrics_are_called_on_success(self, mock_counter):
        """Métricas son llamadas cuando hay éxito"""
        mock_labels = MagicMock()
        mock_counter.labels.return_value = mock_labels

        @retry_async(max_attempts=3, base_delay=0.1, operation_name="test_metrics_call")
        async def operation():
            return "ok"

        await operation()

        # Verificar que se llamó labels con los parámetros correctos
        mock_counter.labels.assert_called()
        # Verificar que se llamó inc()
        mock_labels.inc.assert_called()

    @pytest.mark.asyncio
    @patch("app.utils.retry.RETRY_DELAYS")
    async def test_delay_histogram_is_called_on_retry(self, mock_histogram):
        """Histogram de delays es llamado en reintentos"""
        mock_labels = MagicMock()
        mock_histogram.labels.return_value = mock_labels
        call_count = 0

        @retry_async(max_attempts=3, base_delay=0.1, operation_name="test_histogram_call")
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Transient")
            return "ok"

        await failing_operation()

        # Verificar que se llamó observe() al menos una vez (por el retry)
        mock_labels.observe.assert_called()

    @pytest.mark.asyncio
    @patch("app.utils.retry.RETRY_EXHAUSTED")
    async def test_exhausted_counter_is_called_on_exhaustion(self, mock_counter):
        """Counter de exhaustion es llamado cuando se agotan intentos"""
        mock_labels = MagicMock()
        mock_counter.labels.return_value = mock_labels

        @retry_async(max_attempts=2, base_delay=0.1, operation_name="test_exhausted_call")
        async def always_fails():
            raise ConnectionError("Always fails")

        with pytest.raises(RetryExhausted):
            await always_fails()

        # Verificar que se llamó el counter de exhaustion
        mock_counter.labels.assert_called()
        mock_labels.inc.assert_called()


class TestMetricsDocumentation:
    """Tests para validar documentación de métricas"""

    def test_metrics_have_descriptions(self):
        """Métricas tienen descripciones útiles"""
        for metric in REGISTRY.collect():
            if metric.name in [
                "retry_attempts_total",
                "retry_delay_seconds",
                "retry_exhausted_total",
            ]:
                assert metric.documentation, f"Metric {metric.name} should have documentation"
                assert (
                    len(metric.documentation) > 10
                ), f"Metric {metric.name} documentation is too short"

    def test_histogram_has_reasonable_buckets(self):
        """Histogram tiene buckets razonables para delays esperados"""
        for metric in REGISTRY.collect():
            if metric.name == "retry_delay_seconds":
                # Verificar que hay buckets definidos
                buckets_found = False
                for sample in metric.samples:
                    if "_bucket" in sample.name:
                        buckets_found = True
                        # Verificar que el bucket está en rango razonable (0.5s - 32s)
                        le_value = sample.labels.get("le")
                        if le_value and le_value != "+Inf":
                            assert 0.1 <= float(le_value) <= 64.0
                assert buckets_found, "Histogram should have buckets"
