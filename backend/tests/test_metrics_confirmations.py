import re
from datetime import date

import pytest

pytestmark = pytest.mark.asyncio


def _extract_confirmed(body: str, channel: str) -> int:
    pattern = rf'^reservations_confirmed_total\{{channel="{channel}"}} (\d+)(?:\.\d+)?$'
    for line in body.splitlines():
        m = re.match(pattern, line)
        if m:
            return int(m.group(1))
    return 0


async def test_metrics_reservation_confirmed_counter(test_client, accommodation_factory, db_session):  # type: ignore
    m_before = await test_client.get("/metrics")
    before_val = _extract_confirmed(m_before.text, "whatsapp")

    acc = await accommodation_factory()
    payload = {
        "accommodation_id": acc.id,
        "check_in": date(2025, 3, 10).isoformat(),
        "check_out": date(2025, 3, 12).isoformat(),
        "guests": 2,
        "channel": "whatsapp",
        "contact_name": "Tester",
        "contact_phone": "+5491100000000",
    }
    r1 = await test_client.post("/api/v1/reservations/pre-reserve", json=payload)
    code = r1.json()["code"]
    r2 = await test_client.post(f"/api/v1/reservations/{code}/confirm")
    assert r2.status_code == 200

    m_after = await test_client.get("/metrics")
    after_val = _extract_confirmed(m_after.text, "whatsapp")
    assert after_val >= before_val + 1
