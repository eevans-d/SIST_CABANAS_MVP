"""Tests simplificados para background jobs (expiración de pre-reservas y sincronización iCal).

Estos tests verifican:
- Expiración correcta de pre-reservas vencidas
- Envío de recordatorios
- Manejo de errores básico
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from app.jobs.cleanup import expire_prereservations, send_prereservation_reminders
from app.models.enums import ReservationStatus
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_expire_prereservations_basic(
    db_session: AsyncSession, accommodation_factory, reservation_factory
):
    """Debe expirar pre-reservas vencidas."""
    # Crear alojamiento
    accommodation = await accommodation_factory()

    # Crear pre-reserva expirada
    now = datetime.now(timezone.utc)
    expired_reservation = await reservation_factory(
        accommodation=accommodation,
        code="TEST-EXPIRED-001",
        reservation_status=ReservationStatus.PRE_RESERVED.value,
        expires_at=now - timedelta(minutes=5),  # Expirada hace 5 minutos
    )

    # Ejecutar job
    expired_count = await expire_prereservations(db_session)

    # Verificar resultado
    assert expired_count == 1

    # Verificar estado actualizado
    await db_session.refresh(expired_reservation)
    assert str(expired_reservation.reservation_status) == str(ReservationStatus.CANCELLED.value)
    assert expired_reservation.cancelled_at is not None
    assert expired_reservation.internal_notes == "auto-expired"


@pytest.mark.asyncio
async def test_expire_prereservations_no_expired(
    db_session: AsyncSession, accommodation_factory, reservation_factory
):
    """No debe expirar pre-reservas que aún no vencieron."""
    # Crear alojamiento
    accommodation = await accommodation_factory()

    # Crear pre-reserva válida
    now = datetime.now(timezone.utc)
    valid_reservation = await reservation_factory(
        accommodation=accommodation,
        code="TEST-VALID-001",
        reservation_status=ReservationStatus.PRE_RESERVED.value,
        expires_at=now + timedelta(minutes=30),  # Expira en 30 minutos
    )

    # Ejecutar job
    expired_count = await expire_prereservations(db_session)

    # Verificar que no expiró
    assert expired_count == 0
    await db_session.refresh(valid_reservation)
    assert str(valid_reservation.reservation_status) == str(ReservationStatus.PRE_RESERVED.value)


@pytest.mark.asyncio
async def test_expire_prereservations_only_pre_reserved(
    db_session: AsyncSession, accommodation_factory, reservation_factory
):
    """Solo debe expirar pre-reservas, no confirmadas ni canceladas."""
    # Crear alojamiento
    accommodation = await accommodation_factory()

    now = datetime.now(timezone.utc)

    # Pre-reserva expirada (debe expirar)
    pre_reserved = await reservation_factory(
        accommodation=accommodation,
        code="TEST-PRE-001",
        reservation_status=ReservationStatus.PRE_RESERVED.value,
        expires_at=now - timedelta(minutes=5),
    )

    # Confirmada (no debe tocar)
    confirmed = await reservation_factory(
        accommodation=accommodation,
        code="TEST-CONF-001",
        reservation_status=ReservationStatus.CONFIRMED.value,
        confirmed_at=now - timedelta(hours=1),
        expires_at=None,  # Confirmadas no tienen expires_at
    )

    # Ejecutar job
    expired_count = await expire_prereservations(db_session)

    # Verificar que solo expiró la pre-reserva
    assert expired_count == 1
    await db_session.refresh(pre_reserved)
    await db_session.refresh(confirmed)
    assert str(pre_reserved.reservation_status) == str(ReservationStatus.CANCELLED.value)
    assert str(confirmed.reservation_status) == str(ReservationStatus.CONFIRMED.value)


@pytest.mark.asyncio
async def test_send_prereservation_reminders_basic(
    db_session: AsyncSession, accommodation_factory, reservation_factory
):
    """Debe enviar recordatorios para pre-reservas que expiran pronto."""
    # Crear alojamiento
    accommodation = await accommodation_factory()

    # Crear pre-reserva que expira en 10 minutos
    now = datetime.now(timezone.utc)
    reservation = await reservation_factory(
        accommodation=accommodation,
        code="TEST-REMINDER-001",
        guest_email="pedro@test.com",
        reservation_status=ReservationStatus.PRE_RESERVED.value,
        expires_at=now + timedelta(minutes=10),
    )

    # Mock email service
    with patch("app.jobs.cleanup.email_service") as mock_email:
        mock_email.render.return_value = "<html>Test</html>"
        mock_email.send_html.return_value = None

        # Ejecutar job (ventana de 15 minutos)
        reminder_count = await send_prereservation_reminders(db_session, window_minutes=15)

        # Verificar que se envió
        assert reminder_count == 1
        mock_email.send_html.assert_called_once()

        # Verificar marcado como enviado
        await db_session.refresh(reservation)
        assert "reminder_sent" in str(reservation.internal_notes or "")


@pytest.mark.asyncio
async def test_send_prereservation_reminders_no_duplicates(
    db_session: AsyncSession, accommodation_factory, reservation_factory
):
    """No debe enviar recordatorios duplicados."""
    # Crear alojamiento
    accommodation = await accommodation_factory()

    # Crear pre-reserva que ya tiene recordatorio enviado
    now = datetime.now(timezone.utc)
    await reservation_factory(
        accommodation=accommodation,
        code="TEST-REMINDER-002",
        guest_email="ana@test.com",
        reservation_status=ReservationStatus.PRE_RESERVED.value,
        expires_at=now + timedelta(minutes=10),
        internal_notes="reminder_sent",  # Ya enviado
    )

    # Mock email service
    with patch("app.jobs.cleanup.email_service") as mock_email:
        # Ejecutar job
        reminder_count = await send_prereservation_reminders(db_session, window_minutes=15)

        # Verificar que NO se envió
        assert reminder_count == 0
        mock_email.send_html.assert_not_called()


@pytest.mark.asyncio
async def test_expire_prereservations_batch_size(
    db_session: AsyncSession, accommodation_factory, reservation_factory
):
    """Debe respetar el batch_size."""
    # Crear alojamiento
    accommodation = await accommodation_factory()

    # Crear 5 pre-reservas expiradas
    now = datetime.now(timezone.utc)
    for i in range(5):
        await reservation_factory(
            accommodation=accommodation,
            code=f"TEST-BATCH-{i:03d}",
            reservation_status=ReservationStatus.PRE_RESERVED.value,
            expires_at=now - timedelta(minutes=5),
        )

    # Ejecutar con batch_size=3
    expired_count = await expire_prereservations(db_session, batch_size=3)

    # Debe procesar solo 3
    assert expired_count == 3
