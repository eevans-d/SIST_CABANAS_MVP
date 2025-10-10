"""
Middleware de idempotencia para prevenir procesamiento duplicado de requests.

Especialmente crítico para webhooks de MercadoPago y WhatsApp donde la duplicación
puede causar problemas graves (doble cobro, doble reserva, etc.).
"""

import hashlib
import json
import logging
import time
from typing import Any, Awaitable, Callable, Dict, Optional

from app.core.config import get_settings
from app.core.database import async_session_maker
from app.metrics import (
    IDEMPOTENCY_CACHE_HITS,
    IDEMPOTENCY_CACHE_MISSES,
    IDEMPOTENCY_ERRORS,
    IDEMPOTENCY_KEYS_CREATED,
    IDEMPOTENCY_KEYS_EXPIRED,
    IDEMPOTENCY_PROCESSING_TIME,
)
from app.models.idempotency import IdempotencyKey
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)
settings = get_settings()


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware que implementa idempotencia para endpoints críticos.

    Endpoints que requieren idempotencia:
    - /api/v1/webhooks/mercadopago
    - /api/v1/webhooks/whatsapp
    - /api/v1/reservations (POST)
    - /api/v1/payments (POST)

    Funcionamiento:
    1. Genera hash del contenido del request (body + headers relevantes)
    2. Verifica si existe clave de idempotencia para el mismo contenido
    3. Si existe y no ha expirado: retorna respuesta almacenada
    4. Si no existe: procesa request y almacena resultado
    5. Si existe pero expiró: elimina registro viejo y procesa nuevo request
    """

    def __init__(
        self,
        app,
        enabled_endpoints: Optional[list[str]] = None,
        ttl_hours: int = 48,
        include_headers: Optional[list[str]] = None,
    ):
        super().__init__(app)
        self.ttl_hours = ttl_hours

        # Endpoints que requieren idempotencia (defaults críticos)
        self.enabled_endpoints = enabled_endpoints or [
            "/api/v1/webhooks/mercadopago",
            "/api/v1/webhooks/whatsapp",
            "/api/v1/reservations",
            "/api/v1/payments",
        ]

        # Headers relevantes para generar hash (además del body)
        self.include_headers = include_headers or [
            "x-hub-signature-256",  # WhatsApp
            "x-signature",  # MercadoPago
            "content-type",
            "user-agent",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Procesa request con idempotencia si es necesario.

        Args:
            request: Request FastAPI
            call_next: Siguiente middleware en la cadena

        Returns:
            Response: Respuesta del request (nueva o cacheada)
        """
        # Verificar si endpoint requiere idempotencia
        if not self._should_apply_idempotency(request):
            return await call_next(request)

        # Solo aplicar a métodos POST/PUT/PATCH
        if request.method not in ["POST", "PUT", "PATCH"]:
            return await call_next(request)

        start_time = time.monotonic()

        try:
            # Generar hash del contenido del request
            content_hash = await self._generate_content_hash(request)

            # Generar clave de idempotencia
            idempotency_key = IdempotencyKey.create_key(
                endpoint=str(request.url.path),
                method=request.method,
                content_hash=content_hash,
                ttl_hours=self.ttl_hours,
            )

            # Verificar si ya existe la clave
            existing_response = await self._get_existing_response(idempotency_key)
            if existing_response:
                processing_time = time.monotonic() - start_time

                # Métricas de cache hit
                IDEMPOTENCY_CACHE_HITS.labels(
                    endpoint=request.url.path, method=request.method
                ).inc()

                IDEMPOTENCY_PROCESSING_TIME.labels(
                    endpoint=request.url.path, cache_result="hit"
                ).observe(processing_time)

                logger.info(
                    "idempotency_cache_hit",
                    extra={
                        "idempotency_key": idempotency_key[:16] + "...",
                        "endpoint": request.url.path,
                        "method": request.method,
                        "processing_time_ms": round(processing_time * 1000),
                    },
                )
                return existing_response

            # Procesar request original
            response = await call_next(request)

            # Almacenar resultado para futuros requests idénticos
            await self._store_response(idempotency_key, request, response, content_hash)

            processing_time = time.monotonic() - start_time

            # Métricas de cache miss
            IDEMPOTENCY_CACHE_MISSES.labels(endpoint=request.url.path, method=request.method).inc()

            IDEMPOTENCY_PROCESSING_TIME.labels(
                endpoint=request.url.path, cache_result="miss"
            ).observe(processing_time)

            logger.info(
                "idempotency_cache_miss",
                extra={
                    "idempotency_key": idempotency_key[:16] + "...",
                    "endpoint": request.url.path,
                    "method": request.method,
                    "response_status": response.status_code,
                    "processing_time_ms": round(processing_time * 1000),
                },
            )

            return response

        except Exception as e:
            processing_time = time.monotonic() - start_time

            # Métricas de error
            IDEMPOTENCY_ERRORS.labels(endpoint=request.url.path, error_type=type(e).__name__).inc()

            IDEMPOTENCY_PROCESSING_TIME.labels(
                endpoint=request.url.path, cache_result="error"
            ).observe(processing_time)

            logger.error(
                "idempotency_middleware_error",
                extra={
                    "endpoint": request.url.path,
                    "method": request.method,
                    "error": str(e),
                    "processing_time_ms": round(processing_time * 1000),
                },
            )
            # En caso de error, procesar request normalmente (fail-open)
            return await call_next(request)

    def _should_apply_idempotency(self, request: Request) -> bool:
        """Verifica si el endpoint requiere idempotencia."""
        endpoint = str(request.url.path)
        return any(endpoint.startswith(pattern) for pattern in self.enabled_endpoints)

    async def _generate_content_hash(self, request: Request) -> str:
        """
        Genera hash SHA-256 del contenido del request.

        Incluye:
        - Body completo del request
        - Headers relevantes especificados
        - Query parameters (si existen)

        Args:
            request: Request FastAPI

        Returns:
            Hash SHA-256 hexadecimal del contenido
        """
        # Leer body del request
        body = await request.body()

        # Construir string para hash
        hash_content = {
            "method": request.method,
            "path": str(request.url.path),
            "body": body.decode("utf-8", errors="ignore") if body else "",
            "query_params": dict(request.query_params),
            "headers": {},
        }

        # Añadir headers relevantes
        for header_name in self.include_headers:
            if header_name.lower() in request.headers:
                hash_content["headers"][header_name] = request.headers[header_name]

        # Convertir a JSON string determinístico y hacer hash
        json_content = json.dumps(hash_content, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(json_content.encode()).hexdigest()

    async def _get_existing_response(self, idempotency_key: str) -> Optional[Response]:
        """
        Busca respuesta existente para la clave de idempotencia.

        Args:
            idempotency_key: Clave única de idempotencia

        Returns:
            Response existente o None si no existe/expiró
        """
        try:
            async with async_session_maker() as session:
                # Buscar clave existente
                stmt = select(IdempotencyKey).where(IdempotencyKey.key == idempotency_key)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if not existing:
                    return None

                # Verificar si ha expirado
                if existing.is_expired():
                    # Eliminar registro expirado
                    await session.delete(existing)
                    await session.commit()

                    # Métricas de expiración
                    IDEMPOTENCY_KEYS_EXPIRED.labels(endpoint=existing.endpoint).inc()

                    logger.info(
                        "idempotency_key_expired",
                        extra={
                            "idempotency_key": idempotency_key[:16] + "...",
                            "expired_at": existing.expires_at.isoformat(),
                        },
                    )
                    return None

                # Retornar respuesta almacenada
                if hasattr(existing, "response_status") and hasattr(existing, "response_body"):
                    response_status = getattr(existing, "response_status", None)
                    response_body = getattr(existing, "response_body", None)

                    if response_status:
                        try:
                            if response_body:
                                content = json.loads(response_body)
                            else:
                                content = {"cached": True}
                        except json.JSONDecodeError:
                            content = {"response": response_body or "cached"}

                        return JSONResponse(status_code=response_status, content=content)

                return None

        except Exception as e:
            logger.error(
                "idempotency_get_existing_error",
                extra={"error": str(e), "idempotency_key": idempotency_key[:16] + "..."},
            )
            return None

    async def _store_response(
        self, idempotency_key: str, request: Request, response: Response, content_hash: str
    ) -> None:
        """
        Almacena respuesta para futuros requests idénticos.

        Args:
            idempotency_key: Clave única de idempotencia
            request: Request original
            response: Response a almacenar
            content_hash: Hash del contenido del request
        """
        try:
            # Solo almacenar respuestas exitosas (2xx)
            if not (200 <= response.status_code < 300):
                return

            # Para simplificar, almacenar solo un placeholder JSON
            # En un entorno real, podrías implementar una estrategia más sofisticada
            response_body = json.dumps(
                {"cached": True, "timestamp": time.time(), "status": response.status_code}
            )

            async with async_session_maker() as session:
                # Crear registro de idempotencia
                idempotency_record = IdempotencyKey(
                    key=idempotency_key,
                    endpoint=str(request.url.path),
                    method=request.method,
                    content_hash=content_hash,
                    response_status=response.status_code,
                    response_body=response_body,
                    extra_metadata=json.dumps(
                        {
                            "content_type": response.headers.get("content-type"),
                            "stored_at": time.time(),
                        }
                    ),
                )

                session.add(idempotency_record)
                await session.commit()

                # Métricas de creación
                IDEMPOTENCY_KEYS_CREATED.labels(endpoint=str(request.url.path)).inc()

                logger.info(
                    "idempotency_response_stored",
                    extra={
                        "idempotency_key": idempotency_key[:16] + "...",
                        "endpoint": request.url.path,
                        "response_status": response.status_code,
                    },
                )

        except IntegrityError:
            # Clave duplicada - otro request simultáneo la creó primero
            logger.info(
                "idempotency_concurrent_creation",
                extra={"idempotency_key": idempotency_key[:16] + "..."},
            )
            # No es un error - simplemente otro thread/process creó la clave primero
        except Exception as e:
            logger.error(
                "idempotency_store_error",
                extra={
                    "error": str(e),
                    "idempotency_key": idempotency_key[:16] + "...",
                    "endpoint": request.url.path,
                },
            )
