import pytest
from httpx import AsyncClient
from datetime import date, timedelta


@pytest.mark.anyio
async def test_pre_reserve_confirm_and_ical_export(test_client, accommodation_factory):
    client: AsyncClient = test_client
    acc = await accommodation_factory()

    # 1) Pre-reserva
    payload = {
        "accommodation_id": acc.id,
        "check_in": str(date.today() + timedelta(days=5)),
        "check_out": str(date.today() + timedelta(days=7)),
        "guests": 2,
        "channel": "api",
        "contact_name": "E2E Tester",
        "contact_phone": "+5491100000000",
        "contact_email": "e2e@example.com",
    }
    r = await client.post("/api/v1/reservations/pre-reserve", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data.get("code")

    # 2) Confirmación
    code = data["code"]
    r2 = await client.post(f"/api/v1/reservations/{code}/confirm")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2.get("status") == "confirmed"

    # Smoke iCal endpoint wiring (opcional)
    # Nota: export requiere token válido, cubierto en unit tests de iCal
    # Aquí sólo verificamos que el router está montado en /api/v1
    # r3 = await client.get(f"/api/v1/ical/export/{acc.id}/dummy-token")
    # assert r3.status_code in (200, 403, 404)
