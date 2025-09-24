"""
Tests adicionales para validación completa del constraint anti doble-booking.
Estos tests complementan test_double_booking.py con casos más específicos.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models import Accommodation, Reservation
from app.models.enums import ReservationStatus


class TestDoubleBookingConstraintExtended:
    """Tests extendidos del constraint no_overlap_reservations."""

    @pytest.fixture
    async def sample_accommodation(self, db_session):
        """Fixture para crear un alojamiento de prueba."""
        accommodation = Accommodation(
            name="Cabaña Test Premium",
            type="cabin",
            capacity=6,
            base_price=Decimal("120000.00"),
            description="Cabaña premium para testing",
            amenities={"wifi": True, "kitchen": True, "fireplace": True},
            photos=["test_cabin_1.jpg", "test_cabin_2.jpg"],
            location={"lat": -31.4201, "lng": -64.1888, "address": "Test 123"},
            policies={"check_in": "15:00", "check_out": "11:00", "min_stay": 2},
            active=True
        )
        db_session.add(accommodation)
        await db_session.flush()
        return accommodation

    @pytest.mark.asyncio
    async def test_pre_reserved_blocks_confirmed(self, db_session, sample_accommodation):
        """PRE_RESERVED debe bloquear CONFIRMED en mismas fechas."""
        if db_session.bind.dialect.name != "postgresql":
            pytest.skip("Constraint EXCLUDE sólo soportado en PostgreSQL")

        check_in = date.today() + timedelta(days=5)
        check_out = date.today() + timedelta(days=8)

        # Reserva pre-reservada
        pre_reservation = Reservation(
            code="PRE240924001",
            accommodation_id=sample_accommodation.id,
            guest_name="Martín Silva",
            guest_phone="+5493599999999",
            guest_email="martin@example.com",
            check_in=check_in,
            check_out=check_out,
            guests_count=4,
            total_price=Decimal("360000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("108000.00"),
            reservation_status=ReservationStatus.PRE_RESERVED,
            channel_source="whatsapp"
        )
        db_session.add(pre_reservation)
        await db_session.flush()

        # Intento de confirmación en mismas fechas - DEBE FALLAR
        confirmed_reservation = Reservation(
            code="CON240924001",
            accommodation_id=sample_accommodation.id,
            guest_name="Claudia Morales",
            guest_phone="+5493500000000",
            guest_email="claudia@example.com",
            check_in=check_in,
            check_out=check_out,
            guests_count=2,
            total_price=Decimal("360000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("108000.00"),
            reservation_status=ReservationStatus.CONFIRMED,
            channel_source="email"
        )
        db_session.add(confirmed_reservation)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ["no_overlap_reservations", "overlaps", "exclude"])

    @pytest.mark.asyncio
    async def test_partial_overlap_scenarios(self, db_session, sample_accommodation):
        """Test diferentes tipos de solapamiento parcial."""
        if db_session.bind.dialect.name != "postgresql":
            pytest.skip("Constraint EXCLUDE sólo soportado en PostgreSQL")

        base_date = date.today() + timedelta(days=10)
        
        # Reserva base: días 10-15
        base_reservation = Reservation(
            code="BASE240924001",
            accommodation_id=sample_accommodation.id,
            guest_name="Usuario Base",
            guest_phone="+5493511111111",
            guest_email="base@example.com",
            check_in=base_date,
            check_out=base_date + timedelta(days=5),
            guests_count=3,
            total_price=Decimal("600000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("180000.00"),
            reservation_status=ReservationStatus.CONFIRMED,
            channel_source="whatsapp"
        )
        db_session.add(base_reservation)
        await db_session.flush()

        # Test 1: Solapamiento por la izquierda (8-12 vs 10-15)
        left_overlap = Reservation(
            code="LEFT240924001",
            accommodation_id=sample_accommodation.id,
            guest_name="Left Overlap",
            guest_phone="+5493522222222",
            guest_email="left@example.com",
            check_in=base_date - timedelta(days=2),
            check_out=base_date + timedelta(days=2),
            guests_count=2,
            total_price=Decimal("480000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("144000.00"),
            reservation_status=ReservationStatus.CONFIRMED,
            channel_source="email"
        )
        db_session.add(left_overlap)

        with pytest.raises(IntegrityError):
            await db_session.commit()
        
        # Rollback automático, continúa con el siguiente test
        await db_session.rollback()

        # Test 2: Solapamiento por la derecha (13-18 vs 10-15)
        right_overlap = Reservation(
            code="RIGHT240924001",
            accommodation_id=sample_accommodation.id,
            guest_name="Right Overlap",
            guest_phone="+5493533333333",
            guest_email="right@example.com",
            check_in=base_date + timedelta(days=3),
            check_out=base_date + timedelta(days=8),
            guests_count=4,
            total_price=Decimal("600000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("180000.00"),
            reservation_status=ReservationStatus.PRE_RESERVED,
            channel_source="whatsapp"
        )
        db_session.add(right_overlap)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_different_accommodations_same_dates_allowed(self, db_session):
        """Mismas fechas en diferentes alojamientos debe ser permitido."""
        if db_session.bind.dialect.name != "postgresql":
            pytest.skip("Constraint EXCLUDE sólo soportado en PostgreSQL")

        # Crear dos alojamientos
        acc1 = Accommodation(
            name="Cabaña Norte",
            type="cabin",
            capacity=4,
            base_price=Decimal("100000.00"),
            description="Cabaña en zona norte",
            amenities={"wifi": True, "grill": True},
            photos=["north_cabin.jpg"],
            location={"lat": -31.4201, "lng": -64.1888},
            policies={"check_in": "15:00", "check_out": "11:00"},
            active=True
        )
        
        acc2 = Accommodation(
            name="Cabaña Sur",
            type="cabin",
            capacity=4,
            base_price=Decimal("100000.00"),
            description="Cabaña en zona sur",
            amenities={"wifi": True, "pool": True},
            photos=["south_cabin.jpg"],
            location={"lat": -31.4301, "lng": -64.1988},
            policies={"check_in": "15:00", "check_out": "11:00"},
            active=True
        )
        
        db_session.add_all([acc1, acc2])
        await db_session.flush()

        check_in = date.today() + timedelta(days=7)
        check_out = date.today() + timedelta(days=10)

        # Reserva en alojamiento 1
        reservation1 = Reservation(
            code="DIFF240924001",
            accommodation_id=acc1.id,
            guest_name="Cliente Norte",
            guest_phone="+5493544444444",
            guest_email="norte@example.com",
            check_in=check_in,
            check_out=check_out,
            guests_count=4,
            total_price=Decimal("300000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("90000.00"),
            reservation_status=ReservationStatus.CONFIRMED,
            channel_source="whatsapp"
        )
        
        # Reserva en alojamiento 2 - mismas fechas
        reservation2 = Reservation(
            code="DIFF240924002",
            accommodation_id=acc2.id,
            guest_name="Cliente Sur",
            guest_phone="+5493555555555",
            guest_email="sur@example.com",
            check_in=check_in,
            check_out=check_out,
            guests_count=3,
            total_price=Decimal("300000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("90000.00"),
            reservation_status=ReservationStatus.CONFIRMED,
            channel_source="email"
        )
        
        db_session.add_all([reservation1, reservation2])
        
        # Debe ser exitoso - diferentes alojamientos
        await db_session.commit()
        
        # Verificar que ambas reservas existen
        result = await db_session.execute(select(Reservation))
        reservations = result.scalars().all()
        assert len(reservations) >= 2

    @pytest.mark.asyncio
    async def test_cancelled_allows_same_dates(self, db_session, sample_accommodation):
        """Reserva cancelada permite nueva reserva en mismas fechas."""
        if db_session.bind.dialect.name != "postgresql":
            pytest.skip("Constraint EXCLUDE sólo soportado en PostgreSQL")

        check_in = date.today() + timedelta(days=12)
        check_out = date.today() + timedelta(days=15)

        # Reserva inicial que será cancelada
        original_reservation = Reservation(
            code="CANC240924001",
            accommodation_id=sample_accommodation.id,
            guest_name="Cliente Cancelado",
            guest_phone="+5493566666666",
            guest_email="cancelado@example.com",
            check_in=check_in,
            check_out=check_out,
            guests_count=2,
            total_price=Decimal("360000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("108000.00"),
            reservation_status=ReservationStatus.CONFIRMED,
            channel_source="whatsapp",
            notes="Reserva que será cancelada"
        )
        db_session.add(original_reservation)
        await db_session.flush()

        # Cancelar la reserva
        original_reservation.reservation_status = ReservationStatus.CANCELLED
        await db_session.commit()

        # Nueva reserva en las mismas fechas - debe ser exitosa
        new_reservation = Reservation(
            code="NEW240924001",
            accommodation_id=sample_accommodation.id,
            guest_name="Cliente Nuevo",
            guest_phone="+5493577777777",
            guest_email="nuevo@example.com",
            check_in=check_in,
            check_out=check_out,
            guests_count=4,
            total_price=Decimal("360000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("108000.00"),
            reservation_status=ReservationStatus.PRE_RESERVED,
            channel_source="email",
            notes="Nueva reserva después de cancelación"
        )
        db_session.add(new_reservation)
        
        # Debe ser exitoso
        await db_session.commit()
        
        # Verificar que ambas reservas existen
        result = await db_session.execute(
            select(Reservation).where(
                Reservation.accommodation_id == sample_accommodation.id
            )
        )
        reservations = result.scalars().all()
        assert len(reservations) == 2
        
        # Verificar estados
        states = [r.reservation_status for r in reservations]
        assert ReservationStatus.CANCELLED in states
        assert ReservationStatus.PRE_RESERVED in states

    @pytest.mark.asyncio
    async def test_consecutive_bookings_with_exact_boundary(self, db_session, sample_accommodation):
        """Test crítico: checkout día X, checkin día X (consecutivo perfecto)."""
        if db_session.bind.dialect.name != "postgresql":
            pytest.skip("Constraint EXCLUDE sólo soportado en PostgreSQL")

        boundary_date = date.today() + timedelta(days=20)

        # Primera reserva: termina el día 20
        first_reservation = Reservation(
            code="CONS240924001",
            accommodation_id=sample_accommodation.id,
            guest_name="Primera Reserva",
            guest_phone="+5493588888888",
            guest_email="primera@example.com",
            check_in=boundary_date - timedelta(days=3),
            check_out=boundary_date,  # Termina el día 20
            guests_count=2,
            total_price=Decimal("360000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("108000.00"),
            reservation_status=ReservationStatus.CONFIRMED,
            channel_source="whatsapp"
        )
        db_session.add(first_reservation)
        await db_session.flush()

        # Segunda reserva: empieza el día 20 (mismo día que termina la primera)
        second_reservation = Reservation(
            code="CONS240924002",
            accommodation_id=sample_accommodation.id,
            guest_name="Segunda Reserva",
            guest_phone="+5493599999999",
            guest_email="segunda@example.com",
            check_in=boundary_date,  # Empieza el día 20
            check_out=boundary_date + timedelta(days=3),
            guests_count=3,
            total_price=Decimal("360000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("108000.00"),
            reservation_status=ReservationStatus.CONFIRMED,
            channel_source="email"
        )
        db_session.add(second_reservation)
        
        # CRÍTICO: Debe ser exitoso por el daterange '[)' half-open
        await db_session.commit()
        
        # Verificar que ambas reservas existen
        result = await db_session.execute(
            select(Reservation).where(
                Reservation.accommodation_id == sample_accommodation.id
            )
        )
        reservations = result.scalars().all()
        assert len(reservations) == 2

    @pytest.mark.asyncio
    async def test_constraint_error_message_validation(self, db_session, sample_accommodation):
        """Validar que el error específico del constraint sea detectado."""
        if db_session.bind.dialect.name != "postgresql":
            pytest.skip("Constraint EXCLUDE sólo soportado en PostgreSQL")

        check_in = date.today() + timedelta(days=25)
        check_out = date.today() + timedelta(days=28)

        # Primera reserva
        first = Reservation(
            code="ERR240924001",
            accommodation_id=sample_accommodation.id,
            guest_name="Primera",
            guest_phone="+5493500000001",
            guest_email="primera@test.com",
            check_in=check_in,
            check_out=check_out,
            guests_count=2,
            total_price=Decimal("360000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("108000.00"),
            reservation_status=ReservationStatus.CONFIRMED,
            channel_source="whatsapp"
        )
        db_session.add(first)
        await db_session.flush()

        # Segunda reserva - conflicto directo
        second = Reservation(
            code="ERR240924002",
            accommodation_id=sample_accommodation.id,
            guest_name="Segunda",
            guest_phone="+5493500000002",
            guest_email="segunda@test.com",
            check_in=check_in,
            check_out=check_out,
            guests_count=4,
            total_price=Decimal("360000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("108000.00"),
            reservation_status=ReservationStatus.PRE_RESERVED,
            channel_source="email"
        )
        db_session.add(second)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        
        error_str = str(exc_info.value).lower()
        
        # Verificar que el error contiene información del constraint
        constraint_indicators = [
            "no_overlap_reservations",
            "overlaps", 
            "exclude",
            "gist",
            "period"
        ]
        
        assert any(indicator in error_str for indicator in constraint_indicators), \
            f"Error no contiene indicadores del constraint esperados. Error: {error_str}"