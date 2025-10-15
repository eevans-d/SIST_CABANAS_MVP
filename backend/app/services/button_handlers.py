"""Button Callback Handlers."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional

from app.models import Accommodation, Reservation
from app.services import whatsapp
from app.services.conversation_state import (
    delete_user_context,
    get_user_context,
    set_user_context,
    update_user_context,
)
from app.services.interactive_buttons import (
    build_accommodations_list,
    build_confirmation_buttons,
    build_date_ranges_list,
    build_guests_selection_buttons,
    build_help_topics_list,
    build_my_reservations_actions,
    format_availability_prompt_with_dates,
    format_payment_link_with_buttons,
    format_prereservation_with_buttons,
    format_welcome_with_menu,
)
from app.services.reservations import ReservationService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


async def handle_button_callback(
    button_id: str,
    user_phone: str,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Procesa callback de botón interactivo y ejecuta acción.

    Args:
        button_id: ID del botón presionado
        user_phone: Teléfono del usuario (WhatsApp)
        db: Sesión de base de datos

    Returns:
        Dict con resultado: {"action": "...", ...}
    """
    # 🔄 Cargar contexto de conversación
    context = await get_user_context(user_phone) or {}

    # Actualizar último activity
    await update_user_context(user_phone, {"last_button": button_id}, reset_ttl=True)

    try:
        # ===== Menú Principal =====
        if button_id == "menu_availability":
            result = await _handle_menu_availability(user_phone)
            # Actualizar contexto: usuario quiere ver disponibilidad
            await update_user_context(user_phone, {"current_step": "availability_flow"})
            return result

        elif button_id == "menu_reservations":
            result = await _handle_menu_reservations(user_phone, db)
            await update_user_context(user_phone, {"current_step": "my_reservations"})
            return result

        elif button_id == "menu_help":
            result = await _handle_menu_help(user_phone)
            await update_user_context(user_phone, {"current_step": "help_menu"})
            return result

        elif button_id == "menu_back":
            # Reset a menú principal
            await update_user_context(user_phone, {"current_step": "main_menu"})
            return await _handle_menu_back(user_phone)

        # ===== Selección de Fechas =====
        elif button_id == "date_this_weekend":
            result = await _handle_date_selection(user_phone, db, "this_weekend")
            # Guardar fechas seleccionadas en contexto
            if result.get("action") == "show_accommodations" and "dates" in result:
                await update_user_context(
                    user_phone,
                    {"selected_dates": result["dates"], "current_step": "selecting_accommodation"},
                )
            return result

        elif button_id == "date_next_weekend":
            result = await _handle_date_selection(user_phone, db, "next_weekend")
            if result.get("action") == "show_accommodations" and "dates" in result:
                await update_user_context(
                    user_phone,
                    {"selected_dates": result["dates"], "current_step": "selecting_accommodation"},
                )
            return result

        elif button_id == "date_custom":
            result = await _handle_date_custom(user_phone)
            await update_user_context(user_phone, {"current_step": "awaiting_custom_dates"})
            return result

        elif button_id.startswith("date_range_"):
            # Format: date_range_2025-10-20_2025-10-22
            parts = button_id.split("_", 2)
            if len(parts) == 3:
                date_str = parts[2]
                dates = date_str.split("_")
                if len(dates) == 2:
                    result = await _handle_date_range_selected(user_phone, db, dates[0], dates[1])
                    # Guardar fechas seleccionadas
                    if result.get("action") == "show_accommodations" and "dates" in result:
                        await update_user_context(
                            user_phone,
                            {
                                "selected_dates": result["dates"],
                                "current_step": "selecting_accommodation",
                            },
                        )
                    return result
            return {"action": "error", "error": "invalid_date_format"}

        # ===== Alojamientos (con contexto de fechas) =====
        elif button_id.startswith("acc_"):
            accommodation_id = int(button_id.replace("acc_", ""))
            result = await _handle_accommodation_selected(user_phone, db, accommodation_id)
            # Guardar alojamiento seleccionado
            await update_user_context(
                user_phone,
                {"accommodation_id": accommodation_id, "current_step": "confirming_reservation"},
            )
            return result

        # ===== Confirmación Pre-Reserva =====
        elif button_id.startswith("confirm_res_"):
            reservation_code = button_id.replace("confirm_res_", "")
            result = await _handle_confirm_reservation(user_phone, db, reservation_code)
            # Reset contexto después de confirmación
            if result.get("action") == "reservation_confirmed":
                await update_user_context(user_phone, {"current_step": "main_menu"})
            return result

        # ===== Resto de handlers (sin cambios por ahora) =====
        elif button_id.startswith("change_dates_"):
            reservation_code = button_id.replace("change_dates_", "")
            return await _handle_change_dates(user_phone, db, reservation_code)

        elif button_id == "see_other_acc":
            return await _handle_see_other_accommodations(user_phone, db)

        # ===== Acciones de Pago =====
        elif button_id.startswith("pay_now_"):
            reservation_code = button_id.replace("pay_now_", "")
            return await _handle_pay_now(user_phone, db, reservation_code)

        elif button_id.startswith("consult_payment_"):
            reservation_code = button_id.replace("consult_payment_", "")
            return await _handle_consult_payment(user_phone, db, reservation_code)

        elif button_id.startswith("change_payment_"):
            reservation_code = button_id.replace("change_payment_", "")
            return await _handle_change_payment(user_phone, db, reservation_code)

        # ===== Mis Reservas =====
        elif button_id.startswith("pay_res_"):
            reservation_code = button_id.replace("pay_res_", "")
            return await _handle_pay_reservation(user_phone, db, reservation_code)

        elif button_id.startswith("cancel_res_"):
            reservation_code = button_id.replace("cancel_res_", "")
            return await _handle_cancel_reservation(user_phone, db, reservation_code)

        elif button_id.startswith("view_details_"):
            reservation_code = button_id.replace("view_details_", "")
            return await _handle_view_details(user_phone, db, reservation_code)

        # ===== Ayuda =====
        elif button_id.startswith("help_"):
            topic = button_id.replace("help_", "")
            return await _handle_help_topic(user_phone, topic)

        # ===== Selección de Huéspedes =====
        elif button_id.startswith("guests_"):
            guests_str = button_id.replace("guests_", "")
            if guests_str == "other":
                return await _handle_guests_other(user_phone)
            else:
                try:
                    guests = int(guests_str)
                    # Guardar huéspedes en contexto
                    await update_user_context(user_phone, {"guests_count": guests})
                    return {"action": "guests_selected", "guests": guests}
                except ValueError:
                    return {"action": "error", "error": "invalid_guests"}

        # ===== Reservar de Nuevo =====
        elif button_id == "reserve_again":
            # Reset contexto y volver a disponibilidad
            await update_user_context(user_phone, {"current_step": "availability_flow"})
            return await _handle_menu_availability(user_phone)

        # ===== Botón Desconocido =====
        else:
            return {"action": "unknown_button", "button_id": button_id}

    except Exception as e:
        # Log error pero no fallar completamente
        import structlog

        logger = structlog.get_logger()
        logger.error(
            "button_callback_error", button_id=button_id, user_phone=user_phone, error=str(e)
        )
        return {"action": "error", "error": "processing_error"}


