#!/usr/bin/env python3
"""
Quick DB initialization script for MVP testing.

Creates tables directly from SQLAlchemy models without alembic.
WARNING: Only for development/testing. Do NOT use in production.
"""
# flake8: noqa: E402

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.core.database import engine
from app.models import (  # noqa: F401  # Import all models to register them
    Accommodation,
    IdempotencyKey,
    Payment,
    Reservation,
)
from app.models.base import Base


async def init_db():
    """Create all tables and enable extensions."""
    settings = get_settings()
    print(f"Initializing database: {settings.DATABASE_URL}")

    try:
        # Create all tables
        async with engine.begin() as conn:
            # PostgreSQL extensions
            db_url = settings.DATABASE_URL or ""
            if db_url.startswith("postgresql"):
                from sqlalchemy import text

                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
                print("✅ PostgreSQL extensions enabled")

            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            print("✅ All tables created")

        print("✅ Database initialized successfully")
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        await engine.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(init_db())
    sys.exit(exit_code)
