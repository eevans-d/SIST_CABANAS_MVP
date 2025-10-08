import pytest
from datetime import datetime, timedelta, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Reservation
from app.models.enums import ReservationStatus
from app.jobs.cleanup import expire_prereservations

pytestmark = pytest.mark.asyncio


async def test_expire_prereservations(db_session: AsyncSession, reservation_factory):
    # Crear pre-reserva vencida
    r = await reservation_factory(expires_at=datetime.now(UTC) - timedelta(minutes=5))
    assert r.reservation_status == ReservationStatus.PRE_RESERVED.value

    count = await expire_prereservations(db_session)
    assert count == 1

    refreshed = await db_session.get(Reservation, r.id)
    assert refreshed.reservation_status == ReservationStatus.CANCELLED.value
    assert refreshed.cancelled_at is not None


async def test_no_expire_future(db_session: AsyncSession, reservation_factory):
    r = await reservation_factory(expires_at=datetime.now(UTC) + timedelta(minutes=10))
    count = await expire_prereservations(db_session)
    assert count == 0
    refreshed = await db_session.get(Reservation, r.id)
    assert refreshed.reservation_status == ReservationStatus.PRE_RESERVED.value
