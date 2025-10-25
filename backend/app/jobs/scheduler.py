from __future__ import annotations

"""Scheduler simple para jobs periódicos.

Se ejecuta con `python -m app.jobs.scheduler` dentro del contenedor `scheduler`.
Coordina:
- expiración y recordatorios de pre-reservas
- importación iCal
"""

import asyncio

import structlog
from app.core.config import get_settings
from app.core.database import async_session_maker
from app.jobs.cleanup import expire_prereservations, send_prereservation_reminders
from app.jobs.import_ical import run_ical_sync


async def main() -> None:
    settings = get_settings()
    logger = structlog.get_logger()
    exp_interval = settings.JOB_EXPIRATION_INTERVAL_SECONDS
    ical_interval = getattr(settings, "JOB_ICAL_INTERVAL_SECONDS", 300)
    logger.info("scheduler_start", exp_interval=exp_interval, ical_interval=ical_interval)

    async def loop_expiration():
        while True:
            try:
                async with async_session_maker() as session:
                    expired = await expire_prereservations(session)
                    reminders = await send_prereservation_reminders(session)
                    if expired or reminders:
                        logger.info("scheduler_cleanup_cycle", expired=expired, reminders=reminders)
            except Exception as e:  # pragma: no cover
                logger.error("scheduler_cleanup_error", error=str(e))
            await asyncio.sleep(exp_interval)

    async def loop_ical():
        while True:
            try:
                created = await run_ical_sync(logger)
                if created:
                    logger.info("scheduler_ical_cycle", created=created)
            except Exception as e:  # pragma: no cover
                logger.error("scheduler_ical_error", error=str(e))
            await asyncio.sleep(ical_interval)

    await asyncio.gather(loop_expiration(), loop_ical())


if __name__ == "__main__":
    asyncio.run(main())
