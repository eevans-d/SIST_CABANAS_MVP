from __future__ import annotations

"""Reservation service (MVP) para pre-reservas con lock Redis y constraint Postgres.

Reglas (según especificación .github/copilot-instructions.md):
1. Lock Redis previo (SET NX EX 1800) en clave: lock:acc:{accommodation_id}:{check_in}:{check_out}
2. Si lock falla → retornar error {"error": "processing_or_unavailable"}
3. Calcular precio simple: base_price * noches (placeholder multiplicadores futuros)
4. Insertar reserva en estado pre_reserved con expires_at = ahora + 30 min
5. Manejar IntegrityError: liberar lock y responder {"error": "date_overlap"}
6. Retornar payload mínimo con code, expires_at, deposit_amount

NO se implementa todavía: Mercado Pago, pricing avanzado, extensión de lock.
"""

from datetime import datetime, timedelta, date
from decimal import Decimal
import uuid
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Accommodation, Reservation
from app.models.enums import ReservationStatus, PaymentStatus
from app.core.redis import acquire_lock, release_lock, get_redis_pool
import redis.asyncio as redis

LOCK_TTL_SECONDS = 1800  # 30 minutos
PRERESERVATION_EXPIRY_MINUTES = 30
DEPOSIT_PERCENTAGE_DEFAULT = 30

class ReservationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_accommodation(self, accommodation_id: int) -> Optional[Accommodation]:
        stmt = select(Accommodation).where(Accommodation.id == accommodation_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_prereservation(
        self,
        accommodation_id: int,
        check_in: date,
        check_out: date,
        guests: int,
        channel: str,
        contact_name: str,
        contact_phone: str,
        contact_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Validaciones mínimas
        if check_in >= check_out:
            return {"error": "invalid_dates"}
        if guests <= 0:
            return {"error": "invalid_guests"}

        acc = await self._get_accommodation(accommodation_id)
        if not acc or getattr(acc, "active", True) is False:
            return {"error": "accommodation_not_found"}

        nights = (check_out - check_in).days
        base_price = Decimal(acc.base_price)  # asume field NUMERIC
        total_price = base_price * nights
        deposit_percentage = DEPOSIT_PERCENTAGE_DEFAULT
        deposit_amount = (total_price * Decimal(deposit_percentage) / Decimal(100)).quantize(Decimal('0.01'))

        lock_key = f"lock:acc:{accommodation_id}:{check_in.isoformat()}:{check_out.isoformat()}"
        lock_value = str(uuid.uuid4())

        # Redis lock
        pool = get_redis_pool()
        redis_client = redis.Redis(connection_pool=pool)
        try:
            locked = await acquire_lock(redis_client, lock_key, lock_value, ttl=LOCK_TTL_SECONDS)
            if not locked:
                return {"error": "processing_or_unavailable"}

            # Construir código simple (posible reemplazo futuro por secuencia) YYYYMMDD + uuid corto
            code = f"RES{datetime.utcnow():%y%m%d}{str(uuid.uuid4())[:6].upper()}"
            expires_at = datetime.utcnow() + timedelta(minutes=PRERESERVATION_EXPIRY_MINUTES)

            reservation = Reservation(
                code=code,
                accommodation_id=accommodation_id,
                check_in=check_in,
                check_out=check_out,
                guest_name=contact_name,
                guest_phone=contact_phone,
                guest_email=contact_email,
                guests_count=guests,
                nights=nights,
                base_price_per_night=base_price,
                total_price=total_price,
                deposit_percentage=deposit_percentage,
                deposit_amount=deposit_amount,
                reservation_status=ReservationStatus.PRE_RESERVED.value,
                payment_status=PaymentStatus.PENDING.value,
                expires_at=expires_at,
                lock_value=lock_value,
                channel_source=channel,
            )
            self.db.add(reservation)
            try:
                await self.db.commit()
                await self.db.refresh(reservation)
            except IntegrityError:
                await self.db.rollback()
                # liberar lock al fallar por solapamiento
                await release_lock(redis_client, lock_key, lock_value)
                return {"error": "date_overlap"}

            return {
                "code": reservation.code,
                "expires_at": reservation.expires_at.isoformat() if reservation.expires_at else None,
                "deposit_amount": str(reservation.deposit_amount),
                "total_price": str(reservation.total_price),
                "nights": reservation.nights,
            }
        finally:
            # NO liberamos lock inmediatamente si se creó la pre-reserva exitosamente;
            # el lock expira solo para minimizar carrera hasta confirmación o expiración.
            await redis_client.close()
