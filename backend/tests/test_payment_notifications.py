"""
Tests para notificaciones de estado de pago vía WhatsApp

Verificaciones incluidas:
- Formatters de mensajes específicos por estado (approved, rejected, pending)
- Envío de notificaciones desde MercadoPago webhook
- Manejo de errores en notificaciones sin afectar webhook
- Idempotencia: no reenviar si el estado no cambió
- Contenido de mensajes (emojis, CTAs, info completa)
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import date, datetime, timezone
from decimal import Decimal

from app.services.messages import (
    format_payment_approved,
    format_payment_rejected,
    format_payment_pending,
)
from app.services.whatsapp import (
    send_payment_approved,
    send_payment_rejected,
    send_payment_pending,
)
from app.services.mercadopago import MercadoPagoService
from app.models import Payment, Reservation, Accommodation
from app.models.enums import ReservationStatus, PaymentStatus


class TestPaymentMessageFormatters:
    """Tests para formatters de mensajes de pago"""

    def test_format_payment_approved_content(self):
        """Mensaje de pago aprobado tiene toda la información necesaria"""
        message = format_payment_approved(
            guest_name="Juan Pérez",
            reservation_code="RES001",
            check_in="15/12/2024",
            check_out="18/12/2024",
            accommodation_name="Cabaña Vista Al Lago"
        )

        # Contenido obligatorio
        assert "🎉" in message
        assert "Pago confirmado" in message
        assert "Juan Pérez" in message
        assert "RES001" in message
        assert "15/12/2024" in message
        assert "18/12/2024" in message
        assert "Cabaña Vista Al Lago" in message
        assert "confirmada" in message or "asegurado" in message
        
        # No debe contener términos técnicos
        assert "payment" not in message.lower()
        assert "webhook" not in message.lower()
        assert "api" not in message.lower()

    def test_format_payment_rejected_helpful_info(self):
        """Mensaje de pago rechazado incluye causas posibles y próximos pasos"""
        message = format_payment_rejected(
            guest_name="María García",
            reservation_code="RES002",
            amount="1.250,00"
        )

        # Información esencial
        assert "❌" in message
        assert "María García" in message
        assert "RES002" in message
        assert "$1.250,00" in message
        
        # Causas posibles
        assert "Fondos insuficientes" in message or "fondos" in message.lower()
        assert "Límite" in message or "límite" in message
        assert "banco" in message.lower()
        
        # Call to action
        assert "intentar" in message.lower() or "reintentar" in message.lower()
        assert "ayuda" in message.lower() or "ayudamos" in message.lower()

    def test_format_payment_pending_explanation(self):
        """Mensaje de pago pendiente explica causas y tiempo estimado"""
        message = format_payment_pending(
            guest_name="Carlos López",
            reservation_code="RES003", 
            amount="2.500,50"
        )

        # Información básica
        assert "⏳" in message
        assert "Carlos López" in message
        assert "RES003" in message
        assert "$2.500,50" in message
        assert "proceso" in message.lower() or "revisión" in message.lower()
        
        # Explicación de causas
        assert "seguridad" in message.lower() or "verificación" in message.lower()
        assert "transferencia" in message.lower() or "horarios" in message.lower()
        
        # Tiempo estimado
        assert "24-48" in message or "horas" in message
        assert "paciencia" in message.lower()


class TestWhatsAppPaymentNotifications:
    """Tests para funciones de alto nivel de notificaciones de pago"""

    @pytest.mark.asyncio
    @patch('app.services.whatsapp.send_text_message')
    async def test_send_payment_approved_calls_whatsapp_api(self, mock_send):
        """send_payment_approved envía mensaje correcto via WhatsApp"""
        mock_send.return_value = {"status": "sent", "message_id": "wamid.123"}

        result = await send_payment_approved(
            phone="5491123456789",
            guest_name="Ana Torres",
            reservation_code="RES004",
            check_in="20/12/2024",
            check_out="23/12/2024",
            accommodation_name="Departamento Centro"
        )

        # Verificar llamada a WhatsApp API
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        assert args[0] == "5491123456789"  # phone
        
        message = args[1]
        assert "🎉" in message
        assert "Ana Torres" in message
        assert "RES004" in message
        assert "Departamento Centro" in message
        
        # Verificar resultado
        assert result["status"] == "sent"

    @pytest.mark.asyncio  
    @patch('app.services.whatsapp.send_text_message')
    async def test_send_payment_rejected_includes_amount(self, mock_send):
        """send_payment_rejected incluye monto en mensaje"""
        mock_send.return_value = {"status": "sent"}

        await send_payment_rejected(
            phone="5491123456789",
            guest_name="Pedro Ruiz",
            reservation_code="RES005",
            amount="3.750,25"
        )

        mock_send.assert_called_once()
        message = mock_send.call_args[0][1]
        assert "❌" in message
        assert "Pedro Ruiz" in message
        assert "$3.750,25" in message

    @pytest.mark.asyncio
    @patch('app.services.whatsapp.send_text_message')
    async def test_send_payment_pending_with_logging(self, mock_send):
        """send_payment_pending registra envío correctamente"""
        mock_send.return_value = {"status": "sent"}

        with patch('app.services.whatsapp.logger') as mock_logger:
            await send_payment_pending(
                phone="5491123456789",
                guest_name="Luis Fernández",
                reservation_code="RES006", 
                amount="1.800,00"
            )

            # Verificar logging
            mock_logger.info.assert_called_once()
            log_args = mock_logger.info.call_args[1]
            assert log_args["phone"] == "5491123456789"
            assert log_args["reservation_code"] == "RES006"


class TestMercadoPagoNotificationIntegration:
    """Tests para integración de notificaciones con webhook MercadoPago"""

    @pytest.mark.asyncio
    async def test_new_payment_approved_sends_notification(self, db_session):
        """Nuevo pago aprobado envía notificación de confirmación"""
        # Crear alojamiento y reserva
        accommodation = Accommodation(
            name="Cabaña Bosque",
            type="cabin",
            capacity=4,
            base_price=Decimal("150.00"),
            description="Cabaña en el bosque",
            amenities=[],
            photos=[],
            location={},
            policies={},
            active=True
        )
        db_session.add(accommodation)
        await db_session.flush()

        reservation = Reservation(
            code="RES007",
            accommodation_id=accommodation.id,
            check_in=date(2024, 12, 15),
            check_out=date(2024, 12, 18),
            guest_name="Elena Vargas",
            guest_phone="5491123456789",
            guest_email="elena@email.com",
            guests_count=2,
            nights=3,
            base_price_per_night=Decimal("150.00"),
            total_price=Decimal("450.00"),
            deposit_amount=Decimal("135.00"),
            reservation_status=ReservationStatus.PRE_RESERVED.value,
            payment_status=PaymentStatus.PENDING.value
        )
        db_session.add(reservation)
        await db_session.commit()

        service = MercadoPagoService(db_session)
        
        # Mockear directamente la función de notificación interna
        with patch.object(service, '_send_payment_notification') as mock_notify:
            mock_notify.return_value = None  # Async function returns None
            
            result = await service.process_webhook({
                "id": "mp_payment_123",
                "status": "approved",
                "amount": 135.00,
                "currency": "ARS",
                "external_reference": "RES007"
            })

            # Verificar resultado del webhook
            assert result["status"] == "ok"
            assert not result["idempotent"]
            assert result["reservation_id"] == reservation.id

            # Verificar que se llamó la notificación interna
            mock_notify.assert_called_once()
            args = mock_notify.call_args[0]
            assert args[0] == reservation.id  # reservation_id
            assert args[1] == "approved"  # status
            assert args[2] == Decimal("135.00")  # amount

    @pytest.mark.asyncio
    async def test_payment_status_change_sends_notification(self, db_session):
        """Cambio de estado en pago existente envía nueva notificación"""
        # Crear alojamiento y reserva primero
        accommodation = Accommodation(
            name="Hotel Centro",
            type="room", 
            capacity=2,
            base_price=Decimal("100.00"),
            description="Habitación céntrica",
            amenities=[],
            photos=[],
            location={},
            policies={},
            active=True
        )
        db_session.add(accommodation)
        await db_session.flush()

        reservation = Reservation(
            code="RES008",
            accommodation_id=accommodation.id,
            check_in=date(2024, 12, 10),
            check_out=date(2024, 12, 12),
            guest_name="Carlos Mendez",
            guest_phone="5491123456789",
            guests_count=2,
            nights=2,
            base_price_per_night=Decimal("100.00"),
            total_price=Decimal("200.00"),
            deposit_amount=Decimal("60.00"),
            reservation_status=ReservationStatus.PRE_RESERVED.value
        )
        db_session.add(reservation)
        await db_session.flush()

        # Crear payment existente en estado pending
        payment = Payment(
            reservation_id=reservation.id,  # Asociar a reserva
            external_payment_id="mp_payment_456",
            external_reference="RES008",
            status="pending",
            amount=Decimal("200.00"),
            currency="ARS",
            event_first_received_at=datetime.now(timezone.utc),
            event_last_received_at=datetime.now(timezone.utc),
            events_count=1
        )
        db_session.add(payment)
        await db_session.commit()

        service = MercadoPagoService(db_session)
        
        # Mockear directamente la función de notificación interna
        with patch.object(service, '_send_payment_notification') as mock_notify:
            mock_notify.return_value = None
            
            result = await service.process_webhook({
                "id": "mp_payment_456",
                "status": "rejected",  # Cambio de pending a rejected
                "amount": 200.00,
                "currency": "ARS"
            })

            # Verificar que es idempotente pero cambió estado
            assert result["status"] == "ok"
            assert result["idempotent"]
            assert result["events_count"] == 2

            # Verificar que se llamó notificación por cambio de estado
            mock_notify.assert_called_once()
            args = mock_notify.call_args[0]
            assert len(args) == 3  # reservation_id, status, amount
            assert args[0] == reservation.id  # reservation_id
            assert args[1] == "rejected"  # status
            assert args[2] == Decimal("200.00")  # amount

    @pytest.mark.asyncio
    async def test_same_payment_status_no_notification(self, db_session):
        """Mismo estado de pago no reenvía notificación"""
        payment = Payment(
            external_payment_id="mp_payment_789",
            status="approved",
            amount=Decimal("300.00"),
            currency="ARS",
            event_first_received_at=datetime.now(timezone.utc),
            event_last_received_at=datetime.now(timezone.utc),
            events_count=1
        )
        db_session.add(payment)
        await db_session.commit()

        service = MercadoPagoService(db_session)
        
        with patch('app.services.mercadopago.MercadoPagoService._send_payment_notification') as mock_notify:
            await service.process_webhook({
                "id": "mp_payment_789",
                "status": "approved",  # Mismo estado
                "amount": 300.00
            })

            # No debe enviar notificación
            mock_notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_notification_error_does_not_fail_webhook(self, db_session):
        """Error en notificación no debe hacer fallar el webhook"""
        accommodation = Accommodation(
            name="Casa Playa",
            type="house",
            capacity=6,
            base_price=Decimal("200.00"),
            description="Casa frente al mar",
            amenities=[],
            photos=[],
            location={},
            policies={},
            active=True
        )
        db_session.add(accommodation)
        await db_session.flush()

        reservation = Reservation(
            code="RES009",
            accommodation_id=accommodation.id,
            check_in=date(2024, 12, 20),
            check_out=date(2024, 12, 25),
            guest_name="Roberto Silva",
            guest_phone="5491123456789",
            guests_count=4,
            nights=5,
            base_price_per_night=Decimal("200.00"),
            total_price=Decimal("1000.00"),
            deposit_amount=Decimal("300.00"),
            reservation_status=ReservationStatus.PRE_RESERVED.value
        )
        db_session.add(reservation)
        await db_session.commit()

        service = MercadoPagoService(db_session)
        
        with patch('app.services.whatsapp.send_payment_rejected') as mock_notify:
            # Simular error en notificación
            mock_notify.side_effect = Exception("WhatsApp API down")
            
            # El webhook debe seguir funcionando
            result = await service.process_webhook({
                "id": "mp_payment_error",
                "status": "rejected",
                "amount": 300.00,
                "external_reference": "RES009"
            })

            # Verificar que webhook no falló
            assert result["status"] == "ok"
            assert not result["idempotent"]
            assert result["reservation_id"] == reservation.id

    @pytest.mark.asyncio
    async def test_payment_without_reservation_no_notification(self, db_session):
        """Pago sin reserva asociada no envía notificación"""
        service = MercadoPagoService(db_session)
        
        with patch('app.services.mercadopago.MercadoPagoService._send_payment_notification') as mock_notify:
            result = await service.process_webhook({
                "id": "mp_orphan_payment",
                "status": "approved",
                "amount": 500.00,
                "external_reference": "INEXISTENT_RES"  # Reserva que no existe
            })

            # Webhook debe funcionar
            assert result["status"] == "ok"
            assert not result["idempotent"]
            assert result["reservation_id"] is None

            # No debe intentar notificación
            mock_notify.assert_not_called()