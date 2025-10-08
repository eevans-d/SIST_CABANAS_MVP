import pytest
import asyncio
from datetime import date


@pytest.mark.asyncio
async def test_double_confirm_concurrent(test_client, accommodation_factory):
    acc = await accommodation_factory()
    payload = {
        "accommodation_id": acc.id,
        "check_in": date(2025, 2, 10).isoformat(),
        "check_out": date(2025, 2, 12).isoformat(),
        "guests": 2,
        "channel": "whatsapp",
        "contact_name": "Tester",
        "contact_phone": "+5491100000000",
    }
    # Crear pre-reserva
    r = await test_client.post("/api/v1/reservations/pre-reserve", json=payload)
    assert r.status_code == 200
    code = r.json()["code"]

    # Dos confirmaciones concurrentes
    async def confirm():
        return await test_client.post(f"/api/v1/reservations/{code}/confirm")

    res1, res2 = await asyncio.gather(confirm(), confirm())
    # Uno debe ser success, otro error invalid_state
    results = {res1.json().get("error"), res2.json().get("error")}
    assert results == {None, "invalid_state"}
