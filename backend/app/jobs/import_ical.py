"""Job de sincronización iCal (import) para todos los alojamientos."""

from __future__ import annotations

import time
from typing import Dict, Optional

import httpx
import structlog
from app.core.database import async_session_maker
from app.metrics import (
    ICAL_EVENTS_IMPORTED,
    ICAL_SYNC_AGE_MINUTES,
    ICAL_SYNC_DURATION,
    ICAL_SYNC_ERRORS,
)
from app.models import Accommodation
from app.services.ical import ICalService
from sqlalchemy import select


async def _fetch_ics(
    client: httpx.AsyncClient, url: str, logger: structlog.stdlib.BoundLogger
) -> Optional[str]:
    """Descarga contenido ICS desde URL."""
    try:
        r = await client.get(url, timeout=20)
        if r.status_code == 200 and r.text:
            return r.text
        else:
            logger.warning("ical_fetch_non_200", url=url, status_code=r.status_code)
    except httpx.TimeoutException:
        logger.warning("ical_fetch_timeout", url=url)
    except Exception as e:
        logger.warning("ical_fetch_error", url=url, error=str(e), error_type=type(e).__name__)
    return None


async def run_ical_sync(logger: Optional[structlog.stdlib.BoundLogger] = None) -> int:
    """Sincroniza iCal para todos los alojamientos con URLs configuradas.

    Retorna la cantidad total de eventos creados en esta ejecución (suma por accommodation/source).
    """
    log = logger or structlog.get_logger()
    start_time = time.monotonic()
    total_created = 0

    log.info("ical_sync_started")

    try:
        async with async_session_maker() as session:
            stmt = select(Accommodation).where(Accommodation.active == True)  # noqa: E712
            res = await session.execute(stmt)
            accommodations = res.scalars().all()

            if not accommodations:
                duration = time.monotonic() - start_time
                ICAL_SYNC_DURATION.observe(duration)
                log.info("ical_sync_completed", count=0, duration_ms=round(duration * 1000))
                return 0

            async with httpx.AsyncClient(follow_redirects=True) as client:
                for acc in accommodations:
                    accommodation_id = acc.id
                    urls: Dict[str, str] = getattr(acc, "ical_import_urls", {}) or {}

                    if not urls:
                        continue

                    for source, url in urls.items():
                        ics_text = await _fetch_ics(client, url, log)
                        if not ics_text:
                            ICAL_SYNC_ERRORS.labels(
                                accommodation_id=str(accommodation_id), error_type="fetch_failed"
                            ).inc()
                            log.warning(
                                "ical_fetch_failed",
                                accommodation_id=accommodation_id,
                                source=source,
                                url=url,
                            )
                            continue

                        try:
                            created = await ICalService(session).import_events(
                                int(accommodation_id), ics_text, source  # type: ignore
                            )
                            total_created += int(created or 0)

                            if created:
                                ICAL_EVENTS_IMPORTED.labels(
                                    accommodation_id=str(accommodation_id), source=source
                                ).inc(created)
                                log.info(
                                    "ical_events_imported",
                                    accommodation_id=accommodation_id,
                                    source=source,
                                    created=created,
                                )

                            # Actualizar métrica de edad de sync
                            ICAL_SYNC_AGE_MINUTES.labels(
                                accommodation_id=str(accommodation_id)
                            ).set(0)

                        except Exception as e:  # pragma: no cover
                            ICAL_SYNC_ERRORS.labels(
                                accommodation_id=str(accommodation_id), error_type=type(e).__name__
                            ).inc()
                            log.error(
                                "ical_import_error",
                                accommodation_id=accommodation_id,
                                source=source,
                                error=str(e),
                                error_type=type(e).__name__,
                            )
                            # Rollback y continuar con el siguiente
                            await session.rollback()
                            continue

        duration = time.monotonic() - start_time
        ICAL_SYNC_DURATION.observe(duration)
        log.info(
            "ical_sync_completed",
            total_created=total_created,
            duration_ms=round(duration * 1000),
            success=True,
        )
        return total_created

    except Exception as e:
        duration = time.monotonic() - start_time
        ICAL_SYNC_DURATION.observe(duration)
        log.error(
            "ical_sync_failed",
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=round(duration * 1000),
        )
        raise
