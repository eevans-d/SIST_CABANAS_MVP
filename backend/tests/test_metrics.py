import re
from datetime import date

import pytest


def _extract_metric(body: str, channel: str) -> int:
    # Aceptar valores como 1 o 1.0
    pattern = rf'^reservations_created_total\{{channel="{channel}"}} (\d+)(?:\.\d+)?$'
    for line in body.splitlines():
        m = re.match(pattern, line)
        if m:
            return int(m.group(1))
    return 0


@pytest.mark.asyncio
async def test_metrics_reservation_counter(test_client, accommodation_factory, db_session):  # type: ignore
    # Métricas antes
    m_before = await test_client.get("/metrics")
    assert m_before.status_code == 200
    before_val = _extract_metric(m_before.text, "whatsapp")

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
    r = await test_client.post("/api/v1/reservations/pre-reserve", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "code" in data and data["code"]

    m_after = await test_client.get("/metrics")
    assert m_after.status_code == 200
    after_val = _extract_metric(m_after.text, "whatsapp")
    assert after_val >= before_val + 1
