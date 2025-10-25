"""Decoradores para logging de servicios.

Proporciona decoradores para agregar logging automático a servicios críticos:
- log_service_call: Log de entrada/salida con duración
- Manejo de errores con contexto completo
"""

import time
from functools import wraps
from typing import Any, Callable, TypeVar

import structlog

logger = structlog.get_logger()

F = TypeVar("F", bound=Callable[..., Any])


def log_service_call(operation: str):
    """Decorador para loggear llamadas a servicios con duración.

    Args:
        operation: Nombre de la operación (ej: "create_prereservation")

    Example:
        @log_service_call("create_prereservation")
        async def create_prereservation(self, accommodation_id: int, ...):
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.monotonic()

            # Log de inicio (solo con kwargs relevantes, sin valores sensibles)
            safe_kwargs = {
                k: v for k, v in kwargs.items() if k not in ("password", "token", "secret")
            }
            logger.info(f"{operation}_started", **safe_kwargs)

            try:
                result = await func(*args, **kwargs)
                duration = time.monotonic() - start

                # Log de éxito con duración
                logger.info(
                    f"{operation}_completed",
                    duration_ms=round(duration * 1000),
                    success=True,
                )

                return result

            except Exception as e:
                duration = time.monotonic() - start

                # Log de error con contexto completo
                logger.error(
                    f"{operation}_failed",
                    duration_ms=round(duration * 1000),
                    error=str(e),
                    error_type=type(e).__name__,
                    **safe_kwargs,
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.monotonic()

            safe_kwargs = {
                k: v for k, v in kwargs.items() if k not in ("password", "token", "secret")
            }
            logger.info(f"{operation}_started", **safe_kwargs)

            try:
                result = func(*args, **kwargs)
                duration = time.monotonic() - start

                logger.info(
                    f"{operation}_completed",
                    duration_ms=round(duration * 1000),
                    success=True,
                )

                return result

            except Exception as e:
                duration = time.monotonic() - start

                logger.error(
                    f"{operation}_failed",
                    duration_ms=round(duration * 1000),
                    error=str(e),
                    error_type=type(e).__name__,
                    **safe_kwargs,
                )
                raise

        # Retornar wrapper apropiado según si la función es async o sync
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def log_critical_operation(operation: str, **context):
    """Context manager para loggear operaciones críticas con manejo de errores.

    Args:
        operation: Nombre de la operación crítica
        **context: Contexto adicional para logs

    Example:
        with log_critical_operation("payment_processing", payment_id=123):
            process_payment(...)
    """

    class LogContext:
        def __enter__(self):
            self.start = time.monotonic()
            logger.info(f"{operation}_started", **context)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.monotonic() - self.start

            if exc_type is None:
                logger.info(
                    f"{operation}_completed",
                    duration_ms=round(duration * 1000),
                    success=True,
                    **context,
                )
            else:
                logger.error(
                    f"{operation}_failed",
                    duration_ms=round(duration * 1000),
                    error=str(exc_val),
                    error_type=exc_type.__name__,
                    **context,
                )

            return False  # No suprimir excepciones

    return LogContext()
