"""Tests para EmailService - MVP placeholder."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from app.services.email import EmailService, EMAIL_SENT


@pytest.fixture
def email_service():
    """Fixture para instancia limpia de EmailService."""
    return EmailService()


@pytest.mark.asyncio
async def test_send_prereservation_confirmation_success(email_service):
    """Test envío de email de pre-reserva."""
    with patch('app.services.email.logger') as mock_logger:
        result = await email_service.send_prereservation_confirmation(
            guest_email="test@example.com",
            guest_name="Juan Pérez",
            reservation_code="RES2501231ABC",
            accommodation_name="Cabaña del Bosque",
            check_in="2025-02-01",
            check_out="2025-02-05",
            guests_count=4,
            total_amount=50000.0,
            expires_at="2025-01-23T18:30:00Z",
        )
        
        assert result is True
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        assert call_kwargs["code"] == "RES2501231ABC"
        assert "test@example" in call_kwargs["email"]


@pytest.mark.asyncio
async def test_send_reservation_confirmed_success(email_service):
    """Test envío de email de reserva confirmada."""
    with patch('app.services.email.logger') as mock_logger:
        result = await email_service.send_reservation_confirmed(
            guest_email="confirmed@example.com",
            guest_name="María López",
            reservation_code="RES2501232XYZ",
            accommodation_name="Cabaña Vista al Lago",
            check_in="2025-03-15",
            check_out="2025-03-20",
            guests_count=2,
            total_amount=75000.0,
            accommodation_address="Ruta 40 Km 2450, Bariloche",
            check_in_instructions="Clave de acceso: 1234. Check-in desde las 14hs.",
        )
        
        assert result is True
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        assert call_kwargs["code"] == "RES2501232XYZ"
        assert "confirmed@examp" in call_kwargs["email"]


@pytest.mark.asyncio
async def test_send_reservation_expired_success(email_service):
    """Test envío de email de pre-reserva expirada."""
    with patch('app.services.email.logger') as mock_logger:
        result = await email_service.send_reservation_expired(
            guest_email="expired@example.com",
            guest_name="Carlos García",
            reservation_code="RES2501230DEF",
            accommodation_name="Cabaña del Río",
            check_in="2025-04-10",
            check_out="2025-04-12",
        )
        
        assert result is True
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        assert call_kwargs["code"] == "RES2501230DEF"
        assert "expired@exampl" in call_kwargs["email"]


@pytest.mark.asyncio
async def test_email_metrics_incremented():
    """Test que las métricas se incrementan correctamente."""
    service = EmailService()
    
    # Mock del counter de Prometheus
    with patch.object(EMAIL_SENT, 'labels') as mock_labels:
        mock_counter = MagicMock()
        mock_labels.return_value = mock_counter
        
        await service.send_prereservation_confirmation(
            guest_email="metrics@test.com",
            guest_name="Test User",
            reservation_code="RES123",
            accommodation_name="Test Cabin",
            check_in="2025-01-01",
            check_out="2025-01-05",
            guests_count=2,
            total_amount=10000.0,
            expires_at="2025-01-01T12:00:00Z",
        )
        
        # Verificar que se llamó con los labels correctos
        mock_labels.assert_called_with(type="prereservation", status="logged")
        mock_counter.inc.assert_called_once()


@pytest.mark.asyncio
async def test_email_service_enabled_flag(email_service):
    """Test que el flag enabled está correctamente configurado."""
    assert email_service.enabled is False


@pytest.mark.asyncio
async def test_truncated_email_in_logs(email_service):
    """Test que el email se trunca en los logs por seguridad."""
    with patch('app.services.email.logger') as mock_logger:
        long_email = "verylongemailaddress@example.com"
        
        await email_service.send_prereservation_confirmation(
            guest_email=long_email,
            guest_name="Test",
            reservation_code="RES123",
            accommodation_name="Test",
            check_in="2025-01-01",
            check_out="2025-01-02",
            guests_count=1,
            total_amount=1000.0,
            expires_at="2025-01-01T12:00:00Z",
        )
        
        call_kwargs = mock_logger.info.call_args[1]
        # Debe truncar después de 15 caracteres + "..."
        assert len(call_kwargs["email"]) == 18  # 15 + 3 puntos
        assert call_kwargs["email"].endswith("...")


@pytest.mark.asyncio
async def test_all_email_types_logged_correctly():
    """Test que todos los tipos de email se loguean con el type correcto."""
    service = EmailService()
    
    test_cases = [
        ("prereservation", service.send_prereservation_confirmation, {
            "guest_email": "test@example.com",
            "guest_name": "Test",
            "reservation_code": "RES1",
            "accommodation_name": "Cabin",
            "check_in": "2025-01-01",
            "check_out": "2025-01-02",
            "guests_count": 1,
            "total_amount": 1000.0,
            "expires_at": "2025-01-01T12:00:00Z",
        }),
        ("confirmed", service.send_reservation_confirmed, {
            "guest_email": "test@example.com",
            "guest_name": "Test",
            "reservation_code": "RES2",
            "accommodation_name": "Cabin",
            "check_in": "2025-01-01",
            "check_out": "2025-01-02",
            "guests_count": 1,
            "total_amount": 1000.0,
        }),
        ("expired", service.send_reservation_expired, {
            "guest_email": "test@example.com",
            "guest_name": "Test",
            "reservation_code": "RES3",
            "accommodation_name": "Cabin",
            "check_in": "2025-01-01",
            "check_out": "2025-01-02",
        }),
    ]
    
    for email_type, method, kwargs in test_cases:
        with patch.object(EMAIL_SENT, 'labels') as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter
            
            await method(**kwargs)
            
            # Verificar que se llamó con el tipo correcto
            mock_labels.assert_called_with(type=email_type, status="logged")
            mock_counter.inc.assert_called_once()


@pytest.mark.asyncio
async def test_email_service_returns_true_for_all_methods(email_service):
    """Test que todos los métodos retornan True (éxito)."""
    result1 = await email_service.send_prereservation_confirmation(
        guest_email="test@example.com",
        guest_name="Test",
        reservation_code="RES1",
        accommodation_name="Cabin",
        check_in="2025-01-01",
        check_out="2025-01-02",
        guests_count=1,
        total_amount=1000.0,
        expires_at="2025-01-01T12:00:00Z",
    )
    
    result2 = await email_service.send_reservation_confirmed(
        guest_email="test@example.com",
        guest_name="Test",
        reservation_code="RES2",
        accommodation_name="Cabin",
        check_in="2025-01-01",
        check_out="2025-01-02",
        guests_count=1,
        total_amount=1000.0,
    )
    
    result3 = await email_service.send_reservation_expired(
        guest_email="test@example.com",
        guest_name="Test",
        reservation_code="RES3",
        accommodation_name="Cabin",
        check_in="2025-01-01",
        check_out="2025-01-02",
    )
    
    assert result1 is True
    assert result2 is True
    assert result3 is True
