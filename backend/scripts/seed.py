#!/usr/bin/env python3
from __future__ import annotations

import asyncio
from decimal import Decimal
from datetime import date

from app.core.database import async_session_maker
from app.models import Accommodation

async def main():
    async with async_session_maker() as db:
        acc = Accommodation(
            name="Cabaña Demo",
            type="cabin",
            capacity=4,
            base_price=Decimal("15000.00"),
        )
        db.add(acc)
        await db.commit()
        await db.refresh(acc)
        print({"accommodation_id": acc.id})

if __name__ == "__main__":
    asyncio.run(main())
