"""Mensajes estructurados para WhatsApp con formato claro y amigable.

Proporciona funciones para generar mensajes formateados para diferentes
situaciones: confirmaciones, errores, disponibilidad, etc.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger()


def format_prereservation_confirmation(
    reservation: Dict[str, Any],
    accommodation: Dict[str, Any],
    payment_link: str,
    expiration_minutes: int = 60,
) -> str:
    """Genera mensaje de confirmación de pre-reserva con todos los detalles.

    Args:
        reservation: Diccionario con datos de reserva (code, check_in, check_out, etc.)
        accommodation: Diccionario con datos del alojamiento (name, etc.)
        payment_link: URL de pago de Mercado Pago
        expiration_minutes: Tiempo de expiración en minutos

    Returns:
        str: Mensaje formateado para WhatsApp con emojis y formato markdown
    """
    # Formatear fechas
    check_in = reservation.get("check_in")
    check_out = reservation.get("check_out")

    if isinstance(check_in, str):
        check_in = datetime.fromisoformat(check_in.replace("Z", "+00:00")).date()
    if isinstance(check_out, str):
        check_out = datetime.fromisoformat(check_out.replace("Z", "+00:00")).date()

    check_in_str = check_in.strftime("%d/%m/%Y") if isinstance(check_in, date) else str(check_in)
    check_out_str = (
        check_out.strftime("%d/%m/%Y") if isinstance(check_out, date) else str(check_out)
    )

    # Formatear montos
    total_price = reservation.get("total_price", 0)
    deposit_amount = reservation.get("deposit_amount", 0)

    if isinstance(total_price, (int, float, Decimal)):
        total_str = f"${float(total_price):.2f}"
    else:
        total_str = f"${total_price}"

    if isinstance(deposit_amount, (int, float, Decimal)):
        deposit_str = f"${float(deposit_amount):.2f}"
    else:
        deposit_str = f"${deposit_amount}"

    message = f"""✅ *Pre-reserva Confirmada*

📋 *Código:* {reservation.get('code', 'N/A')}
🏠 *Alojamiento:* {accommodation.get('name', 'N/A')}
📅 *Check-in:* {check_in_str}
📅 *Check-out:* {check_out_str}
👥 *Huéspedes:* {reservation.get('guests_count', 0)}
💰 *Total:* {total_str}
💵 *Seña a pagar:* {deposit_str}

⏰ *Importante:* Esta pre-reserva expira en {expiration_minutes} minutos.

Para confirmar tu reserva, realiza el pago de la seña aquí:
{payment_link}

Una vez acreditado el pago, recibirás la confirmación definitiva.

¿Necesitas ayuda? Responde a este mensaje."""

    return message


def format_reservation_confirmed(
    reservation: Dict[str, Any], accommodation: Dict[str, Any]
) -> str:
    """Genera mensaje de confirmación definitiva de reserva (post-pago).

    Args:
        reservation: Datos de reserva
        accommodation: Datos del alojamiento

    Returns:
        str: Mensaje de confirmación final
    """
    check_in = reservation.get("check_in")
    check_out = reservation.get("check_out")

    if isinstance(check_in, str):
        check_in = datetime.fromisoformat(check_in.replace("Z", "+00:00")).date()
    if isinstance(check_out, str):
        check_out = datetime.fromisoformat(check_out.replace("Z", "+00:00")).date()

    check_in_str = check_in.strftime("%d/%m/%Y") if isinstance(check_in, date) else str(check_in)
    check_out_str = (
        check_out.strftime("%d/%m/%Y") if isinstance(check_out, date) else str(check_out)
    )

    message = f"""🎉 *¡Reserva Confirmada!*

Tu pago ha sido acreditado exitosamente.

📋 *Código de Reserva:* {reservation.get('code', 'N/A')}
🏠 *Alojamiento:* {accommodation.get('name', 'N/A')}
📅 *Check-in:* {check_in_str}
📅 *Check-out:* {check_out_str}

📧 Recibirás un email con los detalles completos y las instrucciones de llegada.

¡Esperamos que disfrutes tu estadía!

Para cualquier consulta, estamos a tu disposición."""

    return message


def format_error_date_overlap(
    accommodation_name: str, check_in: date, check_out: date
) -> str:
    """Mensaje de error cuando las fechas no están disponibles.

    Args:
        accommodation_name: Nombre del alojamiento
        check_in: Fecha de entrada solicitada
        check_out: Fecha de salida solicitada

    Returns:
        str: Mensaje de error amigable con sugerencia
    """
    check_in_str = check_in.strftime("%d/%m/%Y")
    check_out_str = check_out.strftime("%d/%m/%Y")

    return f"""❌ Lo siento, las fechas *{check_in_str}* a *{check_out_str}* no están disponibles para *{accommodation_name}*.

Ya existe una reserva confirmada para ese período.

¿Te gustaría:
• Ver otras fechas disponibles?
• Consultar disponibilidad de otro alojamiento?

