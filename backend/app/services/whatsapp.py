"""WhatsApp Business API service for sending messages and handling interactions."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

import structlog
from app.core.config import get_settings
from app.utils.retry import retry_async

from .messages import (
    format_availability_response,
    format_error_date_overlap,
    format_error_no_availability,
    format_payment_approved,
    format_payment_pending,
    format_payment_rejected,
    format_payment_reminder,
    format_prereservation_confirmation,
    format_reservation_confirmed,
    format_reservation_expired,
)

logger = structlog.get_logger()
settings = get_settings()


@retry_async(max_attempts=3, base_delay=1.0, operation_name="whatsapp_send_text")
async def _send_text_message_with_retry(
    to_phone: str, body: str, timeout: float = 10.0
) -> Dict[str, Any]:
    """Función interna que hace el envío real con retry automático.

    Esta función se ejecuta solo en producción con credenciales válidas.
    Tiene retry automático para manejar errores transitorios.
    """
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

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)

        # Lanzar excepción en errores para que el retry los maneje
        if resp.status_code == 429:
            # Rate limit - transitorio
            raise ConnectionError(f"WhatsApp rate limit: {resp.status_code}")
        elif resp.status_code >= 500:
            # Server error - transitorio
            raise ConnectionError(f"WhatsApp server error: {resp.status_code}")
        elif resp.status_code >= 400:
            # Client error - permanente (no retry)
            logger.warning("whatsapp_client_error", code=resp.status_code, text=resp.text[:200])
            raise ValueError(f"WhatsApp client error {resp.status_code}: {resp.text[:100]}")

        return {
            "status": "sent",
            "message_id": (await resp.json()).get("messages", [{}])[0].get("id"),
        }


async def send_text_message(to_phone: str, body: str) -> Dict[str, Any]:
    """Envía un mensaje de texto vía WhatsApp Cloud API con retry automático.

    En desarrollo o si faltan credenciales, hace no-op para no romper tests.
    En producción, reintenta automáticamente hasta 3 veces con exponential backoff.

    Retorna diccionario con status: "sent" | "skipped" | "error".
    """
    # No-op en no producción o sin credenciales válidas
    if settings.ENVIRONMENT != "production":
        logger.info("whatsapp_send_skipped_env", environment=settings.ENVIRONMENT)
        return {"status": "skipped", "reason": "non_production"}
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_ID:
        logger.warning("whatsapp_send_skipped_missing_creds")
        return {"status": "skipped", "reason": "missing_creds"}
    if (
        settings.WHATSAPP_ACCESS_TOKEN == "dummy"  # nosec B105
        or settings.WHATSAPP_PHONE_ID == "dummy"  # nosec B105
    ):
        logger.info("whatsapp_send_skipped_dummy")
        return {"status": "skipped", "reason": "dummy_creds"}

    try:
        return await _send_text_message_with_retry(to_phone, body)
    except Exception as e:  # pragma: no cover
        logger.exception("whatsapp_send_exception", error=str(e))
        return {"status": "error", "reason": "exception"}


@retry_async(max_attempts=3, base_delay=1.0, operation_name="whatsapp_send_image")
async def _send_image_message_with_retry(
    to_phone: str, image_url: str, caption: Optional[str] = None, timeout: float = 15.0
) -> Dict[str, Any]:
    """Función interna que hace el envío real de imagen con retry automático."""
    import httpx

    url = f"https://graph.facebook.com/v17.0/{settings.WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    image_payload: Dict[str, Any] = {"link": image_url}
    if caption:
        image_payload["caption"] = caption

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "image",
        "image": image_payload,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)

        if resp.status_code == 429:
            raise ConnectionError(f"WhatsApp rate limit: {resp.status_code}")
        elif resp.status_code >= 500:
            raise ConnectionError(f"WhatsApp server error: {resp.status_code}")
        elif resp.status_code >= 400:
            logger.warning(
                "whatsapp_image_client_error", code=resp.status_code, text=resp.text[:200]
            )
            raise ValueError(f"WhatsApp client error {resp.status_code}: {resp.text[:100]}")

        return {
            "status": "sent",
            "message_id": (await resp.json()).get("messages", [{}])[0].get("id"),
        }


async def send_image_message(
    to_phone: str, image_url: str, caption: Optional[str] = None
) -> Dict[str, Any]:
    """Envía una imagen vía WhatsApp Cloud API con retry automático.

    Args:
        to_phone: Número de teléfono destino
        image_url: URL pública de la imagen (debe ser HTTPS)
        caption: Texto opcional que acompaña la imagen

    Returns:
        Dict con status del envío
    """
    # No-op en no producción o sin credenciales válidas
    if settings.ENVIRONMENT != "production":
        logger.info("whatsapp_image_skipped_env", environment=settings.ENVIRONMENT)
        return {"status": "skipped", "reason": "non_production"}
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_ID:
        logger.warning("whatsapp_image_skipped_missing_creds")
        return {"status": "skipped", "reason": "missing_creds"}
    if (
        settings.WHATSAPP_ACCESS_TOKEN == "dummy"  # nosec B105
        or settings.WHATSAPP_PHONE_ID == "dummy"  # nosec B105
    ):
        logger.info("whatsapp_image_skipped_dummy")
        return {"status": "skipped", "reason": "dummy_creds"}

    try:
        return await _send_image_message_with_retry(to_phone, image_url, caption)
    except Exception as e:  # pragma: no cover
        logger.exception("whatsapp_image_exception", error=str(e))
        return {"status": "error", "reason": "exception"}


# ========== High-level message functions ==========


async def send_prereservation_confirmation(
    phone: str,
    reservation: Dict[str, Any],
    accommodation: Dict[str, Any],
    payment_link: str,
    expiration_minutes: int = 60,
) -> Dict[str, Any]:
    """Envía confirmación detallada de pre-reserva vía WhatsApp.

    Args:
        phone: Número de teléfono del cliente
        reservation: Datos de la reserva
        accommodation: Datos del alojamiento
        payment_link: URL de pago de Mercado Pago
        expiration_minutes: Tiempo de expiración en minutos

    Returns:
        Dict con status del envío
    """
    message = format_prereservation_confirmation(
        reservation=reservation,
        accommodation=accommodation,
        payment_link=payment_link,
        expiration_minutes=expiration_minutes,
    )

    result = await send_text_message(phone, message)
    logger.info(
        "prereservation_confirmation_sent",
        phone=phone,
        reservation_code=reservation.get("code"),
        status=result.get("status"),
    )
    return result


async def send_reservation_confirmed(
    phone: str, reservation: Dict[str, Any], accommodation: Dict[str, Any]
) -> Dict[str, Any]:
    """Envía confirmación definitiva de reserva (post-pago).

    Args:
        phone: Número de teléfono del cliente
        reservation: Datos de la reserva
        accommodation: Datos del alojamiento

    Returns:
        Dict con status del envío
    """
    message = format_reservation_confirmed(reservation=reservation, accommodation=accommodation)

    result = await send_text_message(phone, message)
    logger.info(
        "reservation_confirmed_sent",
        phone=phone,
        reservation_code=reservation.get("code"),
        status=result.get("status"),
    )
    return result


async def send_error_date_overlap(
    phone: str, accommodation_name: str, check_in: date, check_out: date
) -> Dict[str, Any]:
    """Envía mensaje de error cuando las fechas no están disponibles.

    Args:
        phone: Número de teléfono del cliente
        accommodation_name: Nombre del alojamiento
        check_in: Fecha de entrada solicitada
        check_out: Fecha de salida solicitada

    Returns:
        Dict con status del envío
    """
    message = format_error_date_overlap(
        accommodation_name=accommodation_name, check_in=check_in, check_out=check_out
    )

    result = await send_text_message(phone, message)
    logger.info("error_date_overlap_sent", phone=phone, status=result.get("status"))
    return result


async def send_error_no_availability(phone: str, check_in: date, check_out: date) -> Dict[str, Any]:
    """Envía mensaje cuando no hay disponibilidad en ningún alojamiento.

    Args:
        phone: Número de teléfono del cliente
        check_in: Fecha de entrada solicitada
        check_out: Fecha de salida solicitada

    Returns:
        Dict con status del envío
    """
    message = format_error_no_availability(check_in=check_in, check_out=check_out)

    result = await send_text_message(phone, message)
    logger.info("error_no_availability_sent", phone=phone, status=result.get("status"))
    return result


async def send_availability_response(
    phone: str, accommodation: Dict[str, Any], check_in: date, check_out: date, price: Decimal
) -> Dict[str, Any]:
    """Envía mensaje mostrando disponibilidad de un alojamiento.

    Args:
        phone: Número de teléfono del cliente
        accommodation: Datos del alojamiento
        check_in: Fecha de entrada
        check_out: Fecha de salida
        price: Precio calculado para el período

    Returns:
        Dict con status del envío
    """
    message = format_availability_response(
        accommodation=accommodation, check_in=check_in, check_out=check_out, price=price
    )

    result = await send_text_message(phone, message)
    logger.info(
        "availability_response_sent",
        phone=phone,
        accommodation_name=accommodation.get("name"),
        status=result.get("status"),
    )
    return result


async def send_payment_reminder(
    phone: str, reservation_code: str, payment_link: str, minutes_remaining: int
) -> Dict[str, Any]:
    """Envía recordatorio de pago pendiente.

    Args:
        phone: Número de teléfono del cliente
        reservation_code: Código de la reserva
        payment_link: URL de pago
        minutes_remaining: Minutos restantes antes de expiración

    Returns:
        Dict con status del envío
    """
    message = format_payment_reminder(
        reservation_code=reservation_code,
        payment_link=payment_link,
        minutes_remaining=minutes_remaining,
    )

    result = await send_text_message(phone, message)
    logger.info(
        "payment_reminder_sent",
        phone=phone,
        reservation_code=reservation_code,
        status=result.get("status"),
    )
    return result


async def send_reservation_expired(phone: str, reservation_code: str) -> Dict[str, Any]:
    """Envía mensaje cuando una pre-reserva ha expirado.

    Args:
        phone: Número de teléfono del cliente
        reservation_code: Código de la reserva expirada

    Returns:
        Dict con status del envío
    """
    message = format_reservation_expired(reservation_code=reservation_code)

    result = await send_text_message(phone, message)
    logger.info(
        "reservation_expired_sent",
        phone=phone,
        reservation_code=reservation_code,
        status=result.get("status"),
    )
    return result


async def send_accommodation_info_with_photo(
    phone: str, accommodation: Dict[str, Any]
) -> Dict[str, Any]:
    """Envía información de alojamiento con foto principal si existe.

    Args:
        phone: Número de teléfono del cliente
        accommodation: Datos del alojamiento (con campo photos)

    Returns:
        Dict con status del envío
    """
    # Obtener foto principal
    photos = accommodation.get("photos", [])
    main_photo = None

    if photos:
        # Buscar foto marcada como primary, o tomar la primera
        main_photo = next((p for p in photos if p.get("is_primary")), photos[0] if photos else None)

    # Enviar foto si existe
    if main_photo and main_photo.get("url"):
        caption = f"📸 *{accommodation.get('name', 'Alojamiento')}*"
        photo_result = await send_image_message(
            to_phone=phone, image_url=main_photo["url"], caption=caption
        )
        logger.info(
            "accommodation_photo_sent",
            phone=phone,
            accommodation_name=accommodation.get("name"),
            photo_status=photo_result.get("status"),
        )

    # Enviar detalles en texto
    capacity = accommodation.get("capacity", "N/A")
    base_price = accommodation.get("base_price", 0)
    description = accommodation.get("description", "")

    message = f"""🏠 *{accommodation.get('name', 'Alojamiento')}*

