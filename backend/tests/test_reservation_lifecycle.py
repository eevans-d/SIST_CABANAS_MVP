import pytest
from datetime import date, timedelta, datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Reservation
from app.models.enums import ReservationStatus

pytestmark = pytest.mark.asyncio


async def test_confirm_then_cancel_reservation(
    test_client, db_session: AsyncSession, accommodation_factory
):
    acc = await accommodation_factory()
    payload = {
        "accommodation_id": acc.id,
        "check_in": (date.today() + timedelta(days=5)).isoformat(),
        "check_out": (date.today() + timedelta(days=7)).isoformat(),
        "guests": 2,
        "channel": "whatsapp",
        "contact_name": "Juan",
        "contact_phone": "+549111111",
    }
    r = await test_client.post("/api/v1/reservations/pre-reserve", json=payload)
    data = r.json()
    assert data.get("code")

    code = data["code"]
    r2 = await test_client.post(f"/api/v1/reservations/{code}/confirm")
    data2 = r2.json()
    assert data2.get("status") == ReservationStatus.CONFIRMED.value

    r3 = await test_client.post(
        f"/api/v1/reservations/{code}/cancel", json={"reason": "cliente pidió"}
    )
    data3 = r3.json()
    assert data3.get("status") == ReservationStatus.CANCELLED.value


async def test_cannot_confirm_expired(test_client, db_session: AsyncSession, accommodation_factory):
    acc = await accommodation_factory()
    payload = {
        "accommodation_id": acc.id,
        "check_in": (date.today() + timedelta(days=10)).isoformat(),
        "check_out": (date.today() + timedelta(days=12)).isoformat(),
        "guests": 2,
        "channel": "whatsapp",
        "contact_name": "Ana",
        "contact_phone": "+549222222",
    }
    r = await test_client.post("/api/v1/reservations/pre-reserve", json=payload)
    data = r.json()
    code = data["code"]

    # Forzar expiración editando directamente expires_at en DB (simplificación)
    q = await db_session.execute(
        Reservation.__table__.update()
        .where(Reservation.code == code)
        .values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
    )
    await db_session.commit()

    r2 = await test_client.post(f"/api/v1/reservations/{code}/confirm")
    data2 = r2.json()
    assert data2.get("error") == "expired"


async def test_invalid_state_transitions(
    test_client, db_session: AsyncSession, accommodation_factory
):
    acc = await accommodation_factory()
    payload = {
        "accommodation_id": acc.id,
        "check_in": (date.today() + timedelta(days=15)).isoformat(),
        "check_out": (date.today() + timedelta(days=16)).isoformat(),
        "guests": 1,
        "channel": "whatsapp",
        "contact_name": "Luis",
        "contact_phone": "+549333333",
    }
    r = await test_client.post("/api/v1/reservations/pre-reserve", json=payload)
    code = r.json()["code"]

    # Cancel first
    await test_client.post(f"/api/v1/reservations/{code}/cancel", json={})

    # Try confirm after cancel
    r2 = await test_client.post(f"/api/v1/reservations/{code}/confirm")
    assert r2.json().get("error") == "invalid_state"
