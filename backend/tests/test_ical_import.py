import pytest
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Reservation

pytestmark = pytest.mark.asyncio

ICS_SAMPLE = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:UID-123@x
DTSTAMP:20250101T000000Z
DTSTART;VALUE=DATE:20251220
DTEND;VALUE=DATE:20251223
SUMMARY:Reserva externa
END:VEVENT
BEGIN:VEVENT
UID:UID-456@x
DTSTAMP:20250101T000000Z
DTSTART;VALUE=DATE:20251225
DTEND;VALUE=DATE:20251227
SUMMARY:Reserva externa 2
END:VEVENT
END:VCALENDAR"""


async def test_import_ical_dedup(test_client, db_session: AsyncSession, accommodation_factory):
    acc = await accommodation_factory()

    # Primera importación
    payload = {"accommodation_id": acc.id, "source": "airbnb", "ical_text": ICS_SAMPLE}
    r1 = await test_client.post("/api/v1/ical/import", json=payload)
    assert r1.json()["created"] == 2

    # Segunda importación (mismos eventos) dedup = 0
    r2 = await test_client.post("/api/v1/ical/import", json=payload)
    assert r2.json()["created"] == 0

    # Export debe contener ambos eventos
    r3 = await test_client.get(f"/api/v1/ical/export/{acc.id}/{acc.ical_export_token}")
    assert r3.status_code == 200
    ics_text = r3.text
    assert "UID:ICAL" not in ics_text  # export usa UID basado en code local, no los originales
    assert "SUMMARY:RESERVA" in ics_text