# ========== Handlers Internos ==========


async def _handle_menu_availability(user_phone: str) -> Dict[str, Any]:
    """Mostrar opciones de disponibilidad."""
    message, buttons = format_availability_prompt_with_dates()
    await whatsapp.send_interactive_buttons(to_phone=user_phone, body_text=message, buttons=buttons)
    return {"action": "menu_availability_shown"}


async def _handle_menu_reservations(user_phone: str, db: AsyncSession) -> Dict[str, Any]:
    """Mostrar reservas del usuario."""
    query = await db.execute(
        select(Reservation)
        .where(Reservation.guest_phone == user_phone)
        .order_by(Reservation.created_at.desc())
        .limit(5)
    )
    reservations = query.scalars().all()

    if not reservations:
        await whatsapp.send_text_message(
            user_phone, "No tenés reservas activas.\n\n¿Querés consultar disponibilidad? 🗓️"
        )
        return {"action": "no_reservations"}

    # Mostrar lista de reservas con estado
    message = "📋 Tus Reservas:\n\n"
    for res in reservations:
        status_emoji = {
            "pre_reserved": "⏳",
            "confirmed": "✅",
            "expired": "⏰",
            "cancelled": "❌",
        }.get(res.reservation_status, "❓")

        message += (
            f"{status_emoji} {res.code}\n"
            f"   {res.check_in.strftime('%d/%m')} - {res.check_out.strftime('%d/%m')}\n"
            f"   ${res.total_price:,.0f}".replace(",", ".") + "\n\n"
        )

    message += "Seleccioná una reserva para ver detalles:"

    # Crear botones con las primeras 3 reservas
    buttons = []
    for res in reservations[:3]:
        buttons.append({"id": f"view_details_{res.code}", "title": f"{res.code[:8]}"})

    await whatsapp.send_interactive_buttons(to_phone=user_phone, body_text=message, buttons=buttons)

    return {"action": "reservations_shown", "count": len(reservations)}


