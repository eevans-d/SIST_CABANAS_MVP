"""
Tests para retry en MercadoPago API

Verificaciones incluidas:
- get_payment_info() reintenta en errores transitorios (429, 5xx)
- get_payment_info() NO reintenta en errores permanentes (4xx)
- get_payment_status() funciona correctamente con retry
- Timeout y NetworkError triggerean retry
- Métricas de retry se registran
"""
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.mercadopago import MercadoPagoService


class MockResponse:
    """Mock de httpx.Response"""

    def __init__(self, status_code: int, json_data: dict = None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self):
        return self._json_data


class TestMercadoPagoGetPaymentWithRetry:
    """Tests para get_payment_info con retry automático"""

    @pytest.mark.asyncio
    async def test_get_payment_info_success_first_attempt(self, db_session):
        """get_payment_info exitoso en primer intento"""
        service = MercadoPagoService(db_session)

        mock_response = MockResponse(
            status_code=200,
            json_data={"id": "123456", "status": "approved", "transaction_amount": 1000.00},
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await service.get_payment_info("123456")

            assert result["id"] == "123456"
            assert result["status"] == "approved"
            # Solo un intento
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_payment_info_retries_on_429(self, db_session):
        """get_payment_info reintenta en rate limit (429)"""
        service = MercadoPagoService(db_session)

        # Primera llamada: 429, segunda: éxito
        responses = [
            MockResponse(status_code=429, text="Rate limit"),
            MockResponse(status_code=200, json_data={"id": "123456", "status": "approved"}),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(side_effect=responses)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await service.get_payment_info("123456")

            assert result["status"] == "approved"
            # Debe haber reintentado
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_get_payment_info_retries_on_500(self, db_session):
        """get_payment_info reintenta en error 500"""
        service = MercadoPagoService(db_session)

        responses = [
            MockResponse(status_code=500, text="Internal Server Error"),
            MockResponse(status_code=500, text="Internal Server Error"),
            MockResponse(status_code=200, json_data={"id": "123456", "status": "approved"}),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(side_effect=responses)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await service.get_payment_info("123456")

            assert result["status"] == "approved"
            # 3 intentos total
            assert mock_get.call_count == 3

    @pytest.mark.asyncio
    async def test_get_payment_info_does_not_retry_on_404(self, db_session):
        """get_payment_info NO reintenta en error 404 (permanente)"""
        service = MercadoPagoService(db_session)

        mock_response = MockResponse(status_code=404, text="Not found")

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            with pytest.raises(ValueError, match="MercadoPago API error: 404"):
                await service.get_payment_info("nonexistent")

            # Solo un intento (no retry en 4xx)
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_payment_info_does_not_retry_on_401(self, db_session):
        """get_payment_info NO reintenta en error 401 (auth error)"""
        service = MercadoPagoService(db_session)

        mock_response = MockResponse(status_code=401, text="Unauthorized")

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            with pytest.raises(ValueError, match="MercadoPago API error: 401"):
                await service.get_payment_info("123456")

            # Solo un intento
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_payment_info_retries_on_timeout(self, db_session):
        """get_payment_info reintenta en timeout"""
        import httpx

        service = MercadoPagoService(db_session)

        # Primera llamada timeout, segunda éxito
        side_effects = [
            httpx.TimeoutException("Timeout"),
            MockResponse(status_code=200, json_data={"id": "123456", "status": "approved"}),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(side_effect=side_effects)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await service.get_payment_info("123456")

            assert result["status"] == "approved"
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_get_payment_info_retries_on_network_error(self, db_session):
        """get_payment_info reintenta en network error"""
        import httpx

        service = MercadoPagoService(db_session)

        side_effects = [
            httpx.NetworkError("Connection failed"),
            MockResponse(status_code=200, json_data={"id": "123456", "status": "approved"}),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(side_effect=side_effects)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await service.get_payment_info("123456")

            assert result["status"] == "approved"
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_get_payment_info_exhausts_retries(self, db_session):
        """get_payment_info agota reintentos tras 3 intentos"""
        from app.utils.retry import RetryExhausted

        service = MercadoPagoService(db_session)

        # Siempre falla con 503
        mock_response = MockResponse(status_code=503, text="Service Unavailable")

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            with pytest.raises(RetryExhausted):
                await service.get_payment_info("123456")

            # 3 intentos máximo
            assert mock_get.call_count == 3

    @pytest.mark.asyncio
    async def test_get_payment_info_requires_access_token(self, db_session):
        """get_payment_info requiere access token configurado"""
        service = MercadoPagoService(db_session)

        with patch("app.services.mercadopago.settings") as mock_settings:
            mock_settings.MERCADOPAGO_ACCESS_TOKEN = None

            with pytest.raises(ValueError, match="not configured"):
                await service.get_payment_info("123456")


class TestMercadoPagoGetPaymentStatus:
    """Tests para get_payment_status (wrapper simplificado)"""

    @pytest.mark.asyncio
    async def test_get_payment_status_returns_status_only(self, db_session):
        """get_payment_status retorna solo el estado"""
        service = MercadoPagoService(db_session)

        mock_response = MockResponse(
            status_code=200,
            json_data={
                "id": "123456",
                "status": "pending",
                "transaction_amount": 500.00,
                "description": "Test payment",
            },
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            status = await service.get_payment_status("123456")

            assert status == "pending"

    @pytest.mark.asyncio
    async def test_get_payment_status_also_retries(self, db_session):
        """get_payment_status también tiene retry automático"""
        service = MercadoPagoService(db_session)

        responses = [
            MockResponse(status_code=503, text="Unavailable"),
            MockResponse(status_code=200, json_data={"id": "123456", "status": "approved"}),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(side_effect=responses)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            status = await service.get_payment_status("123456")

            assert status == "approved"
            # Reintentó
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_get_payment_status_returns_unknown_if_missing(self, db_session):
        """get_payment_status retorna 'unknown' si status no está presente"""
        service = MercadoPagoService(db_session)

        mock_response = MockResponse(
            status_code=200, json_data={"id": "123456"}  # Sin campo status
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            status = await service.get_payment_status("123456")

            assert status == "unknown"


class TestMercadoPagoRetryIntegration:
    """Tests de integración para retry en MercadoPago"""

    @pytest.mark.asyncio
    @patch("app.utils.retry.RETRY_ATTEMPTS")
    async def test_retry_metrics_are_recorded(self, mock_metric, db_session):
        """Métricas de retry se registran para operaciones MercadoPago"""
        mock_labels = MagicMock()
        mock_metric.labels.return_value = mock_labels

        service = MercadoPagoService(db_session)

        mock_response = MockResponse(
            status_code=200, json_data={"id": "123456", "status": "approved"}
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            await service.get_payment_info("123456")

            # Verificar que se registraron métricas
            mock_metric.labels.assert_called()
            mock_labels.inc.assert_called()

    @pytest.mark.asyncio
    async def test_multiple_payment_queries_work_correctly(self, db_session):
        """Múltiples queries de pago funcionan correctamente con retry"""
        service = MercadoPagoService(db_session)

        responses = [
            # Primera consulta: éxito inmediato
            MockResponse(status_code=200, json_data={"id": "111", "status": "approved"}),
            # Segunda consulta: retry y éxito
            MockResponse(status_code=503, text="Unavailable"),
            MockResponse(status_code=200, json_data={"id": "222", "status": "pending"}),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(side_effect=responses)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            # Primera consulta
            result1 = await service.get_payment_info("111")
            assert result1["status"] == "approved"

            # Segunda consulta (con retry)
            result2 = await service.get_payment_info("222")
            assert result2["status"] == "pending"

            # Total: 3 llamadas HTTP (1 + 2)
            assert mock_get.call_count == 3
