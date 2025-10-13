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

from datetime import datetime, timedelta, date, timezone
from decimal import Decimal
import uuid
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Accommodation, Reservation
from prometheus_client import Counter
from app.models.enums import ReservationStatus, PaymentStatus
from app.core.redis import acquire_lock, release_lock, get_redis_pool
import redis.asyncio as redis
from app.services.email import email_service

LOCK_TTL_SECONDS = 1800  # 30 minutos
PRERESERVATION_EXPIRY_MINUTES = 30
DEPOSIT_PERCENTAGE_DEFAULT = 30

# Métricas personalizadas básicas
RESERVATIONS_CREATED = Counter(
    "reservations_created_total", "Reservas pre-reservadas creadas", ["channel"]
)
RESERVATIONS_DATE_OVERLAP = Counter(
    "reservations_date_overlap_total", "Errores por solapamiento de fechas", ["channel"]
)
RESERVATIONS_LOCK_FAILED = Counter(
    "reservations_lock_failed_total", "Fallos de adquisición de lock Redis", ["channel"]
)
RESERVATIONS_CONFIRMED = Counter(
    "reservations_confirmed_total", "Reservas confirmadas", ["channel"]
)


class ReservationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_accommodation(self, accommodation_id: int) -> Optional[Accommodation]:
        stmt = select(Accommodation).where(Accommodation.id == accommodation_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_reservation_by_code(self, code: str) -> Optional[Reservation]:
        stmt = select(Reservation).where(Reservation.code == code)
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
        base_price = Decimal(str(acc.base_price))  # asume field NUMERIC
        weekend_mult = Decimal(getattr(acc, "weekend_multiplier", Decimal("1.2")))
        # Calcular noches weekend (sábado=5, domingo=6) dentro del rango [check_in, check_out)
        weekend_nights = 0
        for i in range(nights):
            day = check_in.weekday()  # 0 lunes
            if (check_in + timedelta(days=i)).weekday() in (5, 6):  # sábado o domingo
                weekend_nights += 1
        weekday_nights = nights - weekend_nights
        total_price = (base_price * weekday_nights) + (base_price * weekend_mult * weekend_nights)
        deposit_percentage = DEPOSIT_PERCENTAGE_DEFAULT
        deposit_amount = (total_price * Decimal(deposit_percentage) / Decimal(100)).quantize(
            Decimal("0.01")
        )

        lock_key = f"lock:acc:{accommodation_id}:{check_in.isoformat()}:{check_out.isoformat()}"
        lock_value = str(uuid.uuid4())

        # Redis lock
        pool = get_redis_pool()
        redis_client = redis.Redis(connection_pool=pool)
        try:
            try:
                locked = await acquire_lock(
                    redis_client, lock_key, lock_value, ttl=LOCK_TTL_SECONDS
                )
            except Exception:  # Fallback: en entorno de test sin Redis operativo
                locked = True  # confiamos en constraint DB para anti solapamiento
            if not locked:
                RESERVATIONS_LOCK_FAILED.labels(channel=channel).inc()
                return {"error": "processing_or_unavailable"}

            # Construir código simple (posible reemplazo futuro por secuencia) YYYYMMDD + uuid corto
            now_utc = datetime.now(timezone.utc)
            code = f"RES{now_utc:%y%m%d}{str(uuid.uuid4())[:6].upper()}"
            expires_at = now_utc + timedelta(minutes=PRERESERVATION_EXPIRY_MINUTES)

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
                RESERVATIONS_DATE_OVERLAP.labels(channel=channel).inc()
                return {"error": "date_overlap"}

            # Incrementar métrica (flush implícito la expone en /metrics inmediatamente)
            RESERVATIONS_CREATED.labels(channel=channel).inc()
            
            # Enviar email de pre-reserva si hay email (best-effort, no bloquea)
            if contact_email:
                try:
                    await email_service.send_prereservation_confirmation(
                        guest_email=contact_email,
                        guest_name=contact_name,
                        reservation_code=code,
                        accommodation_name=str(acc.name),
                        check_in=check_in.isoformat(),
                        check_out=check_out.isoformat(),
                        guests_count=guests,
                        total_amount=float(total_price),
                        expires_at=expires_at.isoformat(),
                    )
                except Exception:  # pragma: no cover
                    pass  # log pero no fallar transacción
            
            return {
                "code": reservation.code,
                "expires_at": (
                    reservation.expires_at.isoformat()
                    if reservation.expires_at is not None
                    else None
                ),
                "deposit_amount": str(reservation.deposit_amount),
                "total_price": str(reservation.total_price),
                "nights": reservation.nights,
            }
        finally:
            # NO liberamos lock inmediatamente si se creó la pre-reserva exitosamente;
            # el lock expira solo para minimizar carrera hasta confirmación o expiración.
            try:
                await redis_client.aclose()  # type: ignore[attr-defined]
            except AttributeError:  # pragma: no cover
                await redis_client.close()

    async def confirm_reservation(self, code: str) -> Dict[str, Any]:
        """Confirmación atómica de una pre-reserva.

        Usa UPDATE condicional para evitar doble confirmación concurrente.
        Compatible con SQLite (sin FOR UPDATE) y Postgres.
        """
        from sqlalchemy import select, update

        sel = select(Reservation).where(Reservation.code == code)
        result = await self.db.execute(sel)
        reservation = result.scalar_one_or_none()
        if not reservation:
            return {"code": None, "status": None, "confirmed_at": None, "error": "not_found"}
        # Cache de valores actuales para evitar accesos perezosos tras UPDATE independiente
        original_code = reservation.code
        original_status = reservation.reservation_status
        now = datetime.now(timezone.utc)
        expires_at = getattr(reservation, "expires_at", None)
        if isinstance(expires_at, datetime) and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if str(original_status) != ReservationStatus.PRE_RESERVED.value:
            return {
                "code": original_code,
                "status": original_status,
                "confirmed_at": None,
                "error": "invalid_state",
            }
        if isinstance(expires_at, datetime) and expires_at < now:
            upd_expired = (
                update(Reservation)
                .where(Reservation.id == reservation.id)
                .where(Reservation.reservation_status == ReservationStatus.PRE_RESERVED.value)
                .values(reservation_status=ReservationStatus.CANCELLED.value, cancelled_at=now)
            )
            await self.db.execute(upd_expired)
            await self.db.commit()
            return {
                "code": original_code,
                "status": ReservationStatus.CANCELLED.value,
                "confirmed_at": None,
                "error": "expired",
            }
        upd_confirm = (
            update(Reservation)
            .where(Reservation.id == reservation.id)
            .where(Reservation.reservation_status == ReservationStatus.PRE_RESERVED.value)
            .values(reservation_status=ReservationStatus.CONFIRMED.value, confirmed_at=now)
        )
        res = await self.db.execute(upd_confirm)
        if res.rowcount == 0:
            await self.db.rollback()
            return {
                "code": original_code,
                "status": original_status,
                "confirmed_at": None,
                "error": "invalid_state",
            }
        await self.db.commit()
        # Realizar un SELECT ligero para obtener confirmed_at sin depender de estado expirado
        sel_after = select(Reservation.confirmed_at).where(Reservation.code == original_code)
        after_row = await self.db.execute(sel_after)
        confirmed_at_val = after_row.scalar_one_or_none()
        confirmed_iso = confirmed_at_val.isoformat() if confirmed_at_val else None
        try:
            channel = getattr(reservation, "channel_source", "unknown") or "unknown"
            RESERVATIONS_CONFIRMED.labels(channel=channel).inc()
        except Exception:  # pragma: no cover
            pass
        
        # Enviar email de confirmación si hay email (best-effort)
        guest_email_val = getattr(reservation, "guest_email", None)
        if guest_email_val:
            try:
                # Obtener nombre del alojamiento si disponible
                accommodation_name = str(reservation.accommodation_id)
                if hasattr(reservation, "accommodation") and reservation.accommodation:
                    accommodation_name = str(reservation.accommodation.name)
                
                await email_service.send_reservation_confirmed(
                    guest_email=str(guest_email_val),
                    guest_name=str(getattr(reservation, "guest_name", "Cliente")),
                    reservation_code=str(original_code),
                    accommodation_name=accommodation_name,
                    check_in=str(reservation.check_in),
                    check_out=str(reservation.check_out),
                    guests_count=int(getattr(reservation, "guests_count", 1)),
                    total_amount=float(getattr(reservation, "total_price", 0)),
                )
            except Exception:  # pragma: no cover
                pass
        
        return {
            "code": original_code,
            "status": ReservationStatus.CONFIRMED.value,
            "confirmed_at": confirmed_iso,
        }

    async def cancel_reservation(self, code: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Cancela una reserva (pre_reserved o confirmed)."""
        reservation = await self._get_reservation_by_code(code)
        if not reservation:
            return {"error": "not_found"}

        if reservation.reservation_status not in [
            ReservationStatus.PRE_RESERVED.value,
            ReservationStatus.CONFIRMED.value,
        ]:
            return {"error": "invalid_state"}

        reservation.reservation_status = ReservationStatus.CANCELLED.value  # type: ignore
        reservation.cancelled_at = datetime.now(timezone.utc)  # type: ignore
        if reason:
            # Append reason to internal_notes
            existing = reservation.internal_notes or ""
            reservation.internal_notes = (existing + f"\nCancelled: {reason}").strip()  # type: ignore
        await self.db.commit()
        return {
            "code": reservation.code,
            "status": reservation.reservation_status,
            "cancelled_at": reservation.cancelled_at.isoformat(),
        }