📏 Capacidad: {capacity} personas
💰 Precio base: ${float(base_price):.2f}/noche

{description}

¿Te gustaría consultar disponibilidad para fechas específicas?"""

    result = await send_text_message(phone, message)
    logger.info(
        "accommodation_info_sent",
        phone=phone,
        accommodation_name=accommodation.get("name"),
        status=result.get("status"),
    )

    return result


# Funciones específicas para estados de pago con retry automático
@retry_async(max_attempts=3, base_delay=1.0, operation_name="whatsapp_payment_notification")
async def send_payment_approved(
    phone: str,
    guest_name: str,
    reservation_code: str,
    check_in: str,
    check_out: str,
    accommodation_name: str,
) -> Dict[str, Any]:
    """Envía notificación de pago aprobado exitosamente.

    Tiene retry automático (3 intentos) para manejar errores transitorios de WhatsApp API.

    Args:
        phone: Número de teléfono del huésped
        guest_name: Nombre del huésped
        reservation_code: Código de la reserva
        check_in: Fecha de entrada (formato dd/mm/yyyy)
        check_out: Fecha de salida (formato dd/mm/yyyy)
        accommodation_name: Nombre del alojamiento

    Returns:
        Dict con resultado del envío
    """
    message = format_payment_approved(
        guest_name, reservation_code, check_in, check_out, accommodation_name
    )
    result = await send_text_message(phone, message)
    logger.info(
        "payment_approved_sent",
        phone=phone,
        reservation_code=reservation_code,
        status=result.get("status"),
    )
    return result


@retry_async(max_attempts=3, base_delay=1.0, operation_name="whatsapp_payment_notification")
async def send_payment_rejected(
    phone: str, guest_name: str, reservation_code: str, amount: str
) -> Dict[str, Any]:
    """Envía notificación de pago rechazado.

    Tiene retry automático (3 intentos) para manejar errores transitorios de WhatsApp API.

    Args:
        phone: Número de teléfono del huésped
        guest_name: Nombre del huésped
        reservation_code: Código de la reserva
        amount: Monto del pago rechazado (formato con separador de miles)

    Returns:
        Dict con resultado del envío
    """
    message = format_payment_rejected(guest_name, reservation_code, amount)
    result = await send_text_message(phone, message)
    logger.info(
        "payment_rejected_sent",
        phone=phone,
        reservation_code=reservation_code,
        status=result.get("status"),
    )
    return result


@retry_async(max_attempts=3, base_delay=1.0, operation_name="whatsapp_payment_notification")
async def send_payment_pending(
    phone: str, guest_name: str, reservation_code: str, amount: str
) -> Dict[str, Any]:
    """Envía notificación de pago pendiente de procesamiento.

    Tiene retry automático (3 intentos) para manejar errores transitorios de WhatsApp API.

    Args:
        phone: Número de teléfono del huésped
        guest_name: Nombre del huésped
        reservation_code: Código de la reserva
        amount: Monto del pago pendiente (formato con separador de miles)

    Returns:
        Dict con resultado del envío
    """
    message = format_payment_pending(guest_name, reservation_code, amount)
    result = await send_text_message(phone, message)
    logger.info(
        "payment_pending_sent",
        phone=phone,
        reservation_code=reservation_code,
        status=result.get("status"),
    )
    return result


# ========== Interactive Buttons & Lists ==========


@retry_async(max_attempts=3, base_delay=1.0, operation_name="whatsapp_send_buttons")
async def _send_interactive_buttons_with_retry(
    to_phone: str,
    body_text: str,
    buttons: list[Dict[str, str]],
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """Envía mensaje con botones interactivos (hasta 3 botones).

    Args:
        to_phone: Número de teléfono destino
        body_text: Texto principal del mensaje
        buttons: Lista de botones [{"id": "btn_1", "title": "Opción 1"}, ...]
        header_text: Texto de encabezado (opcional)
        footer_text: Texto de pie (opcional)
        timeout: Timeout de la request

    Returns:
        Dict con status del envío

    Raises:
        ValueError: Si hay más de 3 botones o formato inválido
    """
    import httpx

    if len(buttons) > 3:
        raise ValueError("WhatsApp solo soporta hasta 3 botones")

    if not all(isinstance(btn, dict) and "id" in btn and "title" in btn for btn in buttons):
        raise ValueError("Cada botón debe tener 'id' y 'title'")

    url = f"https://graph.facebook.com/v17.0/{settings.WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # Construir payload de botones interactivos
    interactive_payload: Dict[str, Any] = {
        "type": "button",
        "body": {"text": body_text},
        "action": {
            "buttons": [
                {"type": "reply", "reply": {"id": btn["id"], "title": btn["title"]}}
                for btn in buttons
            ]
        },
    }

    if header_text:
        interactive_payload["header"] = {"type": "text", "text": header_text}
    if footer_text:
        interactive_payload["footer"] = {"text": footer_text}

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "interactive",
        "interactive": interactive_payload,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)

        if resp.status_code == 429:
            raise ConnectionError(f"WhatsApp rate limit: {resp.status_code}")
        elif resp.status_code >= 500:
            raise ConnectionError(f"WhatsApp server error: {resp.status_code}")
        elif resp.status_code >= 400:
            logger.warning(
                "whatsapp_buttons_client_error", code=resp.status_code, text=resp.text[:200]
            )
            raise ValueError(f"WhatsApp client error {resp.status_code}: {resp.text[:100]}")

        return {
            "status": "sent",
            "message_id": (await resp.json()).get("messages", [{}])[0].get("id"),
        }


async def send_interactive_buttons(
    to_phone: str,
    body_text: str,
    buttons: list[Dict[str, str]],
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Envía mensaje con botones interactivos de WhatsApp.

    Permite enviar hasta 3 botones que el usuario puede presionar.
    Cada botón tiene un ID único y un título visible.

    Args:
        to_phone: Número de teléfono destino
        body_text: Texto principal del mensaje
        buttons: Lista de botones [{"id": "confirm", "title": "✅ Confirmar"}, ...]
        header_text: Encabezado opcional (ej: "🏠 Alojamiento Disponible")
        footer_text: Pie opcional (ej: "Expira en 60 minutos")

    Returns:
        Dict con status: "sent" | "skipped" | "error"

    Example:
        await send_interactive_buttons(
            to_phone="+5491112345678",
            body_text="¿Confirmas la reserva para 2 noches?",
            buttons=[
                {"id": "confirm_res", "title": "✅ Confirmar"},
                {"id": "change_dates", "title": "📅 Cambiar fechas"},
                {"id": "cancel_res", "title": "❌ Cancelar"}
            ],
            header_text="🏠 Cabaña del Bosque",
            footer_text="Expira en 60 minutos"
        )
    """
    # No-op en no producción o sin credenciales
    if settings.ENVIRONMENT != "production":
        logger.info("whatsapp_buttons_skipped_env", environment=settings.ENVIRONMENT)
        return {"status": "skipped", "reason": "non_production"}
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_ID:
        logger.warning("whatsapp_buttons_skipped_missing_creds")
        return {"status": "skipped", "reason": "missing_creds"}
    if (
        settings.WHATSAPP_ACCESS_TOKEN == "dummy"  # nosec B105
        or settings.WHATSAPP_PHONE_ID == "dummy"  # nosec B105
    ):
        logger.info("whatsapp_buttons_skipped_dummy")
        return {"status": "skipped", "reason": "dummy_creds"}

    try:
        return await _send_interactive_buttons_with_retry(
            to_phone, body_text, buttons, header_text, footer_text
        )
    except Exception as e:  # pragma: no cover
        logger.exception("whatsapp_buttons_exception", error=str(e))
        return {"status": "error", "reason": "exception"}


