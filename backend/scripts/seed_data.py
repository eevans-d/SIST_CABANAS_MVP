#!/usr/bin/env python3
"""Create a sample accommodation for testing."""
# flake8: noqa: E402

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import uuid
from decimal import Decimal

from app.core.database import async_session_maker
from app.models import Accommodation
from sqlalchemy import select


async def seed_data():
    """Create sample accommodations."""
    async with async_session_maker() as session:
        # Check if already exists
        stmt = select(Accommodation).filter(Accommodation.name == "Casa Frente al Mar")
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            print("✅ Sample accommodation already exists")
            return

        acc = Accommodation(
            uuid=uuid.uuid4(),
            name="Casa Frente al Mar",
            type="house",
            capacity=6,
            base_price=Decimal("150.00"),
            weekend_multiplier=Decimal("1.3"),
            description="Hermosa casa junto a la playa",
            amenities={"wifi": True, "parking": True, "pool": True},
            photos=["photo1.jpg", "photo2.jpg"],
            location={"lat": -34.9011, "lng": -56.1645, "city": "Montevideo"},
            policies={"checkin": "14:00", "checkout": "11:00", "cancellation": "7 days free"},
            ical_export_token=uuid.uuid4().hex,
            active=True,
        )
        session.add(acc)
        await session.commit()
        print(f"✅ Created sample accommodation: {acc.name} (ID: {acc.id})")


if __name__ == "__main__":
    asyncio.run(seed_data())
