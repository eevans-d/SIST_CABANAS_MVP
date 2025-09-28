from fastapi import APIRouter, Depends
from typing import Dict, Optional
from datetime import datetime, timezone
import structlog

from app.core.database import check_database_health
from app.core.redis import check_redis_health
from app.core.config import get_settings
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Accommodation
from app.metrics import ICAL_LAST_SYNC_AGE_MIN
import os

settings = get_settings()

router = APIRouter()
logger = structlog.get_logger()

@router.get("/healthz")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict:
    """
    Comprehensive health check endpoint.
    Returns system status and component health.
    """
    now = datetime.now(timezone.utc)
    health_status = {
        "status": "healthy",
        "timestamp": now.isoformat(),
        "checks": {}
    }
    
    # Check database
    db_health = await check_database_health()
    health_status["checks"]["database"] = db_health
    
    # Check Redis
    redis_health = await check_redis_health()
    health_status["checks"]["redis"] = redis_health
    
    # Check disk space
    import shutil
    disk_usage = shutil.disk_usage("/")
    disk_free_percent = (disk_usage.free / disk_usage.total) * 100
    health_status["checks"]["disk"] = {
        "status": "ok" if disk_free_percent > 10 else "warning",
        "free_percent": round(disk_free_percent, 2)
    }
    
    # Memory check simplificado (sin psutil para MVP)
    # Placeholder: se podría integrar psutil más adelante si se agrega al requirements
    health_status["checks"]["memory"] = {"status": "ok", "used_percent": None, "detail": "not_collected"}
    
    # iCal last sync: tomamos el más reciente entre todos los accommodations
    try:
        stmt = select(Accommodation.last_ical_sync_at).order_by(Accommodation.last_ical_sync_at.desc()).limit(1)
        res = await db.execute(stmt)
        last_ical_sync: Optional[datetime] = res.scalar_one_or_none()
    except Exception as e:
        last_ical_sync = None
        logger.warning("health_ical_query_failed", error=str(e))

    if last_ical_sync:
        age_min = (now - last_ical_sync).total_seconds() / 60
        try:
            ICAL_LAST_SYNC_AGE_MIN.set(age_min)
        except Exception:
            pass
        max_ok = getattr(settings, "ICAL_SYNC_MAX_AGE_MINUTES", 20)
        health_status["checks"]["ical"] = {
            "status": "ok" if age_min < max_ok else ("warning" if age_min < (max_ok + 10) else "error"),
            "age_minutes": round(age_min, 2)
        }
    else:
        health_status["checks"]["ical"] = {"status": "warning", "age_minutes": None, "detail": "no_sync_data"}

    # Config flags (no hacemos llamadas externas costosas en health para mantener SLA)
    health_status["checks"]["whatsapp"] = {
        "status": "ok" if settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_APP_SECRET else "error"
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