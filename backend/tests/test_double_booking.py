"""
Tests para validar el constraint anti doble-booking.

CRÍTICO: Estos tests DEBEN usar PostgreSQL real, no SQLite.
El constraint EXCLUDE USING gist con daterange solo funciona en Postgres.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models import Accommodation, Reservation
from app.models.enums import ReservationStatus


@pytest.mark.asyncio
async def test_consecutive_reservations_allowed(db_session):
    """Check-out y siguiente check-in mismo día debe ser válido.
    Skip si no es Postgres porque depende de exclusion constraint."""
    if db_session.bind.dialect.name != "postgresql":
        pytest.skip("Constraint EXCLUDE sólo soportado en PostgreSQL")

    acc = Accommodation(
        name="Cabaña Lago",
        type="cabin",
        capacity=4,
        base_price=Decimal("50000.00"),
    )
    db_session.add(acc)
    await db_session.flush()

    r1 = Reservation(
        code="RES2501100001",
        accommodation_id=acc.id,
        check_in=date(2025, 1, 10),
        check_out=date(2025, 1, 12),
        guest_name="Juan",
        guest_phone="+5491111111111",
        guests_count=2,
        nights=2,
        base_price_per_night=Decimal("50000.00"),
        total_price=Decimal("100000.00"),
        deposit_percentage=30,
        deposit_amount=Decimal("30000.00"),
        reservation_status="confirmed",
        payment_status="paid",
    )
    db_session.add(r1)
    await db_session.flush()

    r2 = Reservation(
        code="RES2501120002",
        accommodation_id=acc.id,
        check_in=date(2025, 1, 12),
        check_out=date(2025, 1, 15),
        guest_name="Ana",
        guest_phone="+5491222222222",
        guests_count=2,
        nights=3,
        base_price_per_night=Decimal("50000.00"),
        total_price=Decimal("150000.00"),
        deposit_percentage=30,
        deposit_amount=Decimal("45000.00"),
        reservation_status="confirmed",
        payment_status="paid",
    )
    db_session.add(r2)
    await db_session.commit()

    assert r2.id is not None


@pytest.mark.asyncio
async def test_overlapping_reservation_blocked(db_session):
    """Reserva solapada debe disparar IntegrityError por constraint.
    (Postgres únicamente)"""
    if db_session.bind.dialect.name != "postgresql":
        pytest.skip("Constraint EXCLUDE sólo soportado en PostgreSQL")

    acc = Accommodation(
        name="Depto Centro",
        type="apartment",
        capacity=3,
        base_price=Decimal("40000.00"),
    )
    db_session.add(acc)
    await db_session.flush()

    r1 = Reservation(
        code="RES2501200101",
        accommodation_id=acc.id,
        check_in=date(2025, 1, 20),
        check_out=date(2025, 1, 23),
        guest_name="Luis",
        guest_phone="+5491333333333",
        guests_count=2,
        nights=3,
        base_price_per_night=Decimal("40000.00"),
        total_price=Decimal("120000.00"),
        deposit_percentage=30,
        deposit_amount=Decimal("36000.00"),
        reservation_status="confirmed",
        payment_status="paid",
    )
    db_session.add(r1)
    await db_session.flush()

    r2 = Reservation(
        code="RES2501210102",
        accommodation_id=acc.id,
        check_in=date(2025, 1, 21),  # solapa 21-22
        check_out=date(2025, 1, 24),
        guest_name="María",
        guest_phone="+5491444444444",
        guests_count=2,
        nights=3,
        base_price_per_night=Decimal("40000.00"),
        total_price=Decimal("120000.00"),
        deposit_percentage=30,
        deposit_amount=Decimal("36000.00"),
        reservation_status="confirmed",
        payment_status="paid",
    )
    db_session.add(r2)

    with pytest.raises(IntegrityError):
        await db_session.commit()
        # rollback automático en fixture


@pytest.mark.asyncio
async def test_cancelled_reservation_allows_new(db_session):
    """Una reserva cancelada deja libre el rango (constraint filtra por estado)."""
    if db_session.bind.dialect.name != "postgresql":
        pytest.skip("Constraint EXCLUDE sólo soportado en PostgreSQL")

    acc = Accommodation(
        name="Casa Sierra",
        type="house",
        capacity=6,
        base_price=Decimal("70000.00"),
    )
    db_session.add(acc)
    await db_session.flush()

    r1 = Reservation(
        code="RES2501300201",
        accommodation_id=acc.id,
        check_in=date(2025, 1, 30),
        check_out=date(2025, 2, 2),
        guest_name="Pedro",
        guest_phone="+5491555555555",
        guests_count=4,
        nights=3,
        base_price_per_night=Decimal("70000.00"),
        total_price=Decimal("210000.00"),
        deposit_percentage=30,
        deposit_amount=Decimal("63000.00"),
        reservation_status="confirmed",
        payment_status="paid",
    )
    db_session.add(r1)
    await db_session.flush()

    # Cancelar y commit
    r1.reservation_status = "cancelled"
    await db_session.commit()

    r2 = Reservation(
        code="RES2501300202",
        accommodation_id=acc.id,
        check_in=date(2025, 1, 30),
        check_out=date(2025, 2, 2),
        guest_name="Lucía",
        guest_phone="+5491666666666",
        guests_count=4,
        nights=3,
        base_price_per_night=Decimal("70000.00"),
        total_price=Decimal("210000.00"),
        deposit_percentage=30,
        deposit_amount=Decimal("63000.00"),
        reservation_status="confirmed",
        payment_status="paid",
    )
    db_session.add(r2)
    await db_session.commit()

    assert r2.id is not None
