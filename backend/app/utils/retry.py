"""
Utilidades para retry logic con exponential backoff.

Implementa decorador genérico para reintentar operaciones fallidas
con estrategia de exponential backoff + jitter aleatorio.

Características:
- Exponential backoff: 1s, 2s, 4s, 8s, 16s...
- Jitter aleatorio (±20%) para evitar thundering herd
- Configuración de max_attempts y base_delay
- Logging detallado de cada intento
- Distinción entre errores transitorios (retry) y permanentes (fail fast)
- Métricas Prometheus de retry attempts y failures
"""
from __future__ import annotations

import asyncio
import random
from functools import wraps
from typing import Callable, Type, Tuple, Any
import structlog
from prometheus_client import Counter, Histogram

logger = structlog.get_logger()

# Métricas Prometheus para retry logic
RETRY_ATTEMPTS = Counter(
    "retry_attempts_total",
    "Total de intentos de retry por operación y resultado",
    ["operation", "attempt_number", "result"]  # result = success|retry|failed
)

RETRY_DELAYS = Histogram(
    "retry_delay_seconds",
    "Distribución de delays entre intentos de retry",
    ["operation"],
    buckets=[0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0]
)

RETRY_EXHAUSTED = Counter(
    "retry_exhausted_total",
    "Total de operaciones que agotaron todos los intentos",
    ["operation", "error_type"]
)


class RetryExhausted(Exception):
    """Se lanzó cuando se agotaron todos los intentos de retry"""
    pass


def calculate_backoff_delay(attempt: int, base_delay: float = 1.0, max_delay: float = 32.0) -> float:
    """Calcula el delay para el próximo reintento con exponential backoff + jitter.
    
    Args:
        attempt: Número de intento actual (0-indexed)
        base_delay: Delay base en segundos (default 1.0)
        max_delay: Delay máximo en segundos (default 32.0)
        
    Returns:
        float: Segundos a esperar antes del próximo intento
        
    Example:
        attempt=0 → ~1s
        attempt=1 → ~2s
        attempt=2 → ~4s
        attempt=3 → ~8s
        attempt=4 → ~16s
        attempt=5 → ~32s (capped)
    """
    # Exponential backoff: base_delay * (2 ^ attempt)
    exponential_delay = base_delay * (2 ** attempt)
    
    # Cap al máximo
    capped_delay = min(exponential_delay, max_delay)
    
    # Agregar jitter aleatorio (±20%)
    jitter = capped_delay * 0.2 * (random.random() * 2 - 1)  # Entre -20% y +20%
    
    return max(0.1, capped_delay + jitter)  # Mínimo 0.1s


def is_transient_error(exception: Exception) -> bool:
    """Determina si un error es transitorio (se puede reintentar) o permanente.
    
    Errores transitorios (retry):
    - ConnectionError, TimeoutError
    - HTTP 429 (Rate Limit), 500, 502, 503, 504
    - Errores de red temporales
    
    Errores permanentes (no retry):
    - HTTP 400, 401, 403, 404
    - ValidationError, ValueError, TypeError
    - Errores de lógica de negocio
    
    Args:
        exception: Excepción a evaluar
        
    Returns:
        bool: True si es transitorio (se debe reintentar), False si es permanente
    """
    # Errores Python permanentes
    if isinstance(exception, (ValueError, TypeError, KeyError, AttributeError)):
        return False
    
    # Errores de red/conexión → transitorio
    if isinstance(exception, (ConnectionError, TimeoutError, asyncio.TimeoutError)):
        return True
    
    # Verificar si es un error HTTP (httpx, requests, aiohttp)
    exception_str = str(exception).lower()
    error_name = type(exception).__name__.lower()
    
    # HTTP errors transitorios
    transient_patterns = [
        "429",  # Rate limit
        "500", "502", "503", "504",  # Server errors
        "timeout",
        "connection",
        "network",
        "temporary",
    ]
    
    for pattern in transient_patterns:
        if pattern in exception_str or pattern in error_name:
            return True
    
    # HTTP errors permanentes
    permanent_patterns = [
        "400", "401", "403", "404",  # Client errors
        "validation",
        "invalid",
    ]
    
    for pattern in permanent_patterns:
        if pattern in exception_str or pattern in error_name:
            return False
    
    # Por defecto, considerar transitorio para ser conservadores
    return True


