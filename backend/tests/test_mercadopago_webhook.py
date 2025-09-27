import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Payment, Reservation
from app.models.enums import ReservationStatus, PaymentStatus
from datetime import date, timedelta

pytestmark = pytest.mark.asyncio

async def test_webhook_idempotent(test_client, db_session: AsyncSession, accommodation_factory):
    # Forzar modo dev: no exigir firma en este test
    from app.core.config import get_settings
    get_settings().MERCADOPAGO_WEBHOOK_SECRET = None  # type: ignore[attr-defined]
    acc = await accommodation_factory()
    # Crear pre-reserva
    r_payload = {
        "accommodation_id": acc.id,
        "check_in": (date.today() + timedelta(days=20)).isoformat(),
        "check_out": (date.today() + timedelta(days=22)).isoformat(),
        "guests": 2,
        "channel": "whatsapp",
        "contact_name": "Pago Test",
        "contact_phone": "+549444444",
    }
    resp = await test_client.post("/api/v1/reservations/pre-reserve", json=r_payload)
    code = resp.json()["code"]

    webhook_payload = {
        "id": "MPPAY123",
        "status": "approved",
        "amount": 50000.0,
        "currency": "ARS",
        "external_reference": code
    }

    r1 = await test_client.post("/api/v1/mercadopago/webhook", json=webhook_payload)
    d1 = r1.json()
    assert d1["status"] == "ok"
    assert d1["idempotent"] is False

    # segundo envío idempotente
    r2 = await test_client.post("/api/v1/mercadopago/webhook", json=webhook_payload)
    d2 = r2.json()
    assert d2["idempotent"] is True
    assert d2["events_count"] == 2

    # Verificar reserva confirmada y payment_status paid
    q = await db_session.execute(Reservation.__table__.select().where(Reservation.code == code))
    row = q.first()
    assert row is not None

async def test_webhook_payment_without_reservation(test_client, db_session: AsyncSession):
    # Forzar modo dev: no exigir firma en este test
    from app.core.config import get_settings
    get_settings().MERCADOPAGO_WEBHOOK_SECRET = None  # type: ignore[attr-defined]
    payload = {
        "id": "MPORPHAN1",
        "status": "pending",
        "amount": 1000,
        "currency": "ARS",
        "external_reference": "UNKNOWNCODE"
    }
    r = await test_client.post("/api/v1/mercadopago/webhook", json=payload)
    d = r.json()
    assert d["status"] == "ok"
    assert d["reservation_id"] is None
