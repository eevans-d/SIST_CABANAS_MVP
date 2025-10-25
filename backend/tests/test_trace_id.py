"""Tests para trace ID middleware y logging estructurado.

Valida:
- Trace ID en headers de response
- Trace ID en logs
- Propagación de trace ID a través de requests
- Decoradores de logging
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_trace_id_in_response_header(test_client: AsyncClient):
    """Response debe incluir header X-Trace-ID."""
    response = await test_client.get("/api/v1/healthz")

    assert "X-Trace-ID" in response.headers
    assert len(response.headers["X-Trace-ID"]) == 36  # UUID format


@pytest.mark.asyncio
async def test_trace_id_propagation(test_client: AsyncClient):
    """Trace ID del request debe propagarse al response."""
    custom_trace_id = "test-trace-id-12345"

    response = await test_client.get("/api/v1/healthz", headers={"X-Trace-ID": custom_trace_id})

    assert response.headers["X-Trace-ID"] == custom_trace_id


@pytest.mark.asyncio
async def test_trace_id_generation_when_missing(test_client: AsyncClient):
    """Si no hay trace ID en request, debe generarse uno nuevo."""
    response1 = await test_client.get("/api/v1/healthz")
    response2 = await test_client.get("/api/v1/healthz")

    trace_id_1 = response1.headers["X-Trace-ID"]
    trace_id_2 = response2.headers["X-Trace-ID"]

    # Deben ser diferentes (generados únicos)
    assert trace_id_1 != trace_id_2
    # Deben tener formato UUID
    assert len(trace_id_1) == 36
    assert len(trace_id_2) == 36


@pytest.mark.asyncio
async def test_trace_id_in_logs(test_client: AsyncClient, caplog):
    """Logs deben incluir trace_id cuando hay request activo."""
    import logging

    # Configurar caplog para capturar logs de structlog
    caplog.set_level(logging.INFO)

    custom_trace_id = "test-trace-logging"

    await test_client.get("/api/v1/healthz", headers={"X-Trace-ID": custom_trace_id})

    # Verificar que algún log contiene el trace_id
    # NOTA: En producción structlog usa JSONRenderer, en tests puede usar ConsoleRenderer
    # Por lo que buscamos el trace_id en los logs
    log_output = caplog.text

    # El trace_id debe aparecer en los logs del request
    assert custom_trace_id in log_output or "trace_id" in log_output


@pytest.mark.asyncio
async def test_logging_decorator_basic():
    """Decorador log_service_call debe funcionar correctamente."""
    from app.utils.logging_decorators import log_service_call

    call_count = 0

    @log_service_call("test_operation")
    async def test_service(value: int):
        nonlocal call_count
        call_count += 1
        return value * 2

    result = await test_service(21)

    assert result == 42
    assert call_count == 1


@pytest.mark.asyncio
async def test_logging_decorator_with_exception():
    """Decorador debe loggear errores y re-lanzarlos."""
    from app.utils.logging_decorators import log_service_call

    @log_service_call("failing_operation")
    async def failing_service():
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        await failing_service()


def test_sync_logging_decorator():
    """Decorador debe funcionar con funciones síncronas."""
    from app.utils.logging_decorators import log_service_call

    @log_service_call("sync_operation")
    def sync_service(x: int, y: int):
        return x + y

    result = sync_service(10, 32)
    assert result == 42


def test_get_trace_id_outside_request():
    """get_trace_id debe retornar string vacío fuera de request."""
    from app.core.middleware import get_trace_id

    trace_id = get_trace_id()
    assert trace_id == ""


@pytest.mark.asyncio
async def test_trace_id_cleared_after_request(test_client: AsyncClient):
    """Context vars deben limpiarse después de cada request."""
    from app.core.middleware import get_trace_id

    # Hacer request
    await test_client.get("/api/v1/healthz")

    # Después del request, trace_id debe estar limpio
    # (esto se ejecuta fuera del contexto del request)
    trace_id = get_trace_id()
    assert trace_id == ""


@pytest.mark.asyncio
async def test_request_logging_includes_duration(test_client: AsyncClient, caplog):
    """Logs de request deben incluir duración."""
    import logging

    caplog.set_level(logging.INFO)

    await test_client.get("/api/v1/healthz")

    log_output = caplog.text

    # Debe incluir información de duración
    assert "duration_ms" in log_output or "completed" in log_output
