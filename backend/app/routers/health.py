"""Health check endpoints para monitoreo de sistema."""
import os
import time
from datetime import datetime, timezone
from typing import Dict, Optional

import redis.asyncio as redis
import structlog
from app.core.config import get_settings
from app.core.database import get_db
from app.core.redis import get_redis_pool
from app.metrics import ICAL_LAST_SYNC_AGE_MIN
from app.models import Accommodation
from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()

router = APIRouter()
logger = structlog.get_logger()


@router.get("/healthz")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict:
    """Comprehensive health check endpoint with latency measurements.

    Returns system status and component health.
    """
    now = datetime.now(timezone.utc)
    health_status = {"status": "healthy", "timestamp": now.isoformat(), "checks": {}}

    # Check database with latency
    db_start = time.monotonic()
    try:
        await db.execute(text("SELECT 1"))
        db_latency_ms = round((time.monotonic() - db_start) * 1000, 2)
        db_status = "ok"
        if db_latency_ms > 500:
            db_status = "slow"
            health_status["status"] = "degraded"
        health_status["checks"]["database"] = {
            "status": db_status,
            "latency_ms": db_latency_ms,
        }
    except Exception as e:
        db_latency_ms = round((time.monotonic() - db_start) * 1000, 2)
        health_status["checks"]["database"] = {
            "status": "error",
            "latency_ms": db_latency_ms,
            "error": str(e),
        }
        health_status["status"] = "unhealthy"
        logger.error("health_db_error", error=str(e))

    # Check Redis with latency
    redis_start = time.monotonic()
    try:
        pool = get_redis_pool()
        redis_conn = redis.Redis(connection_pool=pool)
        await redis_conn.ping()
        redis_latency_ms = round((time.monotonic() - redis_start) * 1000, 2)
        redis_status = "ok"
        if redis_latency_ms > 200:
            redis_status = "slow"
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"

        # Info adicional de Redis
        info = await redis_conn.info()
        health_status["checks"]["redis"] = {
            "status": redis_status,
            "latency_ms": redis_latency_ms,
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
        }
        await redis_conn.close()
    except Exception as e:
        redis_latency_ms = round((time.monotonic() - redis_start) * 1000, 2)
        health_status["checks"]["redis"] = {
            "status": "error",
            "latency_ms": redis_latency_ms,
            "error": str(e),
        }
        health_status["status"] = "unhealthy"
        logger.error("health_redis_error", error=str(e))

    # Check disk space
    import shutil

    disk_usage = shutil.disk_usage("/")
    disk_free_percent = (disk_usage.free / disk_usage.total) * 100
    health_status["checks"]["disk"] = {
        "status": "ok" if disk_free_percent > 10 else "warning",
        "free_percent": round(disk_free_percent, 2),
    }

    # Memory check simplificado (sin psutil para MVP)
    # Placeholder: se podría integrar psutil más adelante si se agrega al requirements
    health_status["checks"]["memory"] = {
        "status": "ok",
        "used_percent": None,
        "detail": "not_collected",
    }

    # iCal last sync: tomamos el más reciente entre todos los accommodations
    try:
        stmt = (
            select(Accommodation.last_ical_sync_at)
            .order_by(Accommodation.last_ical_sync_at.desc())
            .limit(1)
        )
        res = await db.execute(stmt)
        last_ical_sync: Optional[datetime] = res.scalar_one_or_none()
    except Exception as e:
        last_ical_sync = None
        logger.warning("health_ical_query_failed", error=str(e))

    if last_ical_sync:
        # Normalizar tz: SQLite puede devolver naive aunque la columna sea timezone-aware
        if last_ical_sync.tzinfo is None:
            last_ical_sync = last_ical_sync.replace(tzinfo=timezone.utc)
        age_min = (now - last_ical_sync).total_seconds() / 60
        try:
            ICAL_LAST_SYNC_AGE_MIN.set(age_min)
        except Exception:  # nosec B110  # Metric failure non-critical
            pass
        max_ok = getattr(settings, "ICAL_SYNC_MAX_AGE_MINUTES", 20)
        health_status["checks"]["ical"] = {
            "status": (
                "ok" if age_min < max_ok else ("warning" if age_min < (max_ok + 10) else "error")
            ),
            "age_minutes": round(age_min, 2),
        }
    else:
        health_status["checks"]["ical"] = {
            "status": "warning",
            "age_minutes": None,
            "detail": "no_sync_data",
        }

    # Config flags (no hacemos llamadas externas costosas en health para mantener SLA)
    health_status["checks"]["whatsapp"] = {
        "status": (
            "ok" if settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_APP_SECRET else "error"
        )
    }
    health_status["checks"]["mercadopago"] = {
        "status": "ok" if settings.MERCADOPAGO_ACCESS_TOKEN else "error"
    }

    # Runtime details (no costosos): gunicorn workers y pool DB configurado
    try:
        gunicorn_workers = int(os.getenv("GUNICORN_WORKERS", "0")) or None
    except Exception:
        gunicorn_workers = None
    health_status["checks"]["runtime"] = {
        "status": "ok",
        "gunicorn_workers": gunicorn_workers,
        "db_pool_size": getattr(settings, "DB_POOL_SIZE", None),
        "db_max_overflow": getattr(settings, "DB_MAX_OVERFLOW", None),
    }

    # Determine overall status
    for check in health_status["checks"].values():
        if check["status"] == "error":
            health_status["status"] = "unhealthy"
            break
        elif check["status"] == "warning":
            health_status["status"] = "degraded"

    return health_status


@router.get("/readyz")
async def readiness_check() -> Dict:
    """Readiness check endpoint for Kubernetes/Docker health checks.

    Quick check that the app is ready to receive traffic.
    Does NOT check external dependencies.
    """
    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
