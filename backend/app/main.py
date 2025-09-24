from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import uuid
from datetime import datetime

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.routers import health
from app.routers import reservations as reservations_router

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
    
    yield
    
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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    with structlog.contextvars.bind_contextvars(request_id=request_id):
        start_time = datetime.utcnow()
        response = await call_next(request)
        
        # Log request
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2)
        )
        
        response.headers["X-Request-ID"] = request_id
        return response

# Exception handlers
@app.exception_handler(400)
async def bad_request_handler(request: Request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Bad Request", "detail": str(exc)}
    )

@app.exception_handler(403)
async def forbidden_handler(request: Request, exc):
    return JSONResponse(
        status_code=403,
        content={"error": "Forbidden", "detail": "Access denied"}
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "detail": "Resource not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error("internal_server_error", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred"}
    )

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(reservations_router.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Sistema de Reservas API", "version": "1.0.0"}