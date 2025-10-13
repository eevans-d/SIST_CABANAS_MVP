# Reexport fixtures desde tests/ para que tests_e2e los vea
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

root = Path(__file__).resolve().parents[1]
tests_dir = root / "tests"
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))


# Fixtures para tests E2E que hablan con el contenedor en :8001
@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTP que se conecta al contenedor E2E en localhost:8001"""
    async with AsyncClient(base_url="http://localhost:8001", timeout=30.0) as ac:
        yield ac


@pytest.fixture()
async def db_session():
    """Sesión de DB conectada a la base de datos del contenedor E2E"""
    # Conectar a postgres-test en el puerto 5433
    DATABASE_URL = (
        "postgresql+asyncpg://alojamientos_test:test_pass@localhost:5433/alojamientos_test"
    )

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture()
def admin_token():
    """Token JWT de admin para tests (placeholder)"""
    return "test_admin_token"