@retry_async(max_attempts=3, base_delay=1.0, operation_name="whatsapp_send_list")
async def _send_interactive_list_with_retry(
    to_phone: str,
    body_text: str,
    button_text: str,
    sections: list[Dict[str, Any]],
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """Envía mensaje con lista interactiva (hasta 10 opciones por sección).

    Args:
        to_phone: Número de teléfono destino
        body_text: Texto principal del mensaje
        button_text: Texto del botón que abre la lista (ej: "Ver opciones")
        sections: Lista de secciones con opciones
        header_text: Encabezado opcional
        footer_text: Pie opcional
        timeout: Timeout de la request

    Returns:
        Dict con status del envío

    Example sections:
        [
            {
                "title": "Cabañas Disponibles",
                "rows": [
                    {"id": "acc_1", "title": "Cabaña del Bosque", "description": "$15,000/noche"},
                    {"id": "acc_2", "title": "Casa del Lago", "description": "$12,000/noche"}
                ]
            }
        ]
    """
    import httpx

    url = f"https://graph.facebook.com/v17.0/{settings.WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    interactive_payload: Dict[str, Any] = {
        "type": "list",
        "body": {"text": body_text},
        "action": {
            "button": button_text,
            "sections": sections,
        },
    }

    if header_text:
        interactive_payload["header"] = {"type": "text", "text": header_text}
    if footer_text:
        interactive_payload["footer"] = {"text": footer_text}

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "interactive",
        "interactive": interactive_payload,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)

        if resp.status_code == 429:
            raise ConnectionError(f"WhatsApp rate limit: {resp.status_code}")
        elif resp.status_code >= 500:
            raise ConnectionError(f"WhatsApp server error: {resp.status_code}")
        elif resp.status_code >= 400:
            logger.warning(
                "whatsapp_list_client_error", code=resp.status_code, text=resp.text[:200]
            )
            raise ValueError(f"WhatsApp client error {resp.status_code}: {resp.text[:100]}")

        return {
            "status": "sent",
            "message_id": (await resp.json()).get("messages", [{}])[0].get("id"),
        }