async def _handle_menu_help(user_phone: str) -> Dict[str, Any]:
    """Mostrar menú de ayuda."""
    sections = build_help_topics_list()
    await whatsapp.send_interactive_list(
        to_phone=user_phone,
        body_text="🆘 ¿En qué puedo ayudarte?",
        button_text="Ver temas",
        sections=sections,
    )
    return {"action": "help_shown"}


async def _handle_menu_back(user_phone: str) -> Dict[str, Any]:
    """Volver al menú principal."""
    message, buttons = format_welcome_with_menu()
    await whatsapp.send_interactive_buttons(to_phone=user_phone, body_text=message, buttons=buttons)
    return {"action": "main_menu_shown"}


async def _handle_date_selection(user_phone: str, db: AsyncSession, preset: str) -> Dict[str, Any]:
    """Manejar selección de fecha predefinida."""
    today = date.today()

    if preset == "this_weekend":
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            check_in = today
        else:
            check_in = today + timedelta(days=days_until_saturday)
        check_out = check_in + timedelta(days=2)
    elif preset == "next_weekend":
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            this_sat = today
        else:
            this_sat = today + timedelta(days=days_until_saturday)
        check_in = this_sat + timedelta(days=7)
        check_out = check_in + timedelta(days=2)
    else:
        return {"action": "error", "error": "unknown_preset"}

    # Buscar alojamientos disponibles
    return await _show_available_accommodations(user_phone, db, check_in, check_out)


async def _handle_date_custom(user_phone: str) -> Dict[str, Any]:
    """Solicitar fechas personalizadas."""
    await whatsapp.send_text_message(
        user_phone,
        "✏️ Escribí las fechas que preferís.\n\n"
        "Ejemplo:\n"
        "• Del 20 al 22 de octubre\n"
        "• 20/10 al 22/10\n"
        "• Próximo finde largo",
    )
    return {"action": "custom_dates_requested"}


async def _handle_date_range_selected(
    user_phone: str, db: AsyncSession, check_in_str: str, check_out_str: str
) -> Dict[str, Any]:
    """Manejar rango de fechas seleccionado de lista."""
    try:
        check_in = date.fromisoformat(check_in_str)
        check_out = date.fromisoformat(check_out_str)
    except ValueError:
        return {"action": "error", "error": "invalid_date_format"}

    return await _show_available_accommodations(user_phone, db, check_in, check_out)


