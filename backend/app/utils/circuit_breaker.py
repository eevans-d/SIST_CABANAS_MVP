"""
Circuit Breaker Pattern para protección contra cascading failures.

Implementa el patrón Circuit Breaker para evitar llamadas repetidas a servicios
que están fallando persistentemente. Estados:
- CLOSED: Funcionamiento normal, requests pasan
- OPEN: Servicio fallando, requests se rechazan inmediatamente
- HALF_OPEN: Periodo de prueba, permite requests limitados

Características:
- Threshold de fallos consecutivos configurable
- Timeout de recuperación configurable
- Métricas Prometheus integradas
- Thread-safe con asyncio locks
"""
from __future__ import annotations

import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps
from dataclasses import dataclass, field

import structlog
from prometheus_client import Counter, Gauge, Histogram

logger = structlog.get_logger()


class CircuitState(str, Enum):
    """Estados posibles del circuit breaker"""
    CLOSED = "closed"  # Normal, requests pasan
    OPEN = "open"  # Fallando, requests rechazados
    HALF_OPEN = "half_open"  # Probando recuperación


# Métricas Prometheus para Circuit Breaker
CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state",
    "Estado actual del circuit breaker (0=closed, 1=open, 2=half_open)",
    ["circuit_name"]
)

CIRCUIT_BREAKER_FAILURES = Counter(
    "circuit_breaker_failures_total",
    "Total de fallos registrados por el circuit breaker",
    ["circuit_name"]
)

CIRCUIT_BREAKER_SUCCESSES = Counter(
    "circuit_breaker_successes_total",
    "Total de éxitos registrados por el circuit breaker",
    ["circuit_name"]
)

CIRCUIT_BREAKER_REJECTIONS = Counter(
    "circuit_breaker_rejections_total",
    "Total de requests rechazados por circuit breaker abierto",
    ["circuit_name"]
)

CIRCUIT_BREAKER_STATE_CHANGES = Counter(
    "circuit_breaker_state_changes_total",
    "Total de cambios de estado del circuit breaker",
    ["circuit_name", "from_state", "to_state"]
)


class CircuitBreakerOpen(Exception):
    """Excepción lanzada cuando el circuit breaker está abierto"""
    pass


@dataclass
class CircuitBreakerConfig:
    """Configuración del circuit breaker"""
    failure_threshold: int = 5  # Fallos consecutivos para abrir
    recovery_timeout: float = 60.0  # Segundos antes de intentar half-open
    success_threshold: int = 2  # Éxitos en half-open para cerrar
    expected_exception: type = Exception  # Tipo de excepción que cuenta como fallo


@dataclass
class CircuitBreakerState:
    """Estado interno del circuit breaker"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class CircuitBreaker:
    """Implementación de Circuit Breaker Pattern"""

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Args:
            name: Nombre del circuit breaker para logging y métricas
            config: Configuración personalizada (usa defaults si None)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitBreakerState()
        
        # Inicializar métrica de estado
        self._update_state_metric()
        
        logger.info(
            "circuit_breaker_initialized",
            name=name,
            failure_threshold=self.config.failure_threshold,
            recovery_timeout=self.config.recovery_timeout
        )

    def _update_state_metric(self):
        """Actualiza métrica Prometheus con estado actual"""
        state_values = {
            CircuitState.CLOSED: 0,
            CircuitState.OPEN: 1,
            CircuitState.HALF_OPEN: 2
        }
        CIRCUIT_BREAKER_STATE.labels(circuit_name=self.name).set(
            state_values[self._state.state]
        )

    async def _transition_to(self, new_state: CircuitState):
        """Transiciona a un nuevo estado con logging y métricas"""
        old_state = self._state.state
        if old_state == new_state:
            return
        
        self._state.state = new_state
        self._update_state_metric()
        
        # Métrica de cambio de estado
        CIRCUIT_BREAKER_STATE_CHANGES.labels(
            circuit_name=self.name,
            from_state=old_state.value,
            to_state=new_state.value
        ).inc()
        
        logger.warning(
            "circuit_breaker_state_change",
            circuit_name=self.name,
            old_state=old_state.value,
            new_state=new_state.value,
            failure_count=self._state.failure_count
        )

    async def _check_state(self):
        """Verifica si el circuit breaker debe cambiar de estado"""
        async with self._state.lock:
            current_time = time.monotonic()
            
            # Si está OPEN, verificar si es momento de probar HALF_OPEN
            if self._state.state == CircuitState.OPEN:
                time_since_failure = current_time - self._state.last_failure_time
                if time_since_failure >= self.config.recovery_timeout:
                    await self._transition_to(CircuitState.HALF_OPEN)
                    self._state.success_count = 0

    async def _on_success(self):
        """Callback cuando una operación es exitosa"""
        async with self._state.lock:
            CIRCUIT_BREAKER_SUCCESSES.labels(circuit_name=self.name).inc()
            
            if self._state.state == CircuitState.HALF_OPEN:
                self._state.success_count += 1
                if self._state.success_count >= self.config.success_threshold:
                    # Suficientes éxitos, cerrar circuit breaker
                    await self._transition_to(CircuitState.CLOSED)
                    self._state.failure_count = 0
            
            elif self._state.state == CircuitState.CLOSED:
                # Reset failure count en estado normal
                self._state.failure_count = 0

    async def _on_failure(self):
        """Callback cuando una operación falla"""
        async with self._state.lock:
            CIRCUIT_BREAKER_FAILURES.labels(circuit_name=self.name).inc()
            
            self._state.failure_count += 1
            self._state.last_failure_time = time.monotonic()
            
            if self._state.state == CircuitState.HALF_OPEN:
                # Fallo en half-open, volver a abrir
                await self._transition_to(CircuitState.OPEN)
                self._state.success_count = 0
            
            elif self._state.state == CircuitState.CLOSED:
                # Verificar si alcanzamos threshold
                if self._state.failure_count >= self.config.failure_threshold:
                    await self._transition_to(CircuitState.OPEN)

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecuta una función protegida por el circuit breaker.
        
        Args:
            func: Función async a ejecutar
            *args, **kwargs: Argumentos para la función
            
        Returns:
            Resultado de la función
            
        Raises:
            CircuitBreakerOpen: Si el circuit breaker está abierto
            Exception: Cualquier excepción de la función original
        """
        await self._check_state()
        
        # Rechazar si está OPEN
        if self._state.state == CircuitState.OPEN:
            CIRCUIT_BREAKER_REJECTIONS.labels(circuit_name=self.name).inc()
            logger.warning(
                "circuit_breaker_rejected_call",
                circuit_name=self.name,
                failure_count=self._state.failure_count
            )
            raise CircuitBreakerOpen(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service unavailable after {self._state.failure_count} failures."
            )
        
        # Intentar ejecutar
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        
        except self.config.expected_exception as e:
            await self._on_failure()
            raise


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 2
):
    """
    Decorador para aplicar circuit breaker a una función async.
    
    Args:
        name: Nombre del circuit breaker
        failure_threshold: Fallos consecutivos para abrir
        recovery_timeout: Segundos antes de probar half-open
        success_threshold: Éxitos en half-open para cerrar
        
    Example:
        @circuit_breaker(name="whatsapp_api", failure_threshold=3)
        async def send_message():
            # código que puede fallar
            pass
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        success_threshold=success_threshold
    )
    breaker = CircuitBreaker(name, config)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            return await breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator
