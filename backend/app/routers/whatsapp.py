from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.database import get_db
from app.core.security import verify_whatsapp_signature
from app.metrics import NLU_PRE_RESERVE
from app.models import Accommodation
from app.services import nlu
from app.services.button_handlers import handle_button_callback
from app.services.reservations import ReservationService
from app.services.whatsapp import send_text_message
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/webhooks/whatsapp")
async def whatsapp_verify(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
):
    """Verificación GET del webhook de WhatsApp (Meta) durante el onboarding.

    Debe comparar el verify_token con WHATSAPP_VERIFY_TOKEN y devolver hub.challenge.
    """
    from app.core.config import get_settings

    settings = get_settings()
    if not (hub_mode == "subscribe" and hub_challenge and hub_verify_token):
        return {"error": "invalid_params"}
    if hub_verify_token != settings.WHATSAPP_VERIFY_TOKEN:
        return {"error": "forbidden"}
    # Responder con el challenge como texto plano es el comportamiento esperado
    return hub_challenge


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
async def whatsapp_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
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
    changes = entry.get("changes") or [{}]
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
        ts_iso = (
            datetime.fromtimestamp(int(timestamp), tz=timezone.utc).isoformat()
            if timestamp
            else datetime.now(timezone.utc).isoformat()
        )
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
    elif msg_type == "interactive":
        # Manejar respuestas a botones o listas
        interactive = msg.get("interactive", {})
        interactive_type = interactive.get("type")  # "button_reply" o "list_reply"

        if interactive_type == "button_reply":
            button_reply = interactive.get("button_reply", {})
            button_id = button_reply.get("id")
            button_title = button_reply.get("title")
            # Normalizar como texto con el button_id
            texto = button_id
            metadata["button_type"] = "reply"
            metadata["button_id"] = button_id
            metadata["button_title"] = button_title
        elif interactive_type == "list_reply":
            list_reply = interactive.get("list_reply", {})
            list_id = list_reply.get("id")
            list_title = list_reply.get("title")
            list_description = list_reply.get("description")
            # Normalizar como texto con el list_id
            texto = list_id
            metadata["button_type"] = "list"
            metadata["button_id"] = list_id
            metadata["button_title"] = list_title
            metadata["button_description"] = list_description

        msg_type = "text"  # Tratar como texto para procesamiento
    else:
        msg_type = "text"
        texto = None

    normalized: Dict[str, Any] = {
        "message_id": message_id,
        "canal": "whatsapp",
        "user_id": from_user,
        "timestamp_iso": ts_iso,
        "tipo": msg_type,
        "texto": texto,
        "media_url": media_url,
        "metadata": metadata,
    }
    # Orquestación mínima: si es texto, intentar NLU -> pre-reserva
    try:
        if msg_type == "text" and (texto or "").strip():
            # Si es callback de botón, manejar primero
            if metadata.get("button_type"):
                button_id = metadata.get("button_id", "")
                button_result = await handle_button_callback(
                    button_id=button_id, user_phone=str(from_user), db=db
                )
                normalized["auto_action"] = "button_callback"
                normalized["button_result"] = button_result
                return normalized

            # Si no es botón, procesar con NLU
            analysis = nlu.analyze(texto or "")
            normalized["nlu"] = analysis

            # Extraer slots
            dates = analysis.get("dates") or []
            guests = analysis.get("guests")
            parsed: list[str] = [d for d in dates if isinstance(d, str)]
            check_in_iso: Optional[str] = (
                parsed[0] if len(parsed) >= 2 else (parsed[0] if len(parsed) == 1 else None)
            )
            check_out_iso: Optional[str] = parsed[1] if len(parsed) >= 2 else None

            missing = []
            # Resolver alojamiento: si hay exactamente 1 activo
            acc_id: Optional[int] = None
            q = await db.execute(
                select(Accommodation).where(Accommodation.active.is_(True)).limit(2)
            )
            accs = q.scalars().all()
            if len(accs) == 1:
                acc_id = accs[0].id
            else:
                missing.append("accommodation_id")

            if not check_in_iso:
                missing.append("check_in")
            if not check_out_iso:
                missing.append("check_out")
            if not guests:
                missing.append("guests")

            if missing:
                normalized["auto_action"] = "needs_slots"
                normalized["missing"] = missing
                try:
                    NLU_PRE_RESERVE.labels(action="needs_slots", source="whatsapp").inc()
                except Exception:
                    pass
                # Enviar prompt simple de slots faltantes (no-op en dev/test)
                try:
                    missing_human = ", ".join(missing)
                    await send_text_message(
                        str(from_user), f"Para avanzar necesito: {missing_human}."
                    )
                except Exception:
                    pass
                return normalized

            # Crear pre-reserva
            from datetime import date as _date

            try:
                ci = _date.fromisoformat(check_in_iso)  # type: ignore[arg-type]
                co = _date.fromisoformat(check_out_iso)  # type: ignore[arg-type]
            except Exception:
                normalized["auto_action"] = "needs_slots"
                normalized["missing"] = ["check_in", "check_out"]
                return normalized

            service = ReservationService(db)
            result = await service.create_prereservation(
                accommodation_id=acc_id,  # type: ignore[arg-type]
                check_in=ci,
                check_out=co,
                guests=int(guests),
                channel="whatsapp",
                contact_name="Cliente WhatsApp",
                contact_phone=str(from_user),
                contact_email=None,
            )
            if result.get("error"):
                normalized["auto_action"] = "error"
                normalized["error"] = result["error"]
                try:
                    NLU_PRE_RESERVE.labels(action="error", source="whatsapp").inc()
                except Exception:
                    pass
                try:
                    await send_text_message(
                        str(from_user), f"No pude crear la pre-reserva: {result['error']}"
                    )
                except Exception:
                    pass
            else:
                normalized["auto_action"] = "pre_reserved"
                normalized["pre_reservation"] = result
                try:
                    NLU_PRE_RESERVE.labels(action="pre_reserved", source="whatsapp").inc()
                except Exception:
                    pass
                try:
                    code = result.get("code", "")
                    exp = result.get("expires_at", "")
                    await send_text_message(
                        str(from_user), f"Listo! Pre-reserva {code} creada. Vence: {exp}"
                    )
                except Exception:
                    pass
    except Exception:  # pragma: no cover - no romper webhook ante errores no previstos
        normalized["auto_action"] = "error"
        normalized["error"] = "internal"

    return normalized
