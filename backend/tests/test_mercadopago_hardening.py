import pytest, hmac, hashlib, json

pytestmark = pytest.mark.asyncio

ENDPOINT = "/api/v1/mercadopago/webhook"

async def test_mp_missing_signature_when_secret_set(test_client):  # type: ignore
    from app.core.config import get_settings
    settings = get_settings()
    settings.MERCADOPAGO_WEBHOOK_SECRET = "mpsecret"  # type: ignore[attr-defined]

    body = {"id": "MPSEC3", "status": "pending", "amount": 100}
    raw = json.dumps(body).encode()
    # Sin header x-signature
    resp = await test_client.post(ENDPOINT, content=raw)
    assert resp.status_code == 403
    d = resp.json()
    assert d["detail"] == "Invalid signature"

async def test_mp_idempotent_update_fields(test_client):  # type: ignore
    # Sin exigir firma (modo dev)
    from app.core.config import get_settings
    settings = get_settings()
    settings.MERCADOPAGO_WEBHOOK_SECRET = None  # type: ignore[attr-defined]

    body = {"id": "MPIDEMP1", "status": "pending", "amount": 100, "currency": "ARS"}
    raw = json.dumps(body).encode()
    r1 = await test_client.post(ENDPOINT, content=raw)
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["idempotent"] is False

    # Mismo payment id, distinto monto y status -> debe actualizar y ser idempotente
    body2 = {"id": "MPIDEMP1", "status": "approved", "amount": 125, "currency": "ARS"}
    raw2 = json.dumps(body2).encode()
    r2 = await test_client.post(ENDPOINT, content=raw2)
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["idempotent"] is True
    assert d2.get("events_count") == 2
