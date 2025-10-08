import pytest
from httpx import Response

pytestmark = pytest.mark.asyncio


async def test_health_degraded_only_ical(test_client, monkeypatch):  # type: ignore
    # Forzamos database y redis OK devolviendo status ok, y iCal warning
    from app.routers import health as health_mod

    async def ok_db():
        return {"status": "ok"}

    async def ok_redis():
        return {"status": "ok"}

    monkeypatch.setattr(health_mod, "check_database_health", ok_db)
    monkeypatch.setattr(health_mod, "check_redis_health", ok_redis)

    r = await test_client.get("/api/v1/healthz")
    assert r.status_code == 200
    data = r.json()
    assert data["checks"]["ical"]["status"] == "warning"
    # No errores, sólo warning => degraded
    assert data["status"] == "degraded"


async def test_health_unhealthy_redis_error(test_client, monkeypatch):  # type: ignore
    from app.routers import health as health_mod

    async def ok_db():
        return {"status": "ok"}

    async def err_redis():
        return {"status": "error", "detail": "connection_failed"}

    monkeypatch.setattr(health_mod, "check_database_health", ok_db)
    monkeypatch.setattr(health_mod, "check_redis_health", err_redis)

    r = await test_client.get("/api/v1/healthz")
    assert r.status_code == 200
    data = r.json()
    assert data["checks"]["redis"]["status"] == "error"
    assert data["status"] == "unhealthy"
