from datetime import UTC, datetime, timedelta

import pytest
from app.jobs.cleanup import send_prereservation_reminders
from app.models import Reservation
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


async def test_send_prereservation_reminders_once(db_session: AsyncSession, reservation_factory):
    # Pre-reserva que expira en 10 minutos
    r = await reservation_factory(expires_at=datetime.now(UTC) + timedelta(minutes=10))

    count = await send_prereservation_reminders(db_session, window_minutes=15)
    assert count >= 1

    refreshed = await db_session.get(Reservation, r.id)
    assert refreshed.internal_notes and "reminder_sent" in refreshed.internal_notes

    # Segunda ejecución no debe duplicar
    count2 = await send_prereservation_reminders(db_session, window_minutes=15)
    assert count2 in (0,)