async def _show_available_accommodations(
    user_phone: str, db: AsyncSession, check_in: date, check_out: date
) -> Dict[str, Any]:
    """Mostrar alojamientos disponibles para las fechas."""
    # Obtener todos los alojamientos activos
    query = await db.execute(select(Accommodation).where(Accommodation.active.is_(True)))
    accommodations = query.scalars().all()

    if not accommodations:
        await whatsapp.send_text_message(
            user_phone, "😞 Lo sentimos, no hay alojamientos disponibles en este momento."
        )
        return {"action": "no_accommodations"}

    # Convertir a dict para build_accommodations_list
    acc_list = [
        {
            "id": acc.id,
            "name": acc.name,
            "base_price": str(acc.base_price),
            "capacity": acc.capacity,
        }
        for acc in accommodations
    ]

    sections = build_accommodations_list(acc_list, check_in, check_out)

    await whatsapp.send_interactive_list(
        to_phone=user_phone,
        body_text=f"🏠 Alojamientos disponibles para:\n📅 {check_in.strftime('%d/%m')} - {check_out.strftime('%d/%m')}",
        button_text="Ver opciones",
        sections=sections,
        header_text="Disponibilidad",
    )

    # Guardar contexto en sesión (simplificado: guardar en metadata del próximo mensaje)
    # En producción: usar Redis para sesiones

    return {
        "action": "accommodations_shown",
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "count": len(accommodations),
    }


async def _handle_confirm_reservation(
    user_phone: str, db: AsyncSession, reservation_code: str
) -> Dict[str, Any]:
    """Confirmar y proceder a pago."""
    # Buscar reserva
    query = await db.execute(
        select(Reservation)
        .where(Reservation.code == reservation_code)
        .where(Reservation.guest_phone == user_phone)
    )
    reservation = query.scalar_one_or_none()

    if not reservation:
        await whatsapp.send_text_message(user_phone, "❌ No encontré esa reserva.")
        return {"action": "reservation_not_found"}

    if reservation.reservation_status != "pre_reserved":
        await whatsapp.send_text_message(
            user_phone, f"Esta reserva ya está {reservation.reservation_status}."
        )
        return {"action": "invalid_status", "status": reservation.reservation_status}

    # Generar link de pago (simplificado)
    payment_link = f"https://mpago.la/{reservation_code}"
    amount = reservation.deposit_amount or reservation.total_price

    header, body, buttons = format_payment_link_with_buttons(
        guest_name=reservation.guest_name,
        reservation_code=reservation_code,
        payment_link=payment_link,
        amount=amount,
    )

    await whatsapp.send_interactive_buttons(
        to_phone=user_phone, body_text=body, buttons=buttons, header_text=header
    )

    return {"action": "payment_link_sent", "reservation_code": reservation_code}


async def _handle_change_dates(
    user_phone: str, db: AsyncSession, reservation_code: str
) -> Dict[str, Any]:
    """Cambiar fechas de reserva."""
    await whatsapp.send_text_message(
        user_phone,
        "📅 Para cambiar las fechas, escribí las nuevas fechas que preferís.\n\n"
        "Ejemplo: Del 25 al 27 de octubre",
    )
    return {"action": "change_dates_requested", "reservation_code": reservation_code}


async def _handle_see_other_accommodations(user_phone: str, db: AsyncSession) -> Dict[str, Any]:
    """Ver otros alojamientos."""
    # Mostrar opciones de fecha de nuevo
    message, buttons = format_availability_prompt_with_dates()
    await whatsapp.send_interactive_buttons(to_phone=user_phone, body_text=message, buttons=buttons)
    return {"action": "see_other_accommodations"}


async def _handle_pay_now(
    user_phone: str, db: AsyncSession, reservation_code: str
) -> Dict[str, Any]:
    """Reenviar link de pago."""
    query = await db.execute(
        select(Reservation)
        .where(Reservation.code == reservation_code)
        .where(Reservation.guest_phone == user_phone)
    )
    reservation = query.scalar_one_or_none()

    if not reservation:
        await whatsapp.send_text_message(user_phone, "❌ No encontré esa reserva.")
        return {"action": "reservation_not_found"}

    payment_link = f"https://mpago.la/{reservation_code}"
    await whatsapp.send_text_message(
        user_phone,
        f"💳 Link de pago:\n{payment_link}\n\n"
        f"Tocá el link para completar el pago de forma segura.",
    )
    return {"action": "payment_link_resent"}


