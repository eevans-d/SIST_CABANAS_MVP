import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import structlog
from app.core.config import get_settings
from app.core.database import async_session_maker
from app.core.logging import setup_logging
from app.core.middleware import TraceIDMiddleware
from app.core.redis import get_redis_pool
from app.jobs.cleanup import expire_prereservations, send_prereservation_reminders
from app.jobs.import_ical import run_ical_sync
from app.routers import admin as admin_router
from app.routers import audio as audio_router
from app.routers import health
from app.routers import ical as ical_router
from app.routers import mercadopago as mercadopago_router
from app.routers import nlu as nlu_router
from app.routers import reservations as reservations_router
from app.routers import whatsapp as whatsapp_router
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

# Setup logging
setup_logging()
logger = structlog.get_logger()

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("application_startup", environment=settings.ENVIRONMENT)

    # Startup tasks
    from app.core.database import engine
    from app.models.base import Base

    # Create tables if not exist (development only)
    if settings.ENVIRONMENT == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Background tasks: expiración/reminders e import iCal
    stop_flag = False

    async def expiration_worker():
        interval = settings.JOB_EXPIRATION_INTERVAL_SECONDS
        logger.info("expiration_worker_start", interval_seconds=interval)
        while not stop_flag:
            try:
                async with async_session_maker() as session:
                    expired = await expire_prereservations(session)
                    if expired:
                        logger.info("pre_reservations_expired", count=expired)
                    reminders = await send_prereservation_reminders(session)
                    if reminders:
                        logger.info("pre_reservations_reminders_sent", count=reminders)
            except Exception as e:  # pragma: no cover
                logger.error("expiration_worker_error", error=str(e))
            finally:
                # dormir al final para que un ciclo rápido no haga drift si tarda > interval
                await asyncio.sleep(interval)
        logger.info("expiration_worker_stop")

    import asyncio

    task = asyncio.create_task(expiration_worker())

    async def ical_worker():
        interval = getattr(settings, "JOB_ICAL_INTERVAL_SECONDS", 300)
        logger.info("ical_worker_start", interval_seconds=interval)
        while not stop_flag:
            try:
                created = await run_ical_sync(logger)
                if created:
                    logger.info("ical_events_created", count=created)
            except Exception as e:  # pragma: no cover
                logger.error("ical_worker_error", error=str(e))
            finally:
                await asyncio.sleep(interval)
        logger.info("ical_worker_stop")

    task2 = asyncio.create_task(ical_worker())

    yield

    # Señal de parada y esperar
    stop_flag = True
    task.cancel()
    task2.cancel()
    try:
        await task
        await task2
    except Exception:  # nosec B110  # Task cancellation expected
        pass

    # Shutdown tasks
    logger.info("application_shutdown")
    await engine.dispose()


app = FastAPI(
    title="Sistema de Reservas API",
    description="API para gestión automatizada de reservas de alojamientos",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Prometheus instrumentation (simple MVP). Expondrá /metrics
Instrumentator().instrument(app).expose(app, include_in_schema=False, endpoint="/metrics")

# Trace ID middleware (PRIMERO para que esté en todos los logs)
app.add_middleware(TraceIDMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["*"] if settings.ENVIRONMENT == "development" else settings.ALLOWED_ORIGINS.split(",")
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limit middleware (simple per-IP + path, Redis-based). Bypass in development.
@app.middleware("http")
async def rate_limit(request: Request, call_next):
    """
    Middleware de rate limiting con observabilidad.

    - Fixed window counter en Redis
    - Métricas Prometheus de bloqueos y contadores actuales
    - Fail-open si Redis falla (no bloquea requests)
    - Bypass para endpoints de observabilidad
    """
    try:
        if not settings.RATE_LIMIT_ENABLED or settings.ENVIRONMENT == "development":
            return await call_next(request)

        path = request.url.path

        # No limitar healthz, readyz ni metrics para no afectar observabilidad
        if path in ("/api/v1/healthz", "/api/v1/readyz", "/metrics"):
            return await call_next(request)

        # Obtener IP del cliente (considerar proxy headers)
        client_ip = request.client.host if request.client else "unknown"
        if "X-Forwarded-For" in request.headers:
            # Tomar la primera IP de la cadena (cliente real)
            client_ip = request.headers["X-Forwarded-For"].split(",")[0].strip()

        # clave por IP + path, ventana deslizante básica (fixed window)
        key = f"ratelimit:{client_ip}:{path}"
        pool = get_redis_pool()
        import redis.asyncio as redis

        r = redis.Redis(connection_pool=pool)

        # Incrementar y setear TTL si clave nueva
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS)

        # Actualizar métrica de contador actual
        from app.metrics import RATE_LIMIT_CURRENT_COUNT

        RATE_LIMIT_CURRENT_COUNT.labels(client_ip=client_ip, path=path).set(count)

        # Verificar si se excedió el límite
        if count > settings.RATE_LIMIT_REQUESTS:
            from app.metrics import RATE_LIMIT_BLOCKED

            RATE_LIMIT_BLOCKED.labels(path=path, client_ip=client_ip).inc()
            logger.warning("rate_limited", ip=client_ip, path=path, count=int(count))
            return JSONResponse(status_code=429, content={"error": "Too Many Requests"})

        return await call_next(request)

    except Exception as e:  # pragma: no cover
        # Fail-open: no bloquear si redis falla
        from app.metrics import RATE_LIMIT_REDIS_ERRORS

        RATE_LIMIT_REDIS_ERRORS.inc()
        logger.error("rate_limit_error", error=str(e))
        return await call_next(request)


# Routers


# Request ID middleware (sin context manager erróneo)
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    try:
        # bind_contextvars no es context manager; simplemente establece valores
        import structlog.contextvars as ctxvars  # type: ignore

        ctxvars.bind_contextvars(request_id=request_id)
    except Exception:  # pragma: no cover  # nosec B110  # Contextvars optional
        pass
    # Usar datetime UTC aware para evitar deprecation warnings
    start_time = datetime.now(UTC)
    response = await call_next(request)
    duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2),
    )
    response.headers["X-Request-ID"] = request_id
    return response


# Exception handlers
@app.exception_handler(400)
async def bad_request_handler(request: Request, exc):
    return JSONResponse(status_code=400, content={"error": "Bad Request", "detail": str(exc)})


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc):
    # Preservar el detalle original si viene desde HTTPException (p.ej. firmas inválidas)
    detail = getattr(exc, "detail", None)
    if not detail:
        detail = "Access denied"
    return JSONResponse(status_code=403, content={"error": "Forbidden", "detail": detail})


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404, content={"error": "Not Found", "detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error("internal_server_error", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred"},
    )


# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(reservations_router.router, prefix="/api/v1")
app.include_router(mercadopago_router.router, prefix="/api/v1/mercadopago")
app.include_router(whatsapp_router.router, prefix="/api/v1")
app.include_router(ical_router.router, prefix="/api/v1")
app.include_router(audio_router.router, prefix="/api/v1")
app.include_router(admin_router.router, prefix="/api/v1")
app.include_router(nlu_router.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Sistema de Reservas API", "version": "1.0.0"}
