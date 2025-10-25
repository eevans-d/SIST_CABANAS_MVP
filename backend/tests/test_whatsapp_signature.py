import hashlib
import hmac
import json
from datetime import datetime, timezone

import pytest

pytestmark = pytest.mark.asyncio

ENDPOINT = "/api/v1/webhooks/whatsapp"


async def test_whatsapp_invalid_signature(test_client, monkeypatch):  # type: ignore
    # Firma inválida -> 403
    body = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "type": "text",
                                    "id": "m1",
                                    "from": "54911",
                                    "timestamp": "1700000000",
                                    "text": {"body": "hola"},
                                }
                            ],
                            "contacts": [{"wa_id": "54911"}],
                        }
                    }
                ]
            }
        ]
    }
    raw = json.dumps(body).encode()
    headers = {"X-Hub-Signature-256": "sha256=deadbeef"}
    resp = await test_client.post(ENDPOINT, content=raw, headers=headers)
    assert resp.status_code == 403
    data = resp.json()
    assert data["detail"] == "Invalid signature"


async def test_whatsapp_valid_signature_text_message(test_client, monkeypatch):  # type: ignore
    from app.core.config import get_settings

    settings = get_settings()
    # Asegurar secreto definido (tests pueden inicializar fallback None)
    if not settings.WHATSAPP_APP_SECRET:
        settings.WHATSAPP_APP_SECRET = "testsecret"  # type: ignore[attr-defined]

    body = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "type": "text",
                                    "id": "m2",
                                    "from": "54922",
                                    "timestamp": "1700000100",
                                    "text": {"body": "disponible el finde?"},
                                }
                            ],
                            "contacts": [{"wa_id": "54922"}],
                        }
                    }
                ]
            }
        ]
    }
    raw = json.dumps(body).encode()
    sig = hmac.new(settings.WHATSAPP_APP_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    headers = {"X-Hub-Signature-256": f"sha256={sig}"}

    resp = await test_client.post(ENDPOINT, content=raw, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["message_id"] == "m2"
    assert data["tipo"] == "text"
    assert data["texto"] == "disponible el finde?"
    assert data["canal"] == "whatsapp"
    # timestamp ISO parseable
    from datetime import datetime

    datetime.fromisoformat(data["timestamp_iso"])
