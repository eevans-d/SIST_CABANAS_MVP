from __future__ import annotations

"""Servicio mínimo de integración Mercado Pago (MVP).

Función principal: procesar webhook idempotente.
- Si payment_id ya existe en tabla payments: incrementar events_count y actualizar timestamps.
- Si no existe: crear registro asociado a reservation (por code) si se provee external_reference.
- Para MVP se asume payload simplificado:
  {
    "id": "123456",            # payment id MP
    "status": "approved|pending|rejected",
    "amount": 1234.56,
    "currency": "ARS",
    "external_reference": "<reservation_code>"
  }

Validaciones futuras (firmas, consulta a API MP) se diferirán.
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Payment, Reservation, Accommodation
from app.models.enums import ReservationStatus, PaymentStatus
import structlog
from app.services.whatsapp import send_payment_approved, send_payment_rejected, send_payment_pending

logger = structlog.get_logger()


class MercadoPagoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_reservation_by_code(self, code: str) -> Optional[Reservation]:
        stmt = select(Reservation).where(Reservation.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_reservation_with_accommodation(self, reservation_id: int) -> Optional[tuple]:
        """Obtiene reserva con datos del alojamiento para notificaciones"""
        stmt = (
            select(Reservation, Accommodation)
            .join(Accommodation, Reservation.accommodation_id == Accommodation.id)
            .where(Reservation.id == reservation_id)
        )
        result = await self.db.execute(stmt)
        row = result.first()
        return row if row else None

    async def _send_payment_notification(self, reservation_id: int, payment_status: str, amount: Decimal) -> None:
        """Envía notificación WhatsApp según el estado del pago"""
        try:
            # Obtener datos completos de reserva y alojamiento
            row = await self._get_reservation_with_accommodation(reservation_id)
            if not row:
                logger.warning("reservation_not_found_for_notification", reservation_id=reservation_id)
                return

            reservation, accommodation = row
            
            # Formatear fechas para mostrar
            check_in_str = reservation.check_in.strftime("%d/%m/%Y")
            check_out_str = reservation.check_out.strftime("%d/%m/%Y")
            amount_str = f"{float(amount):,.2f}"

            # Enviar notificación según estado
            if payment_status == "approved":
                await send_payment_approved(
                    phone=reservation.guest_phone,
                    guest_name=reservation.guest_name,
                    reservation_code=reservation.code,
                    check_in=check_in_str,
                    check_out=check_out_str,
                    accommodation_name=accommodation.name
                )
            elif payment_status == "rejected":
                await send_payment_rejected(
                    phone=reservation.guest_phone,
                    guest_name=reservation.guest_name,
                    reservation_code=reservation.code,
                    amount=amount_str
                )
            elif payment_status == "pending":
                await send_payment_pending(
                    phone=reservation.guest_phone,
                    guest_name=reservation.guest_name,
                    reservation_code=reservation.code,
                    amount=amount_str
                )
                
            logger.info(
                "payment_notification_sent",
                reservation_id=reservation_id,
                payment_status=payment_status,
                phone=reservation.guest_phone
            )
            
        except Exception as e:
            # No fallar el webhook por errores de notificación
            logger.error(
                "payment_notification_failed",
                reservation_id=reservation_id,
                payment_status=payment_status,
                error=str(e)
            )

    async def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payment_id = str(payload.get("id"))
        if not payment_id:
            return {"error": "invalid_payload"}

        status = payload.get("status", "pending")
        amount_raw = payload.get("amount", 0)
        try:
            amount = Decimal(str(amount_raw))
        except Exception:
            amount = Decimal("0")
        currency = payload.get("currency", "ARS")
        external_reference = payload.get("external_reference")

        now = datetime.now(timezone.utc)

        # Buscar existing payment
        stmt = select(Payment).where(Payment.external_payment_id == payment_id)
        result = await self.db.execute(stmt)
        payment = result.scalar_one_or_none()
        if payment:
            # Verificar si cambió el estado (para reenviar notificación)
            status_changed = payment.status != status
            payment.event_last_received_at = now  # type: ignore
            payment.events_count = (payment.events_count or 1) + 1  # type: ignore
            # Actualizar status y monto si cambió (caso reintentos)
            payment.status = status  # type: ignore
            payment.amount = amount  # type: ignore
            await self.db.commit()
            await self.db.refresh(payment)
            
            # Si cambió el estado y hay reserva asociada, enviar notificación
            if status_changed and payment.reservation_id is not None:
                await self._send_payment_notification(int(payment.reservation_id), status, amount)  # type: ignore
            
            return {
                "status": "ok",
                "idempotent": True,
                "payment_id": payment_id,
                "events_count": payment.events_count,
            }

        # Nuevo payment
        reservation_id = None
        if external_reference:
            reservation = await self._get_reservation_by_code(external_reference)
            if reservation:
                reservation_id = reservation.id
                # Si aprobado y reserva pre_reserved -> marcar como confirmed (depósito simplificado)
                if (
                    status == "approved"
                    and reservation.reservation_status == ReservationStatus.PRE_RESERVED.value  # type: ignore
                ):
                    reservation.reservation_status = ReservationStatus.CONFIRMED.value  # type: ignore
                    reservation.confirmed_at = now  # type: ignore
                    reservation.payment_status = PaymentStatus.PAID.value  # type: ignore

        payment = Payment(
            reservation_id=reservation_id if reservation_id is not None else None,
            external_payment_id=payment_id,
            external_reference=external_reference,
            status=status,
            amount=amount,
            currency=currency,
            event_first_received_at=now,
            event_last_received_at=now,
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        
        # Enviar notificación para nuevo pago con reserva asociada
        if reservation_id is not None:
            await self._send_payment_notification(int(reservation_id), status, amount)  # type: ignore
        
        return {
            "status": "ok",
            "idempotent": False,
            "payment_id": payment_id,
            "reservation_id": reservation_id,
        }
