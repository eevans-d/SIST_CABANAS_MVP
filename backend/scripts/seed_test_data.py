"""Seed test data for E2E tests.

Crea alojamientos y reservas de ejemplo para testing.
"""
import asyncio
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog
from app.core.database import async_session_maker
from app.models import Accommodation, Reservation
from app.models.enums import PaymentStatus, ReservationStatus
from sqlalchemy import select

logger = structlog.get_logger()


async def seed_accommodations(session):
    """Crear alojamientos de prueba."""
    logger.info("seeding_accommodations")

    # Verificar si ya existen
    result = await session.execute(select(Accommodation))
    existing = result.scalars().first()
    if existing:
        logger.info("accommodations_already_exist", count=len(result.scalars().all()))
        return

    accommodations = [
        Accommodation(
            name="Cabaña del Bosque",
            type="cabin",
            capacity=4,
            base_price=Decimal("15000.00"),
            weekend_multiplier=Decimal("1.3"),
            description="Cabaña acogedora en el bosque con vista al lago",
            amenities={
                "wifi": True,
                "kitchen": True,
                "parking": True,
                "heating": True,
                "bbq": True,
            },
            photos=[
                {"url": "https://example.com/cabin1.jpg", "order": 1},
                {"url": "https://example.com/cabin2.jpg", "order": 2},
            ],
            location={
                "address": "Ruta 40 Km 2450",
                "city": "San Carlos de Bariloche",
                "province": "Río Negro",
                "country": "Argentina",
                "lat": -41.1335,
                "lng": -71.3103,
            },
            policies={
                "check_in": "14:00",
                "check_out": "10:00",
                "cancellation": "Cancelación gratuita hasta 48hs antes",
                "pets": False,
                "smoking": False,
            },
            active=True,
        ),
        Accommodation(
            name="Cabaña Vista al Lago",
            type="cabin",
            capacity=6,
            base_price=Decimal("22000.00"),
            weekend_multiplier=Decimal("1.4"),
            description="Cabaña premium con vista panorámica al lago Nahuel Huapi",
            amenities={
                "wifi": True,
                "kitchen": True,
                "parking": True,
                "heating": True,
                "bbq": True,
                "jacuzzi": True,
                "fireplace": True,
            },
            photos=[
                {"url": "https://example.com/lake1.jpg", "order": 1},
                {"url": "https://example.com/lake2.jpg", "order": 2},
                {"url": "https://example.com/lake3.jpg", "order": 3},
            ],
            location={
                "address": "Av. Bustillo Km 25",
                "city": "San Carlos de Bariloche",
                "province": "Río Negro",
                "country": "Argentina",
                "lat": -41.0801,
                "lng": -71.5310,
            },
            policies={
                "check_in": "15:00",
                "check_out": "11:00",
                "cancellation": "Cancelación gratuita hasta 72hs antes",
                "pets": True,
                "smoking": False,
            },
            active=True,
        ),
        Accommodation(
            name="Loft Centro",
            type="apartment",
            capacity=2,
            base_price=Decimal("8000.00"),
            weekend_multiplier=Decimal("1.2"),
            description="Loft moderno en el centro de Bariloche",
            amenities={
                "wifi": True,
                "kitchen": False,
                "parking": False,
                "heating": True,
            },
            photos=[
                {"url": "https://example.com/loft1.jpg", "order": 1},
            ],
            location={
                "address": "Mitre 350",
                "city": "San Carlos de Bariloche",
                "province": "Río Negro",
                "country": "Argentina",
                "lat": -41.1344,
                "lng": -71.3020,
            },
            policies={
                "check_in": "14:00",
                "check_out": "10:00",
                "cancellation": "Cancelación gratuita hasta 24hs antes",
                "pets": False,
                "smoking": False,
            },
            active=True,
        ),
    ]

    session.add_all(accommodations)
    await session.commit()

    logger.info("accommodations_seeded", count=len(accommodations))