Puedo ayudarte a encontrar la mejor opción 😊"""


def format_error_no_availability(check_in: date, check_out: date) -> str:
    """Mensaje cuando no hay disponibilidad en ningún alojamiento.

    Args:
        check_in: Fecha de entrada solicitada
        check_out: Fecha de salida solicitada

    Returns:
        str: Mensaje con sugerencia de fechas alternativas
    """
    check_in_str = check_in.strftime("%d/%m/%Y")
    check_out_str = check_out.strftime("%d/%m/%Y")

    return f"""❌ No encontré disponibilidad del *{check_in_str}* al *{check_out_str}* en ninguno de nuestros alojamientos.

¿Quieres que te sugiera fechas cercanas con disponibilidad?

También puedes consultar por fechas específicas escribiendo, por ejemplo:
"Disponibilidad del 20 al 25 de diciembre" """


def format_error_invalid_dates(reason: Optional[str] = None) -> str:
    """Mensaje cuando las fechas ingresadas son inválidas.

    Args:
        reason: Razón específica del error (opcional)

    Returns:
        str: Mensaje explicando el problema con ejemplo
    """
    base_message = """❌ Las fechas que indicaste no son válidas."""

    if reason:
        base_message += f"\n\n{reason}"

    base_message += """

Por favor, intenta nuevamente con este formato:
• "Del 15 al 20 de diciembre"
• "Disponibilidad para el fin de semana"
• "Quiero reservar del 01/12 al 05/12" """

    return base_message


def format_error_capacity_exceeded(
    accommodation_name: str, max_capacity: int, requested: int
) -> str:
    """Mensaje cuando se excede la capacidad del alojamiento.

    Args:
        accommodation_name: Nombre del alojamiento
        max_capacity: Capacidad máxima
        requested: Cantidad de huéspedes solicitada

    Returns:
        str: Mensaje explicando la limitación
    """
    return f"""❌ El alojamiento *{accommodation_name}* tiene capacidad para *{max_capacity} personas* y solicitaste para *{requested}*.

¿Te gustaría:
• Ver alojamientos con mayor capacidad?
• Reservar múltiples alojamientos?

Puedo ayudarte a encontrar la mejor combinación 😊"""


def format_error_generic(error_context: Optional[str] = None) -> str:
    """Mensaje genérico de error cuando no hay categoría específica.

    Args:
        error_context: Contexto adicional del error (opcional)

    Returns:
        str: Mensaje genérico amigable
    """
    message = """😕 Ups, hubo un problema procesando tu solicitud.

¿Podrías reformular tu mensaje?"""

    if error_context:
        message += f"\n\n{error_context}"

    message += """

Si el problema persiste, puedes contactar directamente a soporte."""

    return message


def format_availability_response(
    accommodation: Dict[str, Any], check_in: date, check_out: date, price: Decimal
) -> str:
    """Mensaje mostrando disponibilidad de un alojamiento.

    Args:
        accommodation: Datos del alojamiento
        check_in: Fecha de entrada
        check_out: Fecha de salida
        price: Precio calculado para el período

    Returns:
        str: Mensaje con detalles de disponibilidad
    """
    check_in_str = check_in.strftime("%d/%m/%Y")
    check_out_str = check_out.strftime("%d/%m/%Y")
    nights = (check_out - check_in).days

    return f"""✅ *{accommodation.get('name', 'Alojamiento')}* está disponible

📅 Del {check_in_str} al {check_out_str} ({nights} noches)
👥 Capacidad: hasta {accommodation.get('capacity', 'N/A')} personas
💰 Precio total: ${float(price):.2f}

¿Quieres reservar este alojamiento?
Responde "sí" o "reservar" para continuar.

También puedes consultar por otros alojamientos o fechas 😊"""


def format_payment_reminder(
    reservation_code: str, payment_link: str, minutes_remaining: int
) -> str:
    """Mensaje de recordatorio de pago pendiente.

    Args:
        reservation_code: Código de la reserva
        payment_link: URL de pago
        minutes_remaining: Minutos restantes antes de expiración

    Returns:
        str: Mensaje de recordatorio
    """
    return f"""⏰ *Recordatorio de Pago*

Tu pre-reserva *{reservation_code}* expira en *{minutes_remaining} minutos*.

Para confirmar tu reserva, completa el pago de la seña aquí:
{payment_link}

¿Necesitas más tiempo? Contáctanos."""


def format_reservation_expired(reservation_code: str) -> str:
    """Mensaje cuando una pre-reserva ha expirado.

    Args:
        reservation_code: Código de la reserva expirada

    Returns:
        str: Mensaje informando la expiración
    """
    return f"""⏱️ Tu pre-reserva *{reservation_code}* ha expirado por falta de pago.

Las fechas han quedado liberadas nuevamente.

¿Quieres volver a reservar? Puedo ayudarte a verificar disponibilidad 😊"""
