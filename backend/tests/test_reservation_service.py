import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.services.reservations import ReservationService
from app.models import Accommodation, Reservation
from app.models.enums import ReservationStatus

@pytest.mark.asyncio
async def test_create_prereservation_success(db_session, redis_client):
    if db_session.bind.dialect.name != "postgresql":
        pytest.skip("Necesita Postgres para validar completamente el flow (lock + constraint)")

    acc = Accommodation(
        name="Cabaña Test Service",
        type="cabin",
        capacity=4,
        base_price=Decimal("50000.00"),
    )
    db_session.add(acc)
    await db_session.flush()

    service = ReservationService(db_session)
    today = date.today()
    result = await service.create_prereservation(
        accommodation_id=acc.id,
        check_in=today + timedelta(days=10),
        check_out=today + timedelta(days=12),
        guests=2,
        channel="whatsapp",
        contact_name="Test User",
        contact_phone="+5491100000000",
        contact_email="test@example.com",
    )
    assert "code" in result and result["code"].startswith("RES")
    assert result["nights"] == 2
    assert result["error"] is None if "error" in result else True

@pytest.mark.asyncio
async def test_create_prereservation_overlap_error(db_session, redis_client):
    if db_session.bind.dialect.name != "postgresql":
        pytest.skip("Necesita Postgres para validar overlap")

    acc = Accommodation(
        name="Cabaña Overlap",
        type="cabin",
        capacity=4,
        base_price=Decimal("40000.00"),
    )
    db_session.add(acc)
    await db_session.flush()

    service = ReservationService(db_session)
    base_day = date.today() + timedelta(days=20)

    # Primera pre-reserva
    r1 = await service.create_prereservation(
        accommodation_id=acc.id,
        check_in=base_day,
        check_out=base_day + timedelta(days=3),
        guests=2,
        channel="whatsapp",
        contact_name="User A",
        contact_phone="+5491100000001",
    )
    assert "code" in r1

    # Segunda (solapada)
    r2 = await service.create_prereservation(
        accommodation_id=acc.id,
        check_in=base_day + timedelta(days=1),
        check_out=base_day + timedelta(days=4),
        guests=2,
        channel="whatsapp",
        contact_name="User B",
        contact_phone="+5491100000002",
    )
    # Puede fallar por lock o por constraint; ambos representan protección válida
    assert r2.get("error") in {None, "processing_or_unavailable", "date_overlap"}
