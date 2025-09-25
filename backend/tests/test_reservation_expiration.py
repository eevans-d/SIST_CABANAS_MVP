import pytest
from datetime import date, timedelta, datetime

@pytest.mark.asyncio
async def test_prereservation_expired_cannot_confirm(test_client, accommodation_factory, db_session):
    acc = await accommodation_factory()
    payload = {
        "accommodation_id": acc.id,
        "check_in": date(2025, 3, 10).isoformat(),
        "check_out": date(2025, 3, 12).isoformat(),
        "guests": 2,
        "channel": "whatsapp",
        "contact_name": "Tester",
        "contact_phone": "+5491100000000"
    }
    r = await test_client.post("/api/v1/reservations/pre-reserve", json=payload)
    assert r.status_code == 200
    code = r.json()["code"]

    # Forzar expiración directa en DB
    from app.models import Reservation
    q = await db_session.execute(
        Reservation.__table__.update().where(Reservation.code == code).values(expires_at=datetime.utcnow() - timedelta(minutes=1))
    )
    await db_session.commit()

    c = await test_client.post(f"/api/v1/reservations/{code}/confirm")
    assert c.status_code == 200
    data = c.json()
    assert data.get("error") == "expired"
