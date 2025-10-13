# Reexport fixtures desde tests/ para que tests_e2e los vea
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient

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


# NOTE: db_session fixture removed - E2E tests should only access the system via API
# This ensures tests validate the complete system behavior, not internal DB state directly.


@pytest.fixture()
def admin_token():
    """Token JWT de admin para tests (placeholder)"""
    return "test_admin_token"
