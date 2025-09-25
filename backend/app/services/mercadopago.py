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

from app.models import Payment, Reservation
from app.models.enums import ReservationStatus, PaymentStatus

class MercadoPagoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_reservation_by_code(self, code: str) -> Optional[Reservation]:
        stmt = select(Reservation).where(Reservation.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payment_id = str(payload.get("id"))
        if not payment_id:
            return {"error": "invalid_payload"}

        status = payload.get("status", "pending")
        amount_raw = payload.get("amount", 0)
        try:
            amount = Decimal(str(amount_raw))
        except Exception:
            amount = Decimal('0')
        currency = payload.get("currency", "ARS")
        external_reference = payload.get("external_reference")

        now = datetime.now(timezone.utc)

        # Buscar existing payment
        stmt = select(Payment).where(Payment.external_payment_id == payment_id)
        result = await self.db.execute(stmt)
        payment = result.scalar_one_or_none()
        if payment:
            payment.event_last_received_at = now
            payment.events_count = (payment.events_count or 1) + 1
            # Actualizar status y monto si cambió (caso reintentos)
            payment.status = status
            payment.amount = amount
            await self.db.commit()
            await self.db.refresh(payment)
            return {"status": "ok", "idempotent": True, "payment_id": payment_id, "events_count": payment.events_count}

        # Nuevo payment
        reservation_id = None
        if external_reference:
            reservation = await self._get_reservation_by_code(external_reference)
            if reservation:
                reservation_id = reservation.id
                # Si aprobado y reserva pre_reserved -> marcar como confirmed (depósito simplificado)
                if status == "approved" and reservation.reservation_status == ReservationStatus.PRE_RESERVED.value:
                    reservation.reservation_status = ReservationStatus.CONFIRMED.value
                    reservation.confirmed_at = now
                    reservation.payment_status = PaymentStatus.PAID.value

        payment = Payment(
            reservation_id=reservation_id if reservation_id else 0,  # 0 si no asociada (se podría rechazar)
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
        return {"status": "ok", "idempotent": False, "payment_id": payment_id, "reservation_id": reservation_id}
