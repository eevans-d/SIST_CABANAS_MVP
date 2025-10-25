from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_prereservation_expires_and_confirm_fails(
    test_client, accommodation_factory, db_session
):
    client: AsyncClient = test_client
    acc = await accommodation_factory()

    payload = {
        "accommodation_id": acc.id,
        "check_in": str(date.today() + timedelta(days=2)),
        "check_out": str(date.today() + timedelta(days=3)),
        "guests": 2,
        "channel": "api",
        "contact_name": "Expire Tester",
        "contact_phone": "+5491100000000",
        "contact_email": "expire@example.com",
    }
    r = await client.post("/api/v1/reservations/pre-reserve", json=payload)
    assert r.status_code == 200
    data = r.json()
    code = data["code"]

    # Forzar expiración inmediata en DB
    from app.models import Reservation
    from sqlalchemy import select

    # Buscar reserva por code y actualizar expires_at para forzar expiración
    res = (
        await db_session.execute(select(Reservation).where(Reservation.code == code))
    ).scalar_one()
    obj = res
    now = datetime.now(UTC)
    obj.expires_at = now - timedelta(minutes=1)
    await db_session.commit()

    # Intentar confirmar debe indicar error "expired" (contrato actual: 200 con campo error)
    r2 = await client.post(f"/api/v1/reservations/{code}/confirm")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2.get("error") == "expired"