async def seed_reservations(session):
    """Crear reservas de ejemplo."""
    logger.info("seeding_reservations")

    # Obtener alojamientos
    result = await session.execute(select(Accommodation))
    accommodations = result.scalars().all()

    if not accommodations:
        logger.warning("no_accommodations_found_for_reservations")
        return

    now = datetime.now(timezone.utc)
    today = date.today()

    reservations = [
        # Pre-reserva activa (expira en 20 minutos)
        Reservation(
            code=f"RES{now:%y%m%d}001TST",
            accommodation_id=accommodations[0].id,
            guest_name="Juan Pérez",
            guest_email="juan.perez@test.com",
            guest_phone="+5491112345678",
            check_in=today + timedelta(days=7),
            check_out=today + timedelta(days=10),
            guests_count=4,
            nights=3,
            base_price_per_night=Decimal("15000.00"),
            total_price=Decimal("45000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("13500.00"),
            reservation_status=ReservationStatus.PRE_RESERVED.value,
            payment_status=PaymentStatus.PENDING.value,
            channel_source="whatsapp",
            expires_at=now + timedelta(minutes=20),
            created_at=now - timedelta(minutes=10),
        ),
        # Pre-reserva que expirará pronto (5 minutos)
        Reservation(
            code=f"RES{now:%y%m%d}002TST",
            accommodation_id=accommodations[1].id,
            guest_name="María López",
            guest_email="maria.lopez@test.com",
            guest_phone="+5491198765432",
            check_in=today + timedelta(days=14),
            check_out=today + timedelta(days=17),
            guests_count=2,
            nights=3,
            base_price_per_night=Decimal("22000.00"),
            total_price=Decimal("66000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("19800.00"),
            reservation_status=ReservationStatus.PRE_RESERVED.value,
            payment_status=PaymentStatus.PENDING.value,
            channel_source="email",
            expires_at=now + timedelta(minutes=5),
            created_at=now - timedelta(minutes=25),
        ),
        # Reserva confirmada
        Reservation(
            code=f"RES{now:%y%m%d}003TST",
            accommodation_id=accommodations[0].id,
            guest_name="Carlos García",
            guest_email="carlos.garcia@test.com",
            guest_phone="+5491155554444",
            check_in=today + timedelta(days=21),
            check_out=today + timedelta(days=24),
            guests_count=3,
            nights=3,
            base_price_per_night=Decimal("15000.00"),
            total_price=Decimal("45000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("13500.00"),
            reservation_status=ReservationStatus.CONFIRMED.value,
            payment_status=PaymentStatus.PAID.value,
            channel_source="whatsapp",
            confirmed_at=now - timedelta(hours=2),
            created_at=now - timedelta(hours=3),
        ),
        # Reserva cancelada
        Reservation(
            code=f"RES{now:%y%m%d}004TST",
            accommodation_id=accommodations[2].id,
            guest_name="Ana Rodríguez",
            guest_email="ana.rodriguez@test.com",
            guest_phone="+5491166667777",
            check_in=today + timedelta(days=5),
            check_out=today + timedelta(days=7),
            guests_count=2,
            nights=2,
            base_price_per_night=Decimal("8000.00"),
            total_price=Decimal("16000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("4800.00"),
            reservation_status=ReservationStatus.CANCELLED.value,
            payment_status=PaymentStatus.PENDING.value,
            channel_source="email",
            cancelled_at=now - timedelta(days=1),
            created_at=now - timedelta(days=2),
            internal_notes="Cancelada por el huésped - cambio de planes",
        ),
    ]

    session.add_all(reservations)
    await session.commit()

    logger.info("reservations_seeded", count=len(reservations))


async def main():
    """Seed principal."""
    logger.info("seed_test_data_start")

    try:
        async with async_session_maker() as session:
            await seed_accommodations(session)
            await seed_reservations(session)

        logger.info("seed_test_data_complete", status="success")
        return 0
    except Exception as e:
        logger.error("seed_test_data_failed", error=str(e), error_type=type(e).__name__)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
