import hashlib
import hmac
import json

import pytest

pytestmark = pytest.mark.asyncio

ENDPOINT = "/api/v1/mercadopago/webhook"


async def test_mp_invalid_signature(test_client, monkeypatch):  # type: ignore
    # Configurar secreto
    from app.core.config import get_settings

    settings = get_settings()
    settings.MERCADOPAGO_WEBHOOK_SECRET = "mpsecret"  # type: ignore[attr-defined]

    body = {"id": "MPSEC1", "status": "pending", "amount": 100, "currency": "ARS"}
    raw = json.dumps(body).encode()
    # Firma incorrecta
    headers = {"x-signature": "ts=1,v1=deadbeef"}
    resp = await test_client.post(ENDPOINT, content=raw, headers=headers)
    assert resp.status_code == 403, resp.text
    data = resp.json()
    assert data["detail"] == "Invalid signature"


async def test_mp_valid_signature(test_client, monkeypatch):  # type: ignore
    from app.core.config import get_settings

    settings = get_settings()
    settings.MERCADOPAGO_WEBHOOK_SECRET = "mpsecret"  # type: ignore[attr-defined]

    body = {"id": "MPSEC2", "status": "approved", "amount": 2500, "currency": "ARS"}
    raw = json.dumps(body).encode()
    sig = hmac.new(settings.MERCADOPAGO_WEBHOOK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    headers = {"x-signature": f"ts=1,v1={sig}"}
    resp = await test_client.post(ENDPOINT, content=raw, headers=headers)
    assert resp.status_code == 200, resp.text
    d = resp.json()
    assert d["status"] == "ok"
    assert d["idempotent"] is False
