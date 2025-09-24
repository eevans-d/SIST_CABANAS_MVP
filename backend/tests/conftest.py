"""Fixtures base para el sistema de reservas (MVP).

Objetivos:
- Proveer sesión de DB async aislada por test (rollback al final).
- Facilitar uso de Postgres real (para constraint daterange + gist) pero permitir
  fallback a SQLite in-memory si no se encuentra el server (para tests unitarios simples).
- Proveer cliente Redis (fakeredis si está disponible) para pruebas de locks.
- Incluir factories básicas de modelos (se auto-skippean si los modelos aún no existen).
- Proveer un cliente HTTP async cuando `app.main:app` esté disponible.

NOTA: Los tests que requieran el constraint anti-doble-booking DEBEN ejecutarse
contra PostgreSQL real (variable TEST_DATABASE_URL apuntando a instancia con
`CREATE EXTENSION btree_gist;`).
"""

import pytest
import asyncio
from typing import AsyncGenerator, Callable, Optional
from contextlib import asynccontextmanager
from decimal import Decimal
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore

try:  # fakeredis para velocidad en unit tests
    import fakeredis.aioredis as fakeredis  # type: ignore
except Exception:  # pragma: no cover
    fakeredis = None  # type: ignore

# Imports diferidos (pueden fallar si no existe aún la estructura)
try:
    from app.models.base import Base  # type: ignore
except Exception:  # pragma: no cover
    Base = None  # type: ignore

try:
    from app.core.config import Settings  # type: ignore
except Exception:  # pragma: no cover
    class Settings:  # fallback mínimo para no romper tests iniciales
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

# Test database URL (Postgres preferido; fallback a SQLite si no accesible)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost:5432/test_db"
)
SQLITE_FALLBACK_URL = "sqlite+aiosqlite:///:memory:"
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

async def _can_connect(engine) -> bool:
    try:
        async with engine.begin() as conn:  # simple probe
            await conn.run_sync(lambda c: None)
        return True
    except Exception:
        return False

@pytest.fixture(scope="session")
async def test_engine():  # type: ignore
    """Devuelve engine async.

    Si no puede conectar a Postgres, cae a SQLite in-memory para tests unitarios.
    """
    primary_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        future=True,
    )
    if not await _can_connect(primary_engine):
        await primary_engine.dispose()
        engine = create_async_engine(
            SQLITE_FALLBACK_URL,
            echo=False,
            poolclass=NullPool,
            future=True,
        )
    else:
        engine = primary_engine

    if Base is None:  # Estructura aún no creada
        pytest.skip("Base de modelos no disponible para crear tablas")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture()
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Sesión aislada por test con rollback.

    Usa SAVEPOINT implícito (transacción top-level) para revertir efectos.
    """
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        trans = await session.begin()
        try:
            yield session
        finally:
            if trans.is_active:
                await trans.rollback()

@pytest.fixture(scope="session")
async def redis_client() -> AsyncGenerator["redis.Redis", None]:  # type: ignore
    """Cliente Redis para tests.

    Prioriza fakeredis (memoria, rápido). Si no disponible y redis real tampoco
    instalable, marca tests como xfail.
    """
    if fakeredis is not None:
        client = fakeredis.FakeRedis()
        yield client
        await client.aclose()
        return

    if redis is None:
        pytest.xfail("Ni redis async ni fakeredis disponibles")

    client = redis.from_url(TEST_REDIS_URL, decode_responses=True)
    try:
        await client.ping()
    except Exception:
        pytest.xfail("Redis real no accesible y fakeredis ausente")
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.close()

@pytest.fixture()
def test_settings():  # type: ignore
    """Instancia de Settings sobreescribible.

    Los valores se alinean a entorno de test. Puede extenderse en cada test.
    """
    return Settings(
        ENVIRONMENT="test",
        DATABASE_URL=TEST_DATABASE_URL,
        REDIS_URL=TEST_REDIS_URL,
        WHATSAPP_ACCESS_TOKEN="test_token",
        WHATSAPP_APP_SECRET="test_secret",
        WHATSAPP_PHONE_ID="123456789",
        MERCADOPAGO_ACCESS_TOKEN="test_mp_token",
        BASE_URL="http://localhost:8000",
        DOMAIN="localhost",
        JWT_SECRET="test_jwt_secret",
    )

# ---------------------------------------------------------------------------
# Factories de modelos (auto-skip si aún no existen)
# ---------------------------------------------------------------------------

@pytest.fixture()
async def accommodation_factory(db_session):  # type: ignore
    try:
        from app.models.accommodation import Accommodation  # type: ignore
    except Exception:
        pytest.skip("Modelo Accommodation no disponible todavía")

    async def _create(**overrides):
        data = dict(
            name="Alojamiento Test",
            type="cabin",
            capacity=4,
            base_price=Decimal("12000.00"),
        )
        data.update(overrides)
        obj = Accommodation(**data)
        db_session.add(obj)
        await db_session.commit()
        await db_session.refresh(obj)
        return obj

    return _create

@pytest.fixture()
async def reservation_factory(db_session, accommodation_factory):  # type: ignore
    try:
        from app.models.reservation import Reservation  # type: ignore
    except Exception:
        pytest.skip("Modelo Reservation no disponible todavía")
    from datetime import date

    async def _create(**overrides):
        acc = overrides.pop("accommodation", None) or await accommodation_factory()
        data = dict(
            code="RES2501010001",
            accommodation_id=acc.id,
            check_in=date(2025, 1, 1),
            check_out=date(2025, 1, 3),
            guest_name="Tester",
            guest_phone="+5491100000000",
            guests_count=2,
            nights=2,
            base_price_per_night=Decimal("12000.00"),
            total_price=Decimal("24000.00"),
            deposit_percentage=30,
            deposit_amount=Decimal("7200.00"),
            reservation_status="pre_reserved",
            payment_status="pending",
        )
        data.update(overrides)
        obj = Reservation(**data)
        db_session.add(obj)
        await db_session.commit()
        await db_session.refresh(obj)
        return obj

    return _create

# ---------------------------------------------------------------------------
# Cliente HTTP para tests de API (se activa cuando exista app.main:app)
# ---------------------------------------------------------------------------
@pytest.fixture()
async def test_client():  # type: ignore
    try:
        from httpx import AsyncClient
        from app.main import app  # type: ignore
    except Exception:
        pytest.skip("FastAPI app no disponible aún para test_client")
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client