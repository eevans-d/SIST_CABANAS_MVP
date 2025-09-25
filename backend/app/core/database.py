from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from sqlalchemy.pool import NullPool
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

engine_kwargs = {
    "echo": settings.ENVIRONMENT == "development",
    "pool_pre_ping": True,
}
if settings.ENVIRONMENT == "test":
    engine_kwargs["poolclass"] = NullPool  # type: ignore
else:
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE  # type: ignore
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW  # type: ignore

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Dependency for FastAPI
async def get_db():
    """Get database session for dependency injection"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Health check function
async def check_database_health() -> dict:
    """Check database connectivity and return status.

    Usa una sentencia text() explícita para SQLAlchemy 2.x evitando warnings / errores
    de objetos no ejecutables.
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
            return {"status": "ok", "latency_ms": 0}
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return {"status": "error", "error": str(e)}