async def _handle_consult_payment(
    user_phone: str, db: AsyncSession, reservation_code: str
) -> Dict[str, Any]:
    """Consultar sobre el pago."""
    await whatsapp.send_text_message(
        user_phone,
        "💬 ¿Tenés alguna duda sobre el pago?\n\n" "Escribí tu consulta y te respondo enseguida.",
    )
    return {"action": "payment_consultation_requested"}


async def _handle_change_payment(
    user_phone: str, db: AsyncSession, reservation_code: str
) -> Dict[str, Any]:
    """Cambiar método de pago."""
    await whatsapp.send_text_message(
        user_phone,
        "Por el momento solo aceptamos pagos con Mercado Pago.\n\n"
        "Si tenés problemas, escribime y te ayudo. 🤝",
    )
    return {"action": "change_payment_not_available"}


async def _handle_pay_reservation(
    user_phone: str, db: AsyncSession, reservation_code: str
) -> Dict[str, Any]:
    """Pagar reserva desde lista."""
    return await _handle_pay_now(user_phone, db, reservation_code)


async def _handle_cancel_reservation(
    user_phone: str, db: AsyncSession, reservation_code: str
) -> Dict[str, Any]:
    """Cancelar reserva."""
    query = await db.execute(
        select(Reservation)
        .where(Reservation.code == reservation_code)
        .where(Reservation.guest_phone == user_phone)
    )
    reservation = query.scalar_one_or_none()

    if not reservation:
        await whatsapp.send_text_message(user_phone, "❌ No encontré esa reserva.")
        return {"action": "reservation_not_found"}

    # Confirmar cancelación
    buttons = [
        {"id": f"cancel_confirm_{reservation_code}", "title": "✅ Sí, cancelar"},
        {"id": "cancel_abort", "title": "❌ No, conservar"},
        {"id": "menu_back", "title": "🔙 Volver"},
    ]

    await whatsapp.send_interactive_buttons(
        to_phone=user_phone,
        body_text=f"¿Confirmas que querés cancelar la reserva {reservation_code}?\n\n"
        f"⚠️ Esta acción no se puede deshacer.",
        buttons=buttons,
    )

    return {"action": "cancel_confirmation_requested"}


async def _handle_view_details(
    user_phone: str, db: AsyncSession, reservation_code: str
) -> Dict[str, Any]:
    """Ver detalles de reserva."""
    # O5: joinedload para eliminar query separada de accommodation
    query = await db.execute(
        select(Reservation)
        .options(joinedload(Reservation.accommodation))
        .where(Reservation.code == reservation_code)
        .where(Reservation.guest_phone == user_phone)
    )
    reservation = query.scalar_one_or_none()

    if not reservation:
        await whatsapp.send_text_message(user_phone, "❌ No encontré esa reserva.")
        return {"action": "reservation_not_found"}

    # Acceder directamente a relationship (ya cargado con joinedload)
    accommodation = reservation.accommodation
    acc_name = accommodation.name if accommodation else "Alojamiento"

    nights = (reservation.check_out - reservation.check_in).days
    status_text = {
        "pre_reserved": "⏳ Pre-reserva (pendiente de pago)",
        "confirmed": "✅ Confirmada",
        "expired": "⏰ Expirada",
        "cancelled": "❌ Cancelada",
    }.get(reservation.reservation_status, reservation.reservation_status)

    message = (
        f"📋 Detalles de Reserva {reservation.code}\n\n"
        f"🏠 {acc_name}\n"
        f"📅 {reservation.check_in.strftime('%d/%m/%Y')} - {reservation.check_out.strftime('%d/%m/%Y')}\n"
        f"🌙 {nights} {'noche' if nights == 1 else 'noches'}\n"
        f"👥 {reservation.guests_count} {'huésped' if reservation.guests_count == 1 else 'huéspedes'}\n"
        f"💰 Total: ${reservation.total_price:,.0f}".replace(",", ".") + "\n"
        f"📊 Estado: {status_text}\n"
    )

    # Botones contextuales
    buttons = build_my_reservations_actions(reservation_code, reservation.reservation_status)

    await whatsapp.send_interactive_buttons(to_phone=user_phone, body_text=message, buttons=buttons)

    return {"action": "details_shown", "reservation_code": reservation_code}


