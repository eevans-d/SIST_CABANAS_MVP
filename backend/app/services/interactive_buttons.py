"""Interactive Buttons & Lists Helpers para WhatsApp."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List


def build_main_menu_buttons() -> List[Dict[str, str]]:
    """Construye botones del menú principal.

    Returns:
        Lista de 3 botones para el menú inicial
    """
    return [
        {"id": "menu_availability", "title": "🗓️ Disponibilidad"},
        {"id": "menu_reservations", "title": "📋 Mis Reservas"},
        {"id": "menu_help", "title": "❓ Ayuda"},
    ]


def build_date_selection_buttons() -> List[Dict[str, str]]:
    """Construye botones para selección rápida de fechas.

    Returns:
        Lista de 3 botones con opciones de fecha comunes
    """
    today = date.today()
    next_weekend = today + timedelta(days=(5 - today.weekday()) % 7 or 7)

    return [
        {"id": "date_this_weekend", "title": "🗓️ Este finde"},
        {"id": "date_next_weekend", "title": "📅 Próximo finde"},
        {"id": "date_custom", "title": "✏️ Elegir fecha"},
    ]


def build_confirmation_buttons(action_prefix: str) -> List[Dict[str, str]]:
    """Construye botones de confirmación genéricos.

    Args:
        action_prefix: Prefijo para IDs (ej: "prereserve", "payment")

    Returns:
        Lista de 3 botones: Confirmar, Modificar, Cancelar
    """
    return [
        {"id": f"{action_prefix}_confirm", "title": "✅ Confirmar"},
        {"id": f"{action_prefix}_modify", "title": "✏️ Modificar"},
        {"id": f"{action_prefix}_cancel", "title": "❌ Cancelar"},
    ]


def build_prereservation_buttons(reservation_code: str) -> List[Dict[str, str]]:
    """Construye botones para confirmación de pre-reserva.

    Args:
        reservation_code: Código de la reserva

    Returns:
        Lista de 3 botones específicos para pre-reserva
    """
    return [
        {"id": f"confirm_res_{reservation_code}", "title": "✅ Reservar"},
        {"id": f"change_dates_{reservation_code}", "title": "📅 Cambiar fechas"},
        {"id": "see_other_acc", "title": "🏠 Ver otros"},
    ]


def build_payment_action_buttons(reservation_code: str, payment_link: str) -> List[Dict[str, str]]:
    """Construye botones para acciones de pago.

    Args:
        reservation_code: Código de la reserva
        payment_link: Link de pago de Mercado Pago

    Returns:
        Lista de 3 botones para gestionar pago

    Note:
        El botón "Pagar ahora" debe abrir el link externamente
    """
    return [
        {"id": f"pay_now_{reservation_code}", "title": "💳 Pagar ahora"},
        {"id": f"consult_payment_{reservation_code}", "title": "❓ Consultar"},
        {"id": f"change_payment_{reservation_code}", "title": "🔄 Cambiar"},
    ]


def build_accommodations_list(
    accommodations: List[Dict[str, Any]], check_in: date, check_out: date
) -> List[Dict[str, Any]]:
    """Construye lista interactiva de alojamientos disponibles.

    Args:
        accommodations: Lista de alojamientos con info
        check_in: Fecha de entrada
        check_out: Fecha de salida

    Returns:
        Dict con estructura de lista interactiva de WhatsApp

    Example:
        sections = build_accommodations_list(
            accommodations=[
                {"id": 1, "name": "Cabaña", "base_price": "15000", "capacity": 4},
                {"id": 2, "name": "Casa", "base_price": "12000", "capacity": 6}
            ],
            check_in=date(2025, 10, 20),
            check_out=date(2025, 10, 22)
        )
    """
    nights = (check_out - check_in).days

    rows = []
    for acc in accommodations[:10]:  # WhatsApp limit: 10 items
        acc_id = acc.get("id")
        name = acc.get("name", "Alojamiento")
        base_price = Decimal(str(acc.get("base_price", 0)))
        capacity = acc.get("capacity", 1)

        # Formatear precio por noche
        price_per_night = f"${base_price:,.0f}".replace(",", ".")
        total_price = f"${base_price * nights:,.0f}".replace(",", ".")

        rows.append(
            {
                "id": f"acc_{acc_id}",
                "title": name,
                "description": f"{price_per_night}/noche · {capacity} huéspedes · Total: {total_price}",
            }
        )

    return [{"title": f"Disponibles ({len(rows)} opciones)", "rows": rows}]


def build_date_ranges_list() -> List[Dict[str, Any]]:
    """Construye lista de rangos de fechas comunes.

    Returns:
        Lista de secciones con opciones de fechas predefinidas
    """
    today = date.today()

    # Este fin de semana
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:  # Ya es sábado
        this_sat = today
    else:
        this_sat = today + timedelta(days=days_until_saturday)
    this_sun = this_sat + timedelta(days=1)

    # Próximo fin de semana
    next_sat = this_sat + timedelta(days=7)
    next_sun = next_sat + timedelta(days=1)

    # Feriados largos próximos (hardcoded para ejemplo)
    rows = [
        {
            "id": f"date_range_{this_sat.isoformat()}_{this_sun.isoformat()}",
            "title": "Este fin de semana",
            "description": f"{this_sat.strftime('%d/%m')} - {this_sun.strftime('%d/%m')} (1 noche)",
        },
        {
            "id": f"date_range_{next_sat.isoformat()}_{next_sun.isoformat()}",
            "title": "Próximo fin de semana",
            "description": f"{next_sat.strftime('%d/%m')} - {next_sun.strftime('%d/%m')} (1 noche)",
        },
        {
            "id": f"date_range_{this_sat.isoformat()}_{(this_sun + timedelta(days=1)).isoformat()}",
            "title": "Este finde largo",
            "description": f"{this_sat.strftime('%d/%m')} - {(this_sun + timedelta(days=1)).strftime('%d/%m')} (2 noches)",
        },
        {
            "id": "date_custom",
            "title": "Elegir fechas manualmente",
            "description": "Escribí las fechas que preferís",
        },
    ]

    return [{"title": "Opciones de Fechas", "rows": rows}]


def build_guests_selection_buttons() -> List[Dict[str, str]]:
    """Construye botones para selección rápida de huéspedes.

    Returns:
        Lista de 3 botones con opciones comunes de huéspedes
    """
    return [
        {"id": "guests_2", "title": "👥 2 personas"},
        {"id": "guests_4", "title": "👨‍👩‍👧‍👦 4 personas"},
        {"id": "guests_other", "title": "✏️ Otro número"},
    ]


def build_help_topics_list() -> List[Dict[str, Any]]:
    """Construye lista de temas de ayuda.

    Returns:
        Lista de secciones con tópicos de ayuda
    """
    rows = [
        {
            "id": "help_how_to_reserve",
            "title": "¿Cómo reservar?",
            "description": "Pasos para hacer una reserva",
        },
        {
            "id": "help_payment_methods",
            "title": "Métodos de pago",
            "description": "Tarjetas, transferencia, etc.",
        },
        {
            "id": "help_cancellation",
            "title": "Políticas de cancelación",
            "description": "Plazos y reembolsos",
        },
        {
            "id": "help_check_in",
            "title": "Check-in y check-out",
            "description": "Horarios y procedimiento",
        },
        {
            "id": "help_amenities",
            "title": "Servicios incluidos",
            "description": "WiFi, cocina, estacionamiento...",
        },
        {"id": "help_contact", "title": "Contacto directo", "description": "Teléfono y email"},
    ]

    return [{"title": "Temas de Ayuda", "rows": rows}]


def build_my_reservations_actions(reservation_code: str, status: str) -> List[Dict[str, str]]:
    """Construye botones de acciones según estado de reserva.

    Args:
        reservation_code: Código de la reserva
        status: Estado actual (pre_reserved, confirmed, etc.)

    Returns:
        Lista de botones contextual al estado
    """
    if status == "pre_reserved":
        return [
            {"id": f"pay_res_{reservation_code}", "title": "💳 Pagar"},
            {"id": f"cancel_res_{reservation_code}", "title": "❌ Cancelar"},
            {"id": "menu_back", "title": "🔙 Volver"},
        ]
    elif status == "confirmed":
        return [
            {"id": f"view_details_{reservation_code}", "title": "📄 Ver detalles"},
            {"id": f"cancel_res_{reservation_code}", "title": "❌ Cancelar"},
            {"id": "menu_back", "title": "🔙 Volver"},
        ]
    else:  # expired, cancelled
        return [
            {"id": "reserve_again", "title": "🔄 Reservar de nuevo"},
            {"id": "menu_availability", "title": "🗓️ Ver disponibilidad"},
            {"id": "menu_back", "title": "🔙 Menú principal"},
        ]


# ========== Mensajes con Botones Integrados ==========


def format_welcome_with_menu() -> tuple[str, List[Dict[str, str]]]:
    """Mensaje de bienvenida con menú principal.

    Returns:
        Tupla (mensaje, botones)
    """
    message = (
        "👋 ¡Hola! Soy el asistente de reservas.\n\n"
        "Puedo ayudarte a:\n"
        "• Consultar disponibilidad\n"
        "• Hacer una reserva\n"
        "• Ver tus reservas activas\n\n"
        "¿Qué te gustaría hacer?"
    )
    buttons = build_main_menu_buttons()
    return message, buttons


def format_availability_prompt_with_dates() -> tuple[str, List[Dict[str, str]]]:
    """Mensaje para consultar disponibilidad con opciones de fechas.

    Returns:
        Tupla (mensaje, botones)
    """
    message = (
        "🗓️ ¿Para cuándo querés consultar disponibilidad?\n\n"
        "Elegí una opción o escribí las fechas que prefieras:"
    )
    buttons = build_date_selection_buttons()
    return message, buttons


def format_prereservation_with_buttons(
    guest_name: str,
    accommodation_name: str,
    check_in: date,
    check_out: date,
    guests: int,
    total_price: Decimal,
    reservation_code: str,
) -> tuple[str, str, List[Dict[str, str]]]:
    """Mensaje de pre-reserva con botones de confirmación.

    Args:
        guest_name: Nombre del huésped
        accommodation_name: Nombre del alojamiento
        check_in: Fecha de entrada
        check_out: Fecha de salida
        guests: Número de huéspedes
        total_price: Precio total
        reservation_code: Código de la reserva

    Returns:
        Tupla (header, body, botones)
    """
    nights = (check_out - check_in).days
    price_formatted = f"${total_price:,.0f}".replace(",", ".")

    header = f"✅ Pre-reserva #{reservation_code}"

    body = (
        f"Hola {guest_name}! 👋\n\n"
        f"Tu pre-reserva está lista:\n\n"
        f"🏠 {accommodation_name}\n"
        f"📅 {check_in.strftime('%d/%m/%Y')} - {check_out.strftime('%d/%m/%Y')}\n"
        f"🌙 {nights} {'noche' if nights == 1 else 'noches'}\n"
        f"👥 {guests} {'huésped' if guests == 1 else 'huéspedes'}\n"
        f"💰 Total: {price_formatted}\n\n"
        f"⏰ Esta reserva expira en 60 minutos.\n"
        f"¿Qué querés hacer?"
    )

    buttons = build_prereservation_buttons(reservation_code)

    return header, body, buttons


def format_payment_link_with_buttons(
    guest_name: str, reservation_code: str, payment_link: str, amount: Decimal
) -> tuple[str, str, List[Dict[str, str]]]:
    """Mensaje con link de pago y botones de acción.

    Args:
        guest_name: Nombre del huésped
        reservation_code: Código de la reserva
        payment_link: URL de Mercado Pago
        amount: Monto a pagar

    Returns:
        Tupla (header, body, botones)
    """
    amount_formatted = f"${amount:,.0f}".replace(",", ".")

    header = f"💳 Pago - Reserva #{reservation_code}"

    body = (
        f"Hola {guest_name}! 👋\n\n"
        f"Para confirmar tu reserva, completá el pago:\n\n"
        f"💰 Monto: {amount_formatted}\n"
        f"🔗 Link de pago:\n{payment_link}\n\n"
        f"Aceptamos todas las tarjetas de crédito y débito.\n"
        f"El pago es 100% seguro con Mercado Pago.\n\n"
        f"⏰ Recordá que la reserva expira en 60 minutos."
    )

    buttons = build_payment_action_buttons(reservation_code, payment_link)

    return header, body, buttons
