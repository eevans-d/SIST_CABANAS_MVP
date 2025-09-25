from __future__ import annotations
from fastapi import APIRouter, Request, Depends
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json

from app.core.security import verify_whatsapp_signature

router = APIRouter()

# Contrato de salida unificado
# {
#   "message_id": str,
#   "canal": "whatsapp",
#   "user_id": str,
#   "timestamp_iso": str,
#   "tipo": "text|audio|image|pdf",
#   "texto": str|None,
#   "media_url": str|None,
#   "metadata": {...}
# }

@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request) -> Dict[str, Any]:
    raw_body = await verify_whatsapp_signature(request)

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        return {"error": "invalid_json"}

    # WhatsApp Business Cloud API estructura (simplificada):
    # {
    #   "entry": [ { "changes": [ { "value": { "messages": [ { ... } ], "contacts": [ { ... } ] } } ] } ]
    # }
    entry = (payload.get("entry") or [{}])[0]
    changes = (entry.get("changes") or [{}])
    if not changes:
        return {"error": "no_changes"}
    value = (changes[0] or {}).get("value", {})
    messages = value.get("messages") or []
    if not messages:
        return {"error": "no_messages"}
    msg = messages[0]

    msg_type = msg.get("type")
    message_id = msg.get("id") or msg.get("wamid") or "unknown"
    from_user = msg.get("from") or (value.get("contacts") or [{}])[0].get("wa_id") or "unknown"
    timestamp = msg.get("timestamp")
    try:
        ts_iso = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).isoformat() if timestamp else datetime.now(timezone.utc).isoformat()
    except Exception:
        ts_iso = datetime.now(timezone.utc).isoformat()

    texto: Optional[str] = None
    media_url: Optional[str] = None
    metadata: Dict[str, Any] = {}

    if msg_type == "text":
        texto = (msg.get("text") or {}).get("body")
    elif msg_type == "audio":
        audio = msg.get("audio", {})
        media_url = audio.get("id")  # En la API real se intercambia por URL via /{media-id}
        metadata["mime_type"] = audio.get("mime_type")
        metadata["voice"] = audio.get("voice")
        metadata["file_size"] = audio.get("file_size")
    elif msg_type == "image":
        image = msg.get("image", {})
        media_url = image.get("id")
        metadata["mime_type"] = image.get("mime_type")
        metadata["caption"] = image.get("caption")
    elif msg_type == "document":
        doc = msg.get("document", {})
        media_url = doc.get("id")
        metadata["filename"] = doc.get("filename")
        metadata["mime_type"] = doc.get("mime_type")
    else:
        msg_type = "text"
        texto = None

    normalized = {
        "message_id": message_id,
        "canal": "whatsapp",
        "user_id": from_user,
        "timestamp_iso": ts_iso,
        "tipo": msg_type,
        "texto": texto,
        "media_url": media_url,
        "metadata": metadata,
    }
    # MVP: sólo devolvemos; futuro: encolar a NLU / workflow
    return normalized
