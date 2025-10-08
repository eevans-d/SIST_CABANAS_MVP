import pytest
import hmac, hashlib, json
from app.core.config import get_settings

pytestmark = pytest.mark.asyncio


async def test_invalid_signature_whatsapp(test_client):
    body = {"entry": []}
    r = await test_client.post(
        "/api/v1/webhooks/whatsapp", json=body, headers={"X-Hub-Signature-256": "sha256=WRONG"}
    )
    assert r.status_code == 403


async def test_normalize_text_whatsapp(test_client):
    settings = get_settings()
    message = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "ABCD",
                                    "from": "12345",
                                    "timestamp": "1700000000",
                                    "type": "text",
                                    "text": {"body": "Hola, hay disponibilidad?"},
                                }
                            ],
                            "contacts": [{"wa_id": "12345"}],
                        }
                    }
                ]
            }
        ]
    }
    raw = json.dumps(message).encode("utf-8")
    sig = hmac.new(settings.WHATSAPP_APP_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    r = await test_client.post(
        "/api/v1/webhooks/whatsapp", data=raw, headers={"X-Hub-Signature-256": f"sha256={sig}"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["canal"] == "whatsapp"
    assert data["tipo"] == "text"
    assert "Hola" in (data["texto"] or "")
