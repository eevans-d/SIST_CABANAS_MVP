"""Conversation State Manager - Redis-based stateful conversation tracking.

Gestiona el contexto de conversación de usuarios a través de Redis con TTL automático.
Diseñado para flujos multi-paso en WhatsApp interactive buttons sin persistencia en DB.

Filosofía:
- Estado efímero (TTL 30 min, renovable)
- Schema-less (JSON flexible)
- Fail-safe (contexto perdido = reinicio conversación)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import redis.asyncio as redis
import structlog
from app.core.redis import get_redis_pool
from prometheus_client import Counter, Histogram

logger = structlog.get_logger()

# Métricas
CONVERSATION_STATE_SET = Counter(
    "conversation_state_set_total",
    "Total de operaciones set_user_context",
    ["status"],
)

CONVERSATION_STATE_GET = Counter(
    "conversation_state_get_total",
    "Total de operaciones get_user_context",
    ["status"],
)

CONVERSATION_STATE_UPDATE = Counter(
    "conversation_state_update_total",
    "Total de operaciones update_user_context",
    ["status"],
)

CONVERSATION_STATE_DELETE = Counter(
    "conversation_state_delete_total",
    "Total de operaciones delete_user_context",
    ["status"],
)

CONVERSATION_STATE_TTL_REMAINING = Histogram(
    "conversation_state_ttl_remaining_seconds",
    "TTL restante del contexto al momento de get",
    buckets=[60, 300, 600, 900, 1200, 1500, 1800],
)

# Configuración
CONTEXT_TTL_SECONDS = 1800  # 30 minutos
CONTEXT_KEY_PREFIX = "user_context"


def _make_key(user_id: str) -> str:
    """Generar llave Redis para contexto de usuario."""
    return f"{CONTEXT_KEY_PREFIX}:{user_id}"


async def set_user_context(
    user_id: str,
    context: Dict[str, Any],
    ttl_seconds: int = CONTEXT_TTL_SECONDS,
) -> bool:
    """Guardar contexto completo de usuario en Redis.

    Args:
        user_id: Identificador del usuario (teléfono WhatsApp, email, etc.)
        context: Diccionario con datos del contexto. Recomendado:
            - current_step: str (ej: "awaiting_dates", "selecting_accommodation")
            - selected_dates: dict con check_in/check_out
            - accommodation_id: int
            - guests_count: int
            - temp_data: dict con datos transitorios
        ttl_seconds: Tiempo de vida en segundos (default 30 min)

    Returns:
        bool: True si se guardó exitosamente, False en caso de error

    Example:
        >>> await set_user_context(
        ...     "+5491112345678",
        ...     {
        ...         "current_step": "selecting_accommodation",
        ...         "selected_dates": {"check_in": "2025-10-20", "check_out": "2025-10-22"},
        ...         "guests_count": 2,
        ...     }
        ... )
    """
    try:
        pool = get_redis_pool()
        redis_client = redis.Redis(connection_pool=pool)

        key = _make_key(user_id)
        # Añadir timestamp para auditoría
        context["_updated_at"] = datetime.now(timezone.utc).isoformat()
        value = json.dumps(context, default=str)

        # SET con EX (expire)
        result = await redis_client.set(key, value, ex=ttl_seconds)

        if result:
            CONVERSATION_STATE_SET.labels(status="success").inc()
            logger.debug(
                "conversation_state_set",
                user_id=user_id,
                ttl_seconds=ttl_seconds,
                keys=list(context.keys()),
            )
        else:
            CONVERSATION_STATE_SET.labels(status="failed").inc()
            logger.warning("conversation_state_set_failed", user_id=user_id)

        await redis_client.aclose()
        return bool(result)

    except Exception as e:
        CONVERSATION_STATE_SET.labels(status="error").inc()
        logger.error(
            "conversation_state_set_error",
            user_id=user_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        return False


async def get_user_context(user_id: str) -> Optional[Dict[str, Any]]:
    """Recuperar contexto de usuario desde Redis.

    Args:
        user_id: Identificador del usuario

    Returns:
        Dict con contexto si existe, None si no existe o expiró

    Example:
        >>> context = await get_user_context("+5491112345678")
        >>> if context:
        ...     print(f"Usuario en paso: {context.get('current_step')}")
        ... else:
        ...     print("Conversación nueva o expirada")
    """
    try:
        pool = get_redis_pool()
        redis_client = redis.Redis(connection_pool=pool)

        key = _make_key(user_id)
        data = await redis_client.get(key)

        if data:
            # Registrar TTL restante para métricas
            ttl = await redis_client.ttl(key)
            if ttl > 0:
                CONVERSATION_STATE_TTL_REMAINING.observe(ttl)

            context = json.loads(data)
            CONVERSATION_STATE_GET.labels(status="found").inc()
            logger.debug(
                "conversation_state_get",
                user_id=user_id,
                ttl_remaining=ttl,
                keys=list(context.keys()),
            )
            await redis_client.aclose()
            return context
        else:
            CONVERSATION_STATE_GET.labels(status="not_found").inc()
            logger.debug("conversation_state_not_found", user_id=user_id)
            await redis_client.aclose()
            return None

    except json.JSONDecodeError as e:
        CONVERSATION_STATE_GET.labels(status="decode_error").inc()
        logger.error("conversation_state_json_decode_error", user_id=user_id, error=str(e))
        return None

    except Exception as e:
        CONVERSATION_STATE_GET.labels(status="error").inc()
        logger.error(
            "conversation_state_get_error",
            user_id=user_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        return None


async def update_user_context(
    user_id: str,
    updates: Dict[str, Any],
    reset_ttl: bool = True,
) -> bool:
    """Actualizar parcialmente el contexto (merge con datos existentes).

    Args:
        user_id: Identificador del usuario
        updates: Diccionario con campos a actualizar/agregar
        reset_ttl: Si True, reinicia el TTL a 30 min (default). Si False, mantiene TTL existente.

    Returns:
        bool: True si se actualizó exitosamente, False en caso de error

    Example:
        >>> await update_user_context(
        ...     "+5491112345678",
        ...     {"accommodation_id": 5, "current_step": "confirming"}
        ... )
    """
    try:
        # Obtener contexto actual
        context = await get_user_context(user_id) or {}

        # Merge updates
        context.update(updates)

        # Guardar con TTL renovado (o mantener el existente)
        ttl = CONTEXT_TTL_SECONDS if reset_ttl else -1

        # Si reset_ttl=False, obtener TTL actual
        if not reset_ttl:
            pool = get_redis_pool()
            redis_client = redis.Redis(connection_pool=pool)
            key = _make_key(user_id)
            current_ttl = await redis_client.ttl(key)
            await redis_client.aclose()
            ttl = max(current_ttl, 60) if current_ttl > 0 else CONTEXT_TTL_SECONDS

        result = await set_user_context(user_id, context, ttl_seconds=ttl)

        if result:
            CONVERSATION_STATE_UPDATE.labels(status="success").inc()
        else:
            CONVERSATION_STATE_UPDATE.labels(status="failed").inc()

        return result

    except Exception as e:
        CONVERSATION_STATE_UPDATE.labels(status="error").inc()
        logger.error(
            "conversation_state_update_error",
            user_id=user_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        return False


async def delete_user_context(user_id: str) -> bool:
    """Eliminar contexto de usuario (reset conversación).

    Args:
        user_id: Identificador del usuario

    Returns:
        bool: True si se eliminó (o no existía), False en caso de error

    Example:
        >>> await delete_user_context("+5491112345678")  # Reset conversación
    """
    try:
        pool = get_redis_pool()
        redis_client = redis.Redis(connection_pool=pool)

        key = _make_key(user_id)
        result = await redis_client.delete(key)

        CONVERSATION_STATE_DELETE.labels(status="success").inc()
        logger.debug("conversation_state_deleted", user_id=user_id, existed=bool(result))
        await redis_client.aclose()
        return True

    except Exception as e:
        CONVERSATION_STATE_DELETE.labels(status="error").inc()
        logger.error(
            "conversation_state_delete_error",
            user_id=user_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        return False


async def get_ttl_remaining(user_id: str) -> int:
    """Obtener TTL restante del contexto en segundos.

    Args:
        user_id: Identificador del usuario

    Returns:
        int: Segundos restantes, -2 si no existe, -1 si no tiene expire, 0 si ya expiró
    """
    try:
        pool = get_redis_pool()
        redis_client = redis.Redis(connection_pool=pool)

        key = _make_key(user_id)
        ttl = await redis_client.ttl(key)
        await redis_client.aclose()
        return ttl

    except Exception as e:
        logger.error("conversation_state_ttl_error", user_id=user_id, error=str(e))
        return -2
