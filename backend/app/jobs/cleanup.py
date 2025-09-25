from __future__ import annotations

"""Jobs de limpieza y expiración de pre-reservas.

Reglas:
- Expira reservas en estado pre_reserved cuyo expires_at < ahora (UTC) y que no estén ya canceladas/confirmadas.
- Cambia reservation_status a cancelled y setea cancelled_at.
- No emite eventos externos aún (placeholder para futuras notificaciones).
"""
from datetime import datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models import Reservation
from app.models.enums import ReservationStatus

async def expire_prereservations(db: AsyncSession, batch_size: int = 200) -> int:
    """Marca como canceladas las pre-reservas vencidas.

    Retorna cantidad de reservas expiradas en esta ejecución.
    """
    now = datetime.now(timezone.utc)

    # Selecciona ids para evitar cargar todo el objeto pesado
    stmt = (
        select(Reservation.id)
        .where(Reservation.reservation_status == ReservationStatus.PRE_RESERVED.value)
        .where(Reservation.expires_at.isnot(None))
        .where(Reservation.expires_at < now)
        .limit(batch_size)
    )
    result = await db.execute(stmt)
    ids: List[int] = [row[0] for row in result.all()]
    if not ids:
        return 0

    upd = (
        update(Reservation)
        .where(Reservation.id.in_(ids))
        .values(
            reservation_status=ReservationStatus.CANCELLED.value,
            cancelled_at=now,
            internal_notes="auto-expired"
        )
    )
    await db.execute(upd)
    await db.commit()
    return len(ids)
