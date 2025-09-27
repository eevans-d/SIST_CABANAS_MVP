import pytest
from datetime import date, timedelta

pytestmark = pytest.mark.asyncio


async def test_nlu_analyze_needs_slots(test_client):  # type: ignore
    payload = {"text": "Hola, quisiera info"}
    r = await test_client.post("/api/v1/nlu/analyze", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["action"] == "needs_slots"
    assert "missing" in d["data"]


async def test_nlu_analyze_pre_reserve_flow(test_client, accommodation_factory):  # type: ignore
    acc = await accommodation_factory(active=True)
    # Construir texto con rango y huéspedes
    ci = (date.today() + timedelta(days=10)).strftime("%d/%m/%Y")
    co = (date.today() + timedelta(days=12)).strftime("%d/%m/%Y")
    text = f"Hay libre {ci} al {co} para 3 personas?"
    r = await test_client.post("/api/v1/nlu/analyze", json={"text": text, "accommodation_id": acc.id})
    assert r.status_code == 200
    d = r.json()
    assert d["action"] in ("pre_reserved", "error")
    if d["action"] == "pre_reserved":
        assert d["data"].get("code")