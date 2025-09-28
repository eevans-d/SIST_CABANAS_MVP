from __future__ import annotations

"""Job de sincronización iCal (import) para todos los alojamientos.

Lee `Accommodation.ical_import_urls` (dict {source: url}) y para cada entrada:
- descarga el ICS (httpx, timeout corto)
- delega a ICalService.import_events()
- maneja deduplicación y actualiza last_ical_sync_at (lo hace el servicio)

Este módulo expone `run_ical_sync()` para ser llamado desde el lifespan
o desde un scheduler externo (ver app.jobs.scheduler).
"""

from typing import Dict, Optional
import asyncio
import structlog
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_session_maker
from app.models import Accommodation
from app.services.ical import ICalService


async def _fetch_ics(client: httpx.AsyncClient, url: str) -> Optional[str]:
    try:
        r = await client.get(url, timeout=20)
        if r.status_code == 200 and r.text:
            return r.text
    except Exception:
        return None
    return None


async def run_ical_sync(logger: Optional[structlog.stdlib.BoundLogger] = None) -> int:
    """Sincroniza iCal para todos los alojamientos con URLs configuradas.

    Retorna la cantidad total de eventos creados en esta ejecución (suma por accommodation/source).
    """
    log = logger or structlog.get_logger()
    total_created = 0
    async with async_session_maker() as session:
        stmt = select(Accommodation).where(Accommodation.active == True)  # noqa: E712
        res = await session.execute(stmt)
        accommodations = res.scalars().all()
        if not accommodations:
            return 0
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for acc in accommodations:
                urls: Dict[str, str] = getattr(acc, "ical_import_urls", {}) or {}
                if not urls:
                    continue
                for source, url in urls.items():
                    ics_text = await _fetch_ics(client, url)
                    if not ics_text:
                        log.warning("ical_fetch_failed", accommodation_id=acc.id, source=source)
                        continue
                    try:
                        accommodation_id = int(getattr(acc, "id"))
                        created = await ICalService(session).import_events(accommodation_id, ics_text, source)
                        total_created += int(created or 0)
                        if created:
                            log.info("ical_events_imported", accommodation_id=accommodation_id, source=source, created=created)
                    except Exception as e:  # pragma: no cover
                        log.error("ical_import_error", accommodation_id=int(getattr(acc, "id")), source=source, error=str(e))
                        # continuar con el siguiente
                        await session.rollback()
                        continue
    return total_created
