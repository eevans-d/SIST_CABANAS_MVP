import pytest
from datetime import date
import asyncio

@pytest.mark.asyncio
async def test_double_confirm_concurrency(test_client, accommodation_factory):  # type: ignore
    acc = await accommodation_factory()
    # Crear pre-reserva
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

    async def _confirm():
        return await test_client.post(f"/api/v1/reservations/{code}/confirm")

    # Lanzar dos confirmaciones simultáneas
    resp1, resp2 = await asyncio.gather(_confirm(), _confirm())
    bodies = [resp1.json(), resp2.json()]
    # Debe haber exactamente una confirmación exitosa y un invalid_state
    statuses = sorted(b.get("status") for b in bodies if "status" in b)
    errors = sorted(b.get("error") for b in bodies if "error" in b)
    assert "confirmed" in statuses
    assert "invalid_state" in errors or errors.count("invalid_state") >= 1