def retry_async(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 32.0,
    retriable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    operation_name: str = "operation"
):
    """Decorador para reintentar funciones async con exponential backoff.
    
    Incluye métricas Prometheus automáticas de intentos, delays y fallos.
    
    Args:
        max_attempts: Número máximo de intentos (default 3)
        base_delay: Delay base en segundos (default 1.0)
        max_delay: Delay máximo en segundos (default 32.0)
        retriable_exceptions: Tupla de excepciones que se pueden reintentar
        operation_name: Nombre de la operación para logging y métricas
        
    Example:
        @retry_async(max_attempts=5, base_delay=1.0, operation_name="whatsapp_send")
        async def send_message():
            # código que puede fallar
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    logger.debug(
                        "retry_attempt",
                        operation=operation_name,
                        attempt=attempt + 1,
                        max_attempts=max_attempts
                    )
                    
                    result = await func(*args, **kwargs)
                    
                    # Métrica: intento exitoso
                    RETRY_ATTEMPTS.labels(
                        operation=operation_name,
                        attempt_number=str(attempt + 1),
                        result="success"
                    ).inc()
                    
                    # Si hubo intentos previos, logear el éxito
                    if attempt > 0:
                        logger.info(
                            "retry_success",
                            operation=operation_name,
                            attempt=attempt + 1,
                            total_attempts=attempt + 1
                        )
                    
                    return result
                    
                except retriable_exceptions as e:
                    last_exception = e
                    
                    # Verificar si es un error transitorio
                    if not is_transient_error(e):
                        logger.warning(
                            "retry_permanent_error",
                            operation=operation_name,
                            error=str(e),
                            error_type=type(e).__name__
                        )
                        # Métrica: error permanente (no retry)
                        RETRY_ATTEMPTS.labels(
                            operation=operation_name,
                            attempt_number=str(attempt + 1),
                            result="failed_permanent"
                        ).inc()
                        raise  # No reintentar errores permanentes
                    
                    # Si es el último intento, no esperar
                    if attempt == max_attempts - 1:
                        logger.error(
                            "retry_exhausted",
                            operation=operation_name,
                            total_attempts=max_attempts,
                            last_error=str(e),
                            error_type=type(e).__name__
                        )
                        # Métrica: retry agotado
                        RETRY_EXHAUSTED.labels(
                            operation=operation_name,
                            error_type=type(e).__name__
                        ).inc()
                        break
                    
                    # Calcular delay y esperar
                    delay = calculate_backoff_delay(attempt, base_delay, max_delay)
                    
                    logger.warning(
                        "retry_failed_attempt",
                        operation=operation_name,
                        attempt=attempt + 1,
                        max_attempts=max_attempts,
                        error=str(e),
                        error_type=type(e).__name__,
                        next_retry_in_seconds=round(delay, 2)
                    )
                    
                    # Métrica: intento fallido que se reintentará
                    RETRY_ATTEMPTS.labels(
                        operation=operation_name,
                        attempt_number=str(attempt + 1),
                        result="retry"
                    ).inc()
                    
                    # Métrica: delay aplicado
                    RETRY_DELAYS.labels(operation=operation_name).observe(delay)
                    
                    await asyncio.sleep(delay)
            
            # Si llegamos aquí, se agotaron los intentos
            raise RetryExhausted(
                f"{operation_name} failed after {max_attempts} attempts. "
                f"Last error: {last_exception}"
            ) from last_exception
        
        return wrapper
    return decorator


def retry_sync(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 32.0,
    retriable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    operation_name: str = "operation"
):
    """Decorador para reintentar funciones síncronas con exponential backoff.
    
    Versión síncrona del decorador retry_async. Incluye métricas Prometheus.
    
    Args:
        max_attempts: Número máximo de intentos (default 3)
        base_delay: Delay base en segundos (default 1.0)
        max_delay: Delay máximo en segundos (default 32.0)
        retriable_exceptions: Tupla de excepciones que se pueden reintentar
        operation_name: Nombre de la operación para logging y métricas
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import time
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    logger.debug(
                        "retry_attempt",
                        operation=operation_name,
                        attempt=attempt + 1,
                        max_attempts=max_attempts
                    )
                    
                    result = func(*args, **kwargs)
                    
                    # Métrica: éxito
                    RETRY_ATTEMPTS.labels(
                        operation=operation_name,
                        attempt_number=str(attempt + 1),
                        result="success"
                    ).inc()
                    
                    if attempt > 0:
                        logger.info(
                            "retry_success",
                            operation=operation_name,
                            attempt=attempt + 1,
                            total_attempts=attempt + 1
                        )
                    
                    return result
                    
                except retriable_exceptions as e:
                    last_exception = e
                    
                    if not is_transient_error(e):
                        logger.warning(
                            "retry_permanent_error",
                            operation=operation_name,
                            error=str(e),
                            error_type=type(e).__name__
                        )
                        # Métrica: error permanente
                        RETRY_ATTEMPTS.labels(
                            operation=operation_name,
                            attempt_number=str(attempt + 1),
                            result="failed_permanent"
                        ).inc()
                        raise
                    
                    if attempt == max_attempts - 1:
                        logger.error(
                            "retry_exhausted",
                            operation=operation_name,
                            total_attempts=max_attempts,
                            last_error=str(e),
                            error_type=type(e).__name__
                        )
                        # Métrica: retry agotado
                        RETRY_EXHAUSTED.labels(
                            operation=operation_name,
                            error_type=type(e).__name__
                        ).inc()
                        break
                    
                    delay = calculate_backoff_delay(attempt, base_delay, max_delay)
                    
                    logger.warning(
                        "retry_failed_attempt",
                        operation=operation_name,
                        attempt=attempt + 1,
                        max_attempts=max_attempts,
                        error=str(e),
                        error_type=type(e).__name__,
                        next_retry_in_seconds=round(delay, 2)
                    )
                    
                    # Métrica: intento fallido que se reintentará
                    RETRY_ATTEMPTS.labels(
                        operation=operation_name,
                        attempt_number=str(attempt + 1),
                        result="retry"
                    ).inc()
                    
                    # Métrica: delay aplicado
                    RETRY_DELAYS.labels(operation=operation_name).observe(delay)
                    
                    time.sleep(delay)
            
            raise RetryExhausted(
                f"{operation_name} failed after {max_attempts} attempts. "
                f"Last error: {last_exception}"
            ) from last_exception
        
        return wrapper
    return decorator
