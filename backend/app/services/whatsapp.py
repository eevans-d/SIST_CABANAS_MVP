from __future__ import annotations

from typing import Dict, Any
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


async def send_text_message(to_phone: str, body: str) -> Dict[str, Any]:
    """Envía un mensaje de texto vía WhatsApp Cloud API.

    En desarrollo o si faltan credenciales, hace no-op para no romper tests.
    Retorna diccionario con status: "sent" | "skipped" | "error".
    """
    # No-op en no producción o sin credenciales válidas
    if settings.ENVIRONMENT != "production":
        logger.info("whatsapp_send_skipped_env", environment=settings.ENVIRONMENT)
        return {"status": "skipped", "reason": "non_production"}
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_ID:
        logger.warning("whatsapp_send_skipped_missing_creds")
        return {"status": "skipped", "reason": "missing_creds"}
    if settings.WHATSAPP_ACCESS_TOKEN == "dummy" or settings.WHATSAPP_PHONE_ID == "dummy":
        logger.info("whatsapp_send_skipped_dummy")
        return {"status": "skipped", "reason": "dummy_creds"}

    try:
        import httpx
        url = f"https://graph.facebook.com/v17.0/{settings.WHATSAPP_PHONE_ID}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": body},
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code // 100 == 2:
                return {"status": "sent"}
            logger.warning("whatsapp_send_error", code=resp.status_code, text=resp.text[:200])
            return {"status": "error", "code": resp.status_code}
    except Exception as e:  # pragma: no cover
        logger.exception("whatsapp_send_exception", error=str(e))
        return {"status": "error", "reason": "exception"}
