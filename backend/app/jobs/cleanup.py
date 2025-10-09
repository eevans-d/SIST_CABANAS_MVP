"""Jobs de limpieza y expiración de pre-reservas."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import List

import structlog
from app.metrics import (
    PRERESERVATION_EXPIRY_DURATION,
    PRERESERVATION_REMINDERS_SENT,
    PRERESERVATIONS_EXPIRED,
)
from app.models import Reservation
from app.models.enums import ReservationStatus
from app.services.email import email_service
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


async def expire_prereservations(db: AsyncSession, batch_size: int = 200) -> int:
    """Marca como canceladas las pre-reservas vencidas.

    Retorna cantidad de reservas expiradas en esta ejecución.
    """
    start_time = time.monotonic()
    now = datetime.now(timezone.utc)

    logger.info("expire_prereservations_started", batch_size=batch_size)

    try:
        # Selecciona ids para evitar cargar todo el objeto pesado
        stmt = (
            select(Reservation.id, Reservation.accommodation_id)
            .where(Reservation.reservation_status == ReservationStatus.PRE_RESERVED.value)
            .where(Reservation.expires_at.isnot(None))
            .where(Reservation.expires_at < now)
            .limit(batch_size)
        )
        result = await db.execute(stmt)
        rows = result.all()

        if not rows:
            duration = time.monotonic() - start_time
            PRERESERVATION_EXPIRY_DURATION.observe(duration)
            logger.info(
                "expire_prereservations_completed", count=0, duration_ms=round(duration * 1000)
            )
            return 0

        ids: List[int] = [row[0] for row in rows]
        accommodation_ids: List[int] = [row[1] for row in rows]

        upd = (
            update(Reservation)
            .where(Reservation.id.in_(ids))
            .values(
                reservation_status=ReservationStatus.CANCELLED.value,
                cancelled_at=now,
                internal_notes="auto-expired",
            )
        )
        await db.execute(upd)
        await db.commit()

        # Incrementar métricas por alojamiento
        for acc_id in set(accommodation_ids):
            count_for_acc = accommodation_ids.count(acc_id)
            PRERESERVATIONS_EXPIRED.labels(accommodation_id=str(acc_id)).inc(count_for_acc)

        # Best-effort: enviar notificación de expiración por email si se dispone de guest_email
        try:
            # Cargar datos necesarios para email
            result2 = await db.execute(select(Reservation).where(Reservation.id.in_(ids)))
            rows = result2.scalars().all()
            for r in rows:
                if getattr(r, "guest_email", None):
                    try:
                        html = email_service.render(
                            "expiration.html",
                            {
                                "guest_name": getattr(r, "guest_name", "Cliente"),
                                "code": r.code,
                            },
                        )
                    except Exception:
                        html = f"<h3>Pre-reserva {r.code} expirada</h3>"
                    try:
                        email_service.send_html(
                            r.guest_email,
                            f"Pre-reserva {r.code} expirada",
                            html,
                            email_type="expired",
                        )
                        logger.info(
                            "expiration_email_sent",
                            reservation_id=r.id,
                            code=r.code,
                            email=r.guest_email,
                        )
                    except Exception as e:
                        logger.warning("expiration_email_failed", reservation_id=r.id, error=str(e))
        except Exception as e:
            # No interrumpir el job por fallas de email
            logger.warning("expiration_email_batch_failed", error=str(e))

        duration = time.monotonic() - start_time
        PRERESERVATION_EXPIRY_DURATION.observe(duration)
        logger.info(
            "expire_prereservations_completed",
            count=len(ids),
            duration_ms=round(duration * 1000),
            success=True,
        )
        return len(ids)

    except Exception as e:
        duration = time.monotonic() - start_time
        PRERESERVATION_EXPIRY_DURATION.observe(duration)
        logger.error(
            "expire_prereservations_failed",
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=round(duration * 1000),
        )
        raise


async def send_prereservation_reminders(
    db: AsyncSession, window_minutes: int = 15, batch_size: int = 200
) -> int:
    """Envía recordatorios de pre-reservas que expiran pronto y marca para no duplicar.

    Selecciona pre-reservas con expires_at entre ahora y ahora+ventana que aún no fueron
    marcadas como 'reminder_sent' en internal_notes.
    Retorna cantidad de recordatorios procesados en esta ejecución.
    """
    now = datetime.now(timezone.utc)
    upper = now + timedelta(minutes=window_minutes)

    logger.info(
        "send_prereservation_reminders_started",
        window_minutes=window_minutes,
        batch_size=batch_size,
    )

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
        notes = str(r.internal_notes) if r.internal_notes is not None else ""
        if "reminder_sent" in notes:
            continue

        # Enviar email best-effort
        guest_email = r.guest_email
        if guest_email is not None:
            try:
                guest_name = r.guest_name if r.guest_name is not None else "Cliente"
                try:
                    html = email_service.render(
                        "reminder.html",
                        {
                            "guest_name": str(guest_name),
                            "code": str(r.code),
                        },
                    )
                except Exception:
                    html = f"<h3>Recordatorio: confirmá tu reserva {r.code}</h3>"

                email_service.send_html(
                    str(guest_email),
                    f"Recordatorio reserva {r.code}",
                    html,
                    email_type="pre_reserved",
                )
                PRERESERVATION_REMINDERS_SENT.labels(channel="email").inc()
                logger.info(
                    "reminder_email_sent", reservation_id=r.id, code=r.code, email=str(guest_email)
                )
            except Exception as e:
                logger.warning("reminder_email_failed", reservation_id=r.id, error=str(e))

        # Marcar como recordatorio enviado en internal_notes
        new_notes = (notes + "\n" if notes else "") + "reminder_sent"
        await db.execute(
            update(Reservation).where(Reservation.id == r.id).values(internal_notes=new_notes)
        )
        processed += 1

    if processed:
        await db.commit()

    logger.info("send_prereservation_reminders_completed", count=processed)
    return processed
