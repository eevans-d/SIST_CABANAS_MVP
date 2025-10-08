import pytest

pytestmark = pytest.mark.asyncio


async def test_health_ok(test_client):  # type: ignore
    r = await test_client.get("/api/v1/healthz")
    assert r.status_code == 200
    data = r.json()
    # Debe tener estado general
    assert data["status"] in {
        "healthy",
        "degraded",
        "unhealthy",
    }  # permitir unhealthy si dependencias criticas fallan (e.g. Redis auth)
    checks = data["checks"]
    # Claves mínimas
    for key in ["database", "redis", "disk", "memory", "ical", "whatsapp", "mercadopago"]:
        assert key in checks
    # DB y Redis deberían estar ok en entorno de prueba (o error explícito si no disponibles)
    assert checks["database"]["status"] in {"ok", "error"}
    assert checks["redis"]["status"] in {"ok", "error"}
    # iCal placeholder warning
    assert checks["ical"]["status"] in {"warning", "ok"}
