"""Middleware para trace ID y request logging.

Proporciona:
- Trace ID único por request (X-Trace-ID)
- Context var para acceder al trace ID en cualquier parte del código
- Logging estructurado de requests entrantes
"""

import time
import uuid
from contextvars import ContextVar
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

# Context var para trace ID (accesible en toda la app)
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Middleware que agrega trace ID único a cada request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa request agregando trace ID."""
        # Obtener trace ID del header o generar uno nuevo
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))

        # Guardar en context var para acceso global
        trace_id_var.set(trace_id)

        # Bind trace_id a structlog para este request
        structlog.contextvars.bind_contextvars(trace_id=trace_id)

        # Log de request entrante
        start_time = time.monotonic()

        try:
            response = await call_next(request)

            # Log de request completado con duración
            duration_ms = round((time.monotonic() - start_time) * 1000)
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

            # Agregar trace ID al response header
            response.headers["X-Trace-ID"] = trace_id

            return response

        except Exception as e:
            # Log de error con trace ID
            duration_ms = round((time.monotonic() - start_time) * 1000)
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
        finally:
            # Limpiar contextvars después del request
            structlog.contextvars.clear_contextvars()


def get_trace_id() -> str:
    """Obtiene el trace ID actual del context var.

    Útil para acceder al trace ID en cualquier parte del código.

    Returns:
        str: Trace ID actual o string vacío si no está en un request
    """
    return trace_id_var.get("")
