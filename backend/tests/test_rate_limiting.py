"""
Tests para el middleware de rate limiting.

Valida:
- Límites por IP y path
- Bypass de endpoints de observabilidad
- Fail-open en caso de error de Redis
- Métricas de Prometheus
- Headers X-Forwarded-For
"""

import pytest
from app.core.config import get_settings
from app.metrics import RATE_LIMIT_BLOCKED, RATE_LIMIT_REDIS_ERRORS
from httpx import AsyncClient

settings = get_settings()


@pytest.mark.asyncio
async def test_rate_limit_allows_requests_under_limit(test_client: AsyncClient, redis_client):
    """
    Validar que requests bajo el límite pasan correctamente.
    """
    # Configurar límite temporal en Redis
    test_ip = "192.168.1.100"
    test_path = "/api/v1/reservations"

    # Hacer 5 requests (bajo límite típico de 100/min)
    for i in range(5):
        response = await test_client.get(
            test_path,
            headers={"X-Forwarded-For": test_ip},
        )
        # Debe pasar (aunque /reservations GET no exista, el rate limit deja pasar)
        assert response.status_code in (404, 200, 405), f"Request {i+1} blocked incorrectly"


@pytest.mark.asyncio
async def test_rate_limit_blocks_requests_over_limit(test_client: AsyncClient, redis_client):
    """
    Validar que requests que exceden el límite son bloqueadas con 429.

    IMPORTANTE: Este test requiere que RATE_LIMIT_ENABLED=true en test env.
    """
    if not settings.RATE_LIMIT_ENABLED:
        pytest.skip("Rate limiting disabled in test environment")

    test_ip = "192.168.1.101"
    test_path = "/api/v1/test-rate-limit"
    key = f"ratelimit:{test_ip}:{test_path}"

    # Limpiar contador previo
    await redis_client.delete(key)

    # Obtener límite actual
    limit = settings.RATE_LIMIT_REQUESTS

    # Hacer requests hasta exceder límite
    responses = []
    for i in range(limit + 10):
        response = await test_client.get(
            test_path,
            headers={"X-Forwarded-For": test_ip},
        )
        responses.append(response)

    # Los primeros {limit} deben pasar (aunque sea 404 por endpoint inexistente)
    for i in range(limit):
        assert responses[i].status_code in (404, 200, 405), f"Request {i+1} incorrectly blocked"

    # Los siguientes deben ser bloqueados con 429
    blocked_count = sum(1 for r in responses[limit:] if r.status_code == 429)
    assert blocked_count > 0, "Rate limit did not block requests over limit"


@pytest.mark.asyncio
async def test_rate_limit_bypasses_health_endpoints(test_client: AsyncClient, redis_client):
    """
    Validar que /api/v1/healthz, /metrics no son limitados por rate limit.
    """
    test_ip = "192.168.1.102"

    # Hacer muchos requests a healthz (mucho más que el límite)
    bypass_paths = ["/api/v1/healthz", "/metrics"]

    for path in bypass_paths:
        for _ in range(200):  # Más que cualquier límite razonable
            response = await test_client.get(
                path,
                headers={"X-Forwarded-For": test_ip},
            )
            # Nunca debe ser 429
            assert response.status_code != 429, f"{path} was rate limited (should bypass)"


@pytest.mark.asyncio
async def test_rate_limit_respects_x_forwarded_for(test_client: AsyncClient, redis_client):
    """
    Validar que rate limit usa X-Forwarded-For para identificar cliente real.
    """
    if not settings.RATE_LIMIT_ENABLED:
        pytest.skip("Rate limiting disabled")

    # Dos IPs diferentes deben tener contadores independientes
    ip1 = "10.0.0.1"
    ip2 = "10.0.0.2"
    test_path = "/api/v1/test-path"

    # Limpiar contadores
    await redis_client.delete(f"ratelimit:{ip1}:{test_path}")
    await redis_client.delete(f"ratelimit:{ip2}:{test_path}")

    # Hacer límite de requests con IP1
    limit = settings.RATE_LIMIT_REQUESTS
    for _ in range(limit):
        response = await test_client.get(test_path, headers={"X-Forwarded-For": ip1})
        assert response.status_code in (404, 200, 405)

    # IP1 debe estar bloqueada
    response = await test_client.get(test_path, headers={"X-Forwarded-For": ip1})
    assert response.status_code == 429, "IP1 should be blocked"

    # IP2 debe poder hacer requests (contador independiente)
    response = await test_client.get(test_path, headers={"X-Forwarded-For": ip2})
    assert response.status_code in (404, 200, 405), "IP2 should not be blocked"


