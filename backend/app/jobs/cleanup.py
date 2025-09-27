from __future__ import annotations

"""Jobs de limpieza y expiración de pre-reservas.

Reglas:
- Expira reservas en estado pre_reserved cuyo expires_at < ahora (UTC) y que no estén ya canceladas/confirmadas.
- Cambia reservation_status a cancelled y setea cancelled_at.
- No emite eventos externos aún (placeholder para futuras notificaciones).
"""
from datetime import datetime, timezone, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from prometheus_client import Counter

from app.models import Reservation
from app.models.enums import ReservationStatus
from app.services.email import email_service

# Métricas
PRE_RES_EXPIRED = Counter("prereservations_expired_total", "Pre-reservas expiradas por job")
PRE_RES_REMINDERS = Counter("prereservation_reminders_processed_total", "Recordatorios de pre-reservas procesados")

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
    try:
        PRE_RES_EXPIRED.inc(len(ids))
    except Exception:
        pass
    # Best-effort: enviar notificación de expiración por email si se dispone de guest_email
    try:
        # Cargar datos necesarios para email
        result2 = await db.execute(select(Reservation).where(Reservation.id.in_(ids)))
        rows = result2.scalars().all()
        for r in rows:
            if getattr(r, 'guest_email', None):
                try:
                    html = email_service.render("expiration.html", {
                        "guest_name": getattr(r, 'guest_name', 'Cliente'),
                        "code": r.code,
                    })
                except Exception:
                    html = f"<h3>Pre-reserva {r.code} expirada</h3>"
                try:
                    email_service.send_html(r.guest_email, f"Pre-reserva {r.code} expirada", html, email_type="expired")
                except Exception:
                    pass
    except Exception:
        # No interrumpir el job por fallas de email
        pass
    return len(ids)


async def send_prereservation_reminders(db: AsyncSession, window_minutes: int = 15, batch_size: int = 200) -> int:
    """Envía recordatorios de pre-reservas que expiran pronto y marca para no duplicar.

    Selecciona pre-reservas con expires_at entre ahora y ahora+ventana que aún no fueron
    marcadas como 'reminder_sent' en internal_notes.
    Retorna cantidad de recordatorios procesados en esta ejecución.
    """
    now = datetime.now(timezone.utc)
    upper = now + timedelta(minutes=window_minutes)

    stmt = (
        select(Reservation)
        .where(Reservation.reservation_status == ReservationStatus.PRE_RESERVED.value)
        .where(Reservation.expires_at.isnot(None))
        .where(Reservation.expires_at >= now)
        .where(Reservation.expires_at <= upper)
        .limit(batch_size)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    processed = 0
    for r in rows:
        # Evitar duplicados si ya fue marcado
        notes = (r.internal_notes or "")
        if "reminder_sent" in notes:
            continue
        # Enviar email best-effort
        if getattr(r, 'guest_email', None):
            try:
                try:
                    html = email_service.render("reminder.html", {
                        "guest_name": getattr(r, 'guest_name', 'Cliente'),
                        "code": r.code,
                    })
                except Exception:
                    html = f"<h3>Recordatorio: confirmá tu reserva {r.code}</h3>"
                email_service.send_html(r.guest_email, f"Recordatorio reserva {r.code}", html, email_type="pre_reserved")
            except Exception:
                pass
        # Marcar como recordatorio enviado en internal_notes
        new_notes = (notes + "\n" if notes else "") + "reminder_sent"
        await db.execute(
            update(Reservation).where(Reservation.id == r.id).values(internal_notes=new_notes)
        )
        processed += 1
    if processed:
        await db.commit()
        try:
            PRE_RES_REMINDERS.inc(processed)
        except Exception:
            pass
    return processed
