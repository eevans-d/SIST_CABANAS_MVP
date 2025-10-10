"""Tests para mensajes de WhatsApp estructurados y amigables.

Valida:
- Mensajes de confirmación tienen todos los detalles
- Mensajes de error son amigables (no técnicos)
- Formato correcto con emojis y markdown
- Sugerencias útiles en errores
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.services.messages import (
    format_prereservation_confirmation,
    format_reservation_confirmed,
    format_error_date_overlap,
    format_error_no_availability,
    format_error_invalid_dates,
    format_error_capacity_exceeded,
    format_error_generic,
    format_availability_response,
    format_payment_reminder,
    format_reservation_expired,
)


def test_prereservation_confirmation_has_all_details():
    """Mensaje de confirmación debe incluir todos los detalles críticos."""
    reservation = {
        "code": "PRE-TEST-001",
        "check_in": date(2025, 12, 15),
        "check_out": date(2025, 12, 20),
        "guests_count": 4,
        "total_price": Decimal("1500.00"),
        "deposit_amount": Decimal("450.00"),
    }
    accommodation = {"name": "Cabaña del Bosque"}
    payment_link = "https://mpago.la/test123"

    message = format_prereservation_confirmation(
        reservation=reservation,
        accommodation=accommodation,
        payment_link=payment_link,
        expiration_minutes=60,
    )

    # Verificar que incluye todos los elementos críticos
    assert "PRE-TEST-001" in message  # Código
    assert "Cabaña del Bosque" in message  # Nombre alojamiento
    assert "15/12/2025" in message  # Check-in
    assert "20/12/2025" in message  # Check-out
    assert "4" in message  # Huéspedes
    assert "$1500.00" in message  # Total
    assert "$450.00" in message  # Seña
    assert "60 minutos" in message  # Expiración
    assert payment_link in message  # Link de pago

    # Verificar que tiene formato amigable
    assert "✅" in message  # Emoji
    assert "*Pre-reserva Confirmada*" in message  # Markdown bold


def test_reservation_confirmed_message_structure():
    """Mensaje de confirmación definitiva debe ser celebratorio y claro."""
    reservation = {
        "code": "RES-CONF-001",
        "check_in": date(2025, 12, 15),
        "check_out": date(2025, 12, 20),
    }
    accommodation = {"name": "Cabaña Premium"}

    message = format_reservation_confirmed(reservation=reservation, accommodation=accommodation)

    assert "RES-CONF-001" in message
    assert "Cabaña Premium" in message
    assert "🎉" in message  # Emoji celebratorio
    assert "Confirmada" in message
    assert "pago ha sido acreditado" in message.lower()


def test_error_date_overlap_is_user_friendly():
    """Mensaje de error de fechas no disponibles debe ser amigable."""
    message = format_error_date_overlap(
        accommodation_name="Cabaña Test",
        check_in=date(2025, 12, 15),
        check_out=date(2025, 12, 20),
    )

    # NO debe contener términos técnicos
    assert "IntegrityError" not in message
    assert "database" not in message.lower()
    assert "exception" not in message.lower()
    assert "constraint" not in message.lower()

    # Debe contener información útil
    assert "15/12/2025" in message
    assert "20/12/2025" in message
    assert "Cabaña Test" in message

    # Debe sugerir alternativas
    assert "otras fechas" in message.lower() or "disponibilidad" in message.lower()


def test_error_no_availability_suggests_alternatives():
    """Mensaje sin disponibilidad debe sugerir alternativas."""
    message = format_error_no_availability(
        check_in=date(2025, 12, 25), check_out=date(2025, 12, 31)
    )

    assert "25/12/2025" in message
    assert "31/12/2025" in message
    assert "No encontré disponibilidad" in message or "no están disponibles" in message.lower()

    # Debe sugerir acción
    assert "fechas cercanas" in message.lower() or "otras fechas" in message.lower()


def test_error_invalid_dates_provides_examples():
    """Mensaje de fechas inválidas debe dar ejemplos de formato correcto."""
    message = format_error_invalid_dates()

    assert "no son válidas" in message.lower()
    # Debe incluir ejemplos
    assert "ejemplo" in message.lower() or "formato" in message.lower()
    assert "Del" in message or "del" in message  # Ejemplo de formato


def test_error_capacity_exceeded_is_helpful():
    """Mensaje de capacidad excedida debe ser útil y sugerir opciones."""
    message = format_error_capacity_exceeded(
        accommodation_name="Cabaña Pequeña", max_capacity=4, requested=6
    )

    assert "Cabaña Pequeña" in message
    assert "4" in message  # Capacidad máxima
    assert "6" in message  # Solicitado

    # Debe sugerir alternativas
    assert "mayor capacidad" in message.lower() or "múltiples" in message.lower()


def test_error_generic_is_polite():
    """Mensaje de error genérico debe ser educado y no técnico."""
    message = format_error_generic()

    assert "problema" in message.lower() or "error" in message.lower()
    assert "reformular" in message.lower() or "intenta" in message.lower()

    # No debe ser técnico
    assert "stack trace" not in message.lower()
    assert "exception" not in message.lower()


def test_availability_response_has_details_and_cta():
    """Mensaje de disponibilidad debe tener detalles y call-to-action."""
    accommodation = {"name": "Cabaña Deluxe", "capacity": 6}
    check_in = date(2025, 12, 15)
    check_out = date(2025, 12, 20)
    price = Decimal("2000.50")

    message = format_availability_response(
        accommodation=accommodation, check_in=check_in, check_out=check_out, price=price
    )

    assert "Cabaña Deluxe" in message
    assert "15/12/2025" in message
    assert "20/12/2025" in message
    assert "6" in message  # Capacidad
    assert "$2000.50" in message  # Precio
    assert "5 noches" in message  # Cantidad de noches

    # Debe tener call-to-action
    assert "reservar" in message.lower() or "sí" in message.lower()


def test_payment_reminder_is_urgent_but_polite():
    """Recordatorio de pago debe ser urgente pero educado."""
    message = format_payment_reminder(
        reservation_code="PRE-001", payment_link="https://mpago.la/test", minutes_remaining=15
    )

    assert "PRE-001" in message
    assert "15 minutos" in message
    assert "https://mpago.la/test" in message

    # Debe transmitir urgencia
    assert "expira" in message.lower() or "recordatorio" in message.lower()

    # Debe ser educado
    assert "?" in message  # Pregunta educada


def test_reservation_expired_is_empathetic():
    """Mensaje de expiración debe ser empático y ofrecer ayuda."""
    message = format_reservation_expired(reservation_code="PRE-002")

    assert "PRE-002" in message
    assert "expirado" in message.lower() or "expira" in message.lower()

    # Debe ofrecer re-reservar
    assert "volver a reservar" in message.lower() or "disponibilidad" in message.lower()


def test_messages_use_emojis_consistently():
    """Todos los mensajes deben usar emojis para mejor UX."""
    messages = [
        format_prereservation_confirmation(
            {"code": "X", "check_in": date.today(), "check_out": date.today(), "guests_count": 2, "total_price": 100, "deposit_amount": 30},
            {"name": "Test"},
            "https://test.com",
        ),
        format_reservation_confirmed(
            {"code": "X", "check_in": date.today(), "check_out": date.today()}, {"name": "Test"}
        ),
        format_error_date_overlap("Test", date.today(), date.today() + timedelta(days=1)),
        format_error_no_availability(date.today(), date.today() + timedelta(days=1)),
        format_availability_response(
            {"name": "Test", "capacity": 4}, date.today(), date.today() + timedelta(days=1), Decimal("100")
        ),
    ]

    # Todos deben tener al menos un emoji
    for msg in messages:
        # Verificar que hay algún carácter emoji (rango Unicode básico)
        assert any(ord(c) > 127 for c in msg), f"Message without emoji: {msg[:50]}"


def test_no_technical_terms_in_error_messages():
    """Mensajes de error no deben contener terminología técnica."""
    error_messages = [
        format_error_date_overlap("Test", date.today(), date.today()),
        format_error_no_availability(date.today(), date.today()),
        format_error_invalid_dates(),
        format_error_capacity_exceeded("Test", 4, 6),
        format_error_generic(),
    ]

    technical_terms = [
        "IntegrityError",
        "ValueError",
        "Exception",
        "database",
        "constraint",
        "query",
        "transaction",
        "rollback",
        "commit",
    ]

    for msg in error_messages:
        for term in technical_terms:
            assert term.lower() not in msg.lower(), f"Technical term '{term}' found in: {msg[:100]}"


def test_messages_have_clear_next_steps():
    """Mensajes deben indicar claramente qué hacer a continuación."""
    # Confirmación → pagar
    prereserv = format_prereservation_confirmation(
        {"code": "X", "check_in": date.today(), "check_out": date.today(), "guests_count": 2, "total_price": 100, "deposit_amount": 30},
        {"name": "Test"},
        "https://pay.com",
    )
    assert "pago" in prereserv.lower() or "pagar" in prereserv.lower()

    # Error → sugerir alternativa
    error = format_error_date_overlap("Test", date.today(), date.today())
    assert "?" in error  # Pregunta que invita a acción

    # Disponibilidad → reservar
    avail = format_availability_response(
        {"name": "Test", "capacity": 4}, date.today(), date.today() + timedelta(days=1), Decimal("100")
    )
    assert "reservar" in avail.lower() or "sí" in avail.lower()
