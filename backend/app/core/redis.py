import redis.asyncio as redis
from typing import Optional
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Redis connection pool
redis_pool: Optional[redis.ConnectionPool] = None

def get_redis_pool() -> redis.ConnectionPool:
    """Get or create Redis connection pool"""
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=50,
            decode_responses=True,
        )
    return redis_pool

async def get_redis() -> redis.Redis:
    """Get Redis client for dependency injection"""
    pool = get_redis_pool()
    client = redis.Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.close()

# Utility functions for locks
async def acquire_lock(
    redis_client: redis.Redis,
    key: str,
    value: str,
    ttl: int = 1800
) -> bool:
    """Acquire a distributed lock with TTL"""
    return await redis_client.set(key, value, nx=True, ex=ttl)

async def release_lock(
    redis_client: redis.Redis,
    key: str,
    value: str
) -> bool:
    """Release a lock only if we own it"""
    lua_script = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    else
        return 0
    end
    """
    result = await redis_client.eval(lua_script, 1, key, value)
    return bool(result)

async def extend_lock(
    redis_client: redis.Redis,
    key: str,
    value: str,
    ttl: int = 900
) -> bool:
    """Extend a lock TTL only if we own it"""
    lua_script = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("EXPIRE", KEYS[1], ARGV[2])
    else
        return 0
    end
    """
    result = await redis_client.eval(lua_script, 1, key, value, ttl)
    return bool(result)

# Health check function
async def check_redis_health() -> dict:
    """Check Redis connectivity and return status"""
    try:
        pool = get_redis_pool()
        client = redis.Redis(connection_pool=pool)
        await client.ping()
        info = await client.info()
        await client.close()
        return {
            "status": "ok",
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown")
        }
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        return {"status": "error", "error": str(e)}