async def _handle_accommodation_selected(
    user_phone: str, db: AsyncSession, accommodation_id: int
) -> Dict[str, Any]:
    """Alojamiento seleccionado de lista."""
    # En producción: recuperar check_in/check_out de sesión Redis
    # Por ahora: solicitar número de huéspedes

    query = await db.execute(select(Accommodation).where(Accommodation.id == accommodation_id))
    accommodation = query.scalar_one_or_none()

    if not accommodation:
        await whatsapp.send_text_message(user_phone, "❌ Alojamiento no encontrado.")
        return {"action": "accommodation_not_found"}

    message = (
        f"✅ Seleccionaste: {accommodation.name}\n\n"
        f"👥 ¿Cuántos huéspedes serán?\n"
        f"(Capacidad máxima: {accommodation.capacity})"
    )

    buttons = [
        {"id": "guests_2", "title": "👥 2 personas"},
        {"id": "guests_4", "title": "👨‍👩‍👧‍👦 4 personas"},
        {"id": "guests_other", "title": "✏️ Otro número"},
    ]

    await whatsapp.send_interactive_buttons(to_phone=user_phone, body_text=message, buttons=buttons)

    return {"action": "accommodation_selected", "accommodation_id": accommodation_id}


async def _handle_help_topic(user_phone: str, topic: str) -> Dict[str, Any]:
    """Responder a tema de ayuda."""
    responses = {
        "how_to_reserve": (
            "📝 Cómo Reservar:\n\n"
            "1️⃣ Consultá disponibilidad\n"
            "2️⃣ Elegí fechas y alojamiento\n"
            "3️⃣ Confirmá datos\n"
            "4️⃣ Pagá con Mercado Pago\n"
            "5️⃣ ¡Listo! Recibís confirmación\n\n"
            "¿Querés empezar? 🏠"
        ),
        "payment_methods": (
            "💳 Métodos de Pago:\n\n"
            "• Tarjetas de crédito\n"
            "• Tarjetas de débito\n"
            "• Mercado Pago\n\n"
            "🔒 Pagos 100% seguros"
        ),
        "cancellation": (
            "🔄 Políticas de Cancelación:\n\n"
            "• Cancelación gratuita hasta 48hs antes\n"
            "• Menos de 48hs: reembolso del 50%\n"
            "• No-show: sin reembolso\n\n"
            "Para cancelar, escribí: cancelar [código]"
        ),
        "check_in": (
            "🏠 Check-in y Check-out:\n\n"
            "• Check-in: 14:00 hs\n"
            "• Check-out: 10:00 hs\n\n"
            "Te enviaremos las instrucciones de acceso por WhatsApp."
        ),
        "amenities": (
            "✨ Servicios Incluidos:\n\n"
            "• WiFi gratis\n"
            "• Cocina equipada\n"
            "• Estacionamiento\n"
            "• Ropa de cama\n"
            "• Toallas\n\n"
            "Cada alojamiento puede tener servicios adicionales."
        ),
        "contact": (
            "📞 Contacto Directo:\n\n"
            "WhatsApp: Este número\n"
            "Email: info@alojamientos.com\n"
            "Horario: 9:00 - 21:00 hs\n\n"
            "¡Estamos para ayudarte! 🤝"
        ),
    }

    response = responses.get(topic, "Información no disponible.")

    await whatsapp.send_text_message(user_phone, response)

    # Ofrecer volver al menú
    buttons = [{"id": "menu_back", "title": "🔙 Menú principal"}]
    await whatsapp.send_interactive_buttons(
        to_phone=user_phone, body_text="¿Necesitás algo más?", buttons=buttons
    )

    return {"action": "help_topic_shown", "topic": topic}


async def _handle_guests_other(user_phone: str) -> Dict[str, Any]:
    """Solicitar número de huéspedes personalizado."""
    await whatsapp.send_text_message(
        user_phone, "✏️ ¿Cuántos huéspedes serán?\n\n" "Escribí el número:"
    )
    return {"action": "guests_custom_requested"}
