"""
Tests para retry logic con exponential backoff.

Verificaciones incluidas:
- Cálculo correcto de backoff delays
- Distinción entre errores transitorios y permanentes
- Límite de reintentos
- Logging de cada intento
- Aplicación en WhatsApp service
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.utils.retry import (
    calculate_backoff_delay,
    is_transient_error,
    retry_async,
    retry_sync,
    RetryExhausted,
)


class TestBackoffCalculation:
    """Tests para cálculo de exponential backoff"""

    def test_backoff_increases_exponentially(self):
        """El delay crece exponencialmente: 1s, 2s, 4s, 8s, 16s..."""
        # Sin jitter para test predecible
        with patch('app.utils.retry.random.random', return_value=0.5):  # jitter=0
            assert 0.8 < calculate_backoff_delay(0, base_delay=1.0) < 1.2  # ~1s
            assert 1.6 < calculate_backoff_delay(1, base_delay=1.0) < 2.4  # ~2s
            assert 3.2 < calculate_backoff_delay(2, base_delay=1.0) < 4.8  # ~4s
            assert 6.4 < calculate_backoff_delay(3, base_delay=1.0) < 9.6  # ~8s

    def test_backoff_respects_max_delay(self):
        """El delay no excede el máximo configurado"""
        with patch('app.utils.retry.random.random', return_value=0.5):
            delay = calculate_backoff_delay(10, base_delay=1.0, max_delay=10.0)
            assert delay <= 12.0  # max_delay + 20% jitter

    def test_backoff_has_jitter(self):
        """El jitter aleatorio evita thundering herd"""
        delays = [calculate_backoff_delay(2, base_delay=1.0) for _ in range(10)]
        # Todos deben estar cerca de 4s pero no ser exactamente iguales
        assert all(3.0 < d < 5.0 for d in delays)
        assert len(set(delays)) > 1  # Al menos algunos diferentes

    def test_backoff_minimum_delay(self):
        """El delay mínimo es 0.1s incluso con jitter negativo"""
        with patch('app.utils.retry.random.random', return_value=0):  # jitter máximo negativo
            delay = calculate_backoff_delay(0, base_delay=0.1)
            assert delay >= 0.1


class TestTransientErrorDetection:
    """Tests para detección de errores transitorios vs permanentes"""

    def test_connection_errors_are_transient(self):
        """Errores de conexión son transitorios"""
        assert is_transient_error(ConnectionError("Connection refused"))
        assert is_transient_error(TimeoutError("Request timeout"))
        assert is_transient_error(asyncio.TimeoutError("Async timeout"))

    def test_http_5xx_are_transient(self):
        """Errores HTTP 5xx son transitorios"""
        assert is_transient_error(Exception("HTTP 500 Internal Server Error"))
        assert is_transient_error(Exception("HTTP 502 Bad Gateway"))
        assert is_transient_error(Exception("HTTP 503 Service Unavailable"))
        assert is_transient_error(Exception("HTTP 504 Gateway Timeout"))

    def test_http_429_is_transient(self):
        """HTTP 429 Rate Limit es transitorio"""
        assert is_transient_error(Exception("HTTP 429 Too Many Requests"))
        assert is_transient_error(Exception("Rate limit exceeded: 429"))

    def test_http_4xx_are_permanent(self):
        """Errores HTTP 4xx (excepto 429) son permanentes"""
        assert not is_transient_error(Exception("HTTP 400 Bad Request"))
        assert not is_transient_error(Exception("HTTP 401 Unauthorized"))
        assert not is_transient_error(Exception("HTTP 403 Forbidden"))
        assert not is_transient_error(Exception("HTTP 404 Not Found"))

    def test_validation_errors_are_permanent(self):
        """Errores de validación son permanentes"""
        assert not is_transient_error(ValueError("Invalid input"))
        assert not is_transient_error(Exception("Validation failed"))


class TestRetryAsyncDecorator:
    """Tests para decorador de retry asíncrono"""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        """Función exitosa no reintenta"""
        call_count = 0

        @retry_async(max_attempts=3, base_delay=0.1)
        async def succeeds_immediately():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await succeeds_immediately()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_transient_error(self):
        """Reintenta en errores transitorios"""
        call_count = 0

        @retry_async(max_attempts=3, base_delay=0.1)
        async def fails_twice_then_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary network issue")
            return "success"

        result = await fails_twice_then_succeeds()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_does_not_retry_permanent_errors(self):
        """No reintenta errores permanentes"""
        call_count = 0

        @retry_async(max_attempts=3, base_delay=0.1)
        async def fails_permanently():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input data")

        with pytest.raises(ValueError):
            await fails_permanently()

        assert call_count == 1  # Solo un intento

    @pytest.mark.asyncio
    async def test_exhausts_retries_and_raises(self):
        """Lanza RetryExhausted después de max_attempts"""
        call_count = 0

        @retry_async(max_attempts=3, base_delay=0.1)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")

        with pytest.raises(RetryExhausted) as exc_info:
            await always_fails()

        assert call_count == 3
        assert "failed after 3 attempts" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_respects_custom_max_attempts(self):
        """Respeta configuración de max_attempts"""
        call_count = 0

        @retry_async(max_attempts=5, base_delay=0.1)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise TimeoutError("Timeout")

        with pytest.raises(RetryExhausted):
            await always_fails()

        assert call_count == 5

    @pytest.mark.asyncio
    async def test_logs_retry_attempts(self):
        """Logging detallado de cada intento"""
        @retry_async(max_attempts=3, base_delay=0.1, operation_name="test_op")
        async def fails_once():
            if not hasattr(fails_once, 'called'):
                fails_once.called = True  # type: ignore
                raise ConnectionError("First failure")
            return "ok"

        with patch('app.utils.retry.logger') as mock_logger:
            result = await fails_once()

            assert result == "ok"
            # Debe haber logeado warning del fallo y success del reintento exitoso
            assert mock_logger.warning.called
            assert mock_logger.info.called


class TestRetrySyncDecorator:
    """Tests para decorador de retry síncrono"""

    def test_sync_retries_work(self):
        """Decorador síncrono funciona correctamente"""
        call_count = 0

        @retry_sync(max_attempts=3, base_delay=0.1)
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temp error")
            return "success"

        result = fails_twice()
        assert result == "success"
        assert call_count == 3

    def test_sync_respects_permanent_errors(self):
        """No reintenta errores permanentes en versión síncrona"""
        call_count = 0

        @retry_sync(max_attempts=3, base_delay=0.1)
        def permanent_failure():
            nonlocal call_count
            call_count += 1
            raise ValueError("Bad value")

        with pytest.raises(ValueError):
            permanent_failure()

        assert call_count == 1


class TestWhatsAppRetryIntegration:
    """Tests para retry logic aplicado a WhatsApp service"""

    @pytest.mark.asyncio
    async def test_whatsapp_retries_on_500_error(self):
        """WhatsApp reintenta en errores 500"""
        from app.services.whatsapp import _send_text_message_with_retry

        call_count = 0

        class MockResponse:
            def __init__(self, status_code, text="", json_data=None):
                self.status_code = status_code
                self.text = text
                self._json_data = json_data or {}
            
            def json(self):
                return self._json_data

        async def mock_post(self, url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return MockResponse(500, "Internal Server Error")
            return MockResponse(200, json_data={"messages": [{"id": "wamid.123"}]})

        with patch('httpx.AsyncClient.post', new=mock_post):
            result = await _send_text_message_with_retry("5491123456789", "Test message", timeout=5.0)

            assert result["status"] == "sent"
            assert call_count == 3  # Falló 2 veces, exitoso en la 3ra

    @pytest.mark.asyncio
    async def test_whatsapp_does_not_retry_400_error(self):
        """WhatsApp NO reintenta errores 400 (permanentes)"""
        from app.services.whatsapp import _send_text_message_with_retry

        call_count = 0

        class MockResponse:
            def __init__(self, status_code, text=""):
                self.status_code = status_code
                self.text = text
            
            def json(self):
                return {}

        async def mock_post(self, url, **kwargs):
            nonlocal call_count
            call_count += 1
            return MockResponse(400, "Bad Request")

        with patch('httpx.AsyncClient.post', new=mock_post):
            with pytest.raises(ValueError):  # Error permanente
                await _send_text_message_with_retry("invalid", "Test", timeout=5.0)

            assert call_count == 1  # No reintentó

    @pytest.mark.asyncio
    async def test_whatsapp_retries_rate_limit(self):
        """WhatsApp reintenta en rate limit (429)"""
        from app.services.whatsapp import _send_text_message_with_retry

        call_count = 0

        class MockResponse:
            def __init__(self, status_code, text="", json_data=None):
                self.status_code = status_code
                self.text = text
                self._json_data = json_data or {}
            
            def json(self):
                return self._json_data

        async def mock_post(self, url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return MockResponse(429, "Rate limit exceeded")
            return MockResponse(200, json_data={"messages": [{"id": "wamid.456"}]})

        with patch('httpx.AsyncClient.post', new=mock_post):
            result = await _send_text_message_with_retry("5491123456789", "Test", timeout=5.0)

            assert result["status"] == "sent"
            assert call_count == 2  # Reintentó después del 429

    @pytest.mark.asyncio
    async def test_whatsapp_image_has_retry(self):
        """send_image_message también tiene retry"""
        from app.services.whatsapp import _send_image_message_with_retry

        call_count = 0

        class MockResponse:
            def __init__(self, status_code, text="", json_data=None):
                self.status_code = status_code
                self.text = text
                self._json_data = json_data or {}
            
            def json(self):
                return self._json_data

        async def mock_post(self, url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return MockResponse(503, "Service Unavailable")
            return MockResponse(200, json_data={"messages": [{"id": "wamid.789"}]})

        with patch('httpx.AsyncClient.post', new=mock_post):
            result = await _send_image_message_with_retry(
                "5491123456789",
                "https://example.com/image.jpg",
                caption="Test Image",
                timeout=5.0
            )

            assert result["status"] == "sent"
            assert call_count == 2