@pytest.mark.asyncio
async def test_rate_limit_fail_open_on_redis_error(test_client: AsyncClient, monkeypatch):
    """
    Validar que si Redis falla, el rate limit hace fail-open (no bloquea).
    """

    # Mockear get_redis_pool para que falle
    async def mock_failing_redis():
        raise ConnectionError("Redis connection failed")

    from app import main

    monkeypatch.setattr(main, "get_redis_pool", mock_failing_redis)

    # Request debe pasar aunque Redis falle
    response = await test_client.get("/api/v1/test-path")
    assert response.status_code != 429, "Request blocked on Redis failure (should fail-open)"

    # Verificar que se incrementó métrica de errores
    # (requiere acceso a registry de Prometheus, simplificado)
    # En producción, verificar RATE_LIMIT_REDIS_ERRORS.collect()[0].samples


@pytest.mark.asyncio
async def test_rate_limit_metrics_are_updated(test_client: AsyncClient, redis_client):
    """
    Validar que métricas de Prometheus se actualizan correctamente.
    """
    if not settings.RATE_LIMIT_ENABLED:
        pytest.skip("Rate limiting disabled")

    test_ip = "192.168.1.200"
    test_path = "/api/v1/metrics-test"

    # Limpiar contador
    key = f"ratelimit:{test_ip}:{test_path}"
    await redis_client.delete(key)

    # Obtener conteo inicial de bloqueos
    initial_blocked = RATE_LIMIT_BLOCKED.labels(path=test_path, client_ip=test_ip)._value.get()

    # Exceder límite
    limit = settings.RATE_LIMIT_REQUESTS
    for _ in range(limit + 5):
        await test_client.get(test_path, headers={"X-Forwarded-For": test_ip})

    # Verificar que métrica de bloqueos aumentó
    final_blocked = RATE_LIMIT_BLOCKED.labels(path=test_path, client_ip=test_ip)._value.get()
    assert final_blocked > initial_blocked, "RATE_LIMIT_BLOCKED metric not incremented"


@pytest.mark.asyncio
async def test_rate_limit_window_expiration(test_client: AsyncClient, redis_client):
    """
    Validar que el contador de rate limit expira después de la ventana de tiempo.
    """
    if not settings.RATE_LIMIT_ENABLED:
        pytest.skip("Rate limiting disabled")

    test_ip = "192.168.1.300"
    test_path = "/api/v1/expiration-test"
    key = f"ratelimit:{test_ip}:{test_path}"

    # Limpiar contador
    await redis_client.delete(key)

    # Hacer 1 request
    await test_client.get(test_path, headers={"X-Forwarded-For": test_ip})

    # Verificar que TTL está configurado
    ttl = await redis_client.ttl(key)
    assert ttl > 0, "Rate limit key should have TTL"
    assert ttl <= settings.RATE_LIMIT_WINDOW_SECONDS, "TTL exceeds configured window"


@pytest.mark.asyncio
async def test_rate_limit_different_paths_independent_counters(
    test_client: AsyncClient, redis_client
):
    """
    Validar que diferentes paths tienen contadores independientes.
    """
    if not settings.RATE_LIMIT_ENABLED:
        pytest.skip("Rate limiting disabled")

    test_ip = "192.168.1.400"
    path1 = "/api/v1/path-1"
    path2 = "/api/v1/path-2"

    # Limpiar contadores
    await redis_client.delete(f"ratelimit:{test_ip}:{path1}")
    await redis_client.delete(f"ratelimit:{test_ip}:{path2}")

    # Exceder límite en path1
    limit = settings.RATE_LIMIT_REQUESTS
    for _ in range(limit):
        await test_client.get(path1, headers={"X-Forwarded-For": test_ip})

    # path1 debe estar bloqueado
    response = await test_client.get(path1, headers={"X-Forwarded-For": test_ip})
    assert response.status_code == 429, "path1 should be blocked"

    # path2 debe estar libre (contador independiente)
    response = await test_client.get(path2, headers={"X-Forwarded-For": test_ip})
    assert response.status_code in (404, 200, 405), "path2 should not be blocked"
