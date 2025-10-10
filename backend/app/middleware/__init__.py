"""
Middleware personalizado para el sistema de reservas.

Contiene:
- IdempotencyMiddleware: Prevención de procesamiento duplicado
"""

from .idempotency import IdempotencyMiddleware

__all__ = [
    "IdempotencyMiddleware",
]