async def send_interactive_list(
    to_phone: str,
    body_text: str,
    button_text: str,
    sections: list[Dict[str, Any]],
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Envía mensaje con lista interactiva de WhatsApp.

    Permite enviar listas con hasta 10 opciones por sección.
    Ideal para mostrar múltiples alojamientos, fechas, etc.

    Args:
        to_phone: Número de teléfono destino
        body_text: Texto principal del mensaje
        button_text: Texto del botón para abrir lista (ej: "Ver alojamientos")
        sections: Lista de secciones con sus opciones
        header_text: Encabezado opcional
        footer_text: Pie opcional

    Returns:
        Dict con status: "sent" | "skipped" | "error"

    Example:
        await send_interactive_list(
            to_phone="+5491112345678",
            body_text="Tenemos 3 alojamientos disponibles para tus fechas:",
            button_text="Ver alojamientos 🏠",
            sections=[
                {
                    "title": "Disponibles",
                    "rows": [
                        {
                            "id": "acc_1",
                            "title": "Cabaña del Bosque",
                            "description": "$15,000/noche · 4 huéspedes"
                        },
                        {
                            "id": "acc_2",
                            "title": "Casa del Lago",
                            "description": "$12,000/noche · 6 huéspedes"
                        }
                    ]
                }
            ],
            header_text="🏠 Alojamientos Disponibles",
            footer_text="Precios para 20-22 Oct"
        )
    """
    # No-op en no producción o sin credenciales
    if settings.ENVIRONMENT != "production":
        logger.info("whatsapp_list_skipped_env", environment=settings.ENVIRONMENT)
        return {"status": "skipped", "reason": "non_production"}
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_ID:
        logger.warning("whatsapp_list_skipped_missing_creds")
        return {"status": "skipped", "reason": "missing_creds"}
    if (
        settings.WHATSAPP_ACCESS_TOKEN == "dummy"  # nosec B105
        or settings.WHATSAPP_PHONE_ID == "dummy"  # nosec B105
    ):
        logger.info("whatsapp_list_skipped_dummy")
        return {"status": "skipped", "reason": "dummy_creds"}

    try:
        return await _send_interactive_list_with_retry(
            to_phone, body_text, button_text, sections, header_text, footer_text
        )
    except Exception as e:  # pragma: no cover
        logger.exception("whatsapp_list_exception", error=str(e))
        return {"status": "error", "reason": "exception"}
