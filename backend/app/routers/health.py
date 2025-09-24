from fastapi import APIRouter, Depends
from typing import Dict
from datetime import datetime
import structlog

from app.core.database import check_database_health
from app.core.redis import check_redis_health

router = APIRouter()
logger = structlog.get_logger()

@router.get("/healthz")
async def health_check() -> Dict:
    """
    Comprehensive health check endpoint.
    Returns system status and component health.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
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
    
    # Check memory
    import psutil
    memory = psutil.virtual_memory()
    health_status["checks"]["memory"] = {
        "status": "ok" if memory.percent < 90 else "warning",
        "used_percent": memory.percent
    }
    
    # Determine overall status
    for check in health_status["checks"].values():
        if check["status"] == "error":
            health_status["status"] = "unhealthy"
            break
        elif check["status"] == "warning":
            health_status["status"] = "degraded"
    
    return health_status