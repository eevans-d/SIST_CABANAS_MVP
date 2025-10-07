from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from pydantic_settings import SettingsConfigDict
from typing import Optional
import secrets
import os

class Settings(BaseSettings):
    model_config: SettingsConfigDict = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",  # Ignorar variables de entorno no utilizadas (p.ej. DB_NAME)
    }
    # Environment
    ENVIRONMENT: str = Field(default="development")
    
    # Database
    DATABASE_URL: str | None = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 5
    
    # Redis
    REDIS_URL: str | None = None
    REDIS_PASSWORD: str | None = None
    
    # WhatsApp
    WHATSAPP_ACCESS_TOKEN: str | None = None
    WHATSAPP_VERIFY_TOKEN: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    WHATSAPP_APP_SECRET: str | None = None
    WHATSAPP_PHONE_ID: str | None = None
    
    # Mercado Pago
    MERCADOPAGO_ACCESS_TOKEN: str | None = None
    MERCADOPAGO_WEBHOOK_SECRET: Optional[str] = None
    
    # Application
    BASE_URL: str | None = None
    JWT_SECRET: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JOB_EXPIRATION_INTERVAL_SECONDS: int = 60
    JOB_ICAL_INTERVAL_SECONDS: int = 300
    ICAL_SYNC_MAX_AGE_MINUTES: int = 20
    # Rate limit (simple)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # iCal
    ICS_SALT: str = Field(default_factory=lambda: secrets.token_hex(16))
    
    # Audio / NLU
    AUDIO_MODEL: str = "base"
    AUDIO_MIN_CONFIDENCE: float = 0.6

    # Security
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    # Domain
    DOMAIN: str = "localhost"

    # Email (SMTP)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASS: str | None = None
    SMTP_FROM: str | None = None

    # Admin (seguridad mínima)
    ADMIN_ALLOWED_EMAILS: str = "admin@example.com"  # coma-separado
    ADMIN_CSRF_SECRET: str = Field(default_factory=lambda: secrets.token_urlsafe(24))
    
    @field_validator("DATABASE_URL", mode="before")
    def validate_database_url(cls, v: str | None):
        if v is None:
            raise ValueError("DATABASE_URL is required")
        # Permitir SQLite (principalmente usado en tests / fallback import-time)
        if v.startswith("sqlite"):
            return v
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://")
        return v
    
    @field_validator("REDIS_URL", mode="before")
    def validate_redis_url(cls, v: str | None, info):
        if v is None:
            raise ValueError("REDIS_URL is required")
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must be a Redis URL")
            
        # Asegurar que la URL de Redis incluya la contraseña si está configurada
        password = info.data.get("REDIS_PASSWORD")
        if password and ":@" not in v and f":{password}@" not in v:
            # Insertar la contraseña en la URL si no está presente
            # Formato: redis://host:port/db -> redis://:password@host:port/db
            v = v.replace("redis://", f"redis://:{password}@")
            
        return v
    

# Singleton instance
_settings = None

def get_settings() -> Settings:
    """Devuelve Settings con cache controlado y auto-refresh.

    - Usa un singleton cached por proceso.
    - Si `DATABASE_URL` en entorno difiere del valor en cache, reconstruye el singleton.
    - Si la construcción falla (imports tempranos), usa un fallback mínimo.
    """
    global _settings
    env = os.getenv("ENVIRONMENT")
    current_db_url = os.getenv("DATABASE_URL")
    if _settings is not None and current_db_url and getattr(_settings, "DATABASE_URL", None) != current_db_url:
        _settings = None
    if _settings is None:
        try:
            _settings = Settings()
        except Exception:
            # Fallback mínimamente viable si variables no están listas (no recomendado fuera de tests)
            default_db = "postgresql+asyncpg://user:pass@localhost:5432/db"
            dummy = {
                "ENVIRONMENT": env or "development",
                "DATABASE_URL": current_db_url or default_db,
                "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                "WHATSAPP_ACCESS_TOKEN": os.getenv("WHATSAPP_ACCESS_TOKEN", "dummy"),
                "WHATSAPP_APP_SECRET": os.getenv("WHATSAPP_APP_SECRET", "dummy"),
                "WHATSAPP_PHONE_ID": os.getenv("WHATSAPP_PHONE_ID", "dummy"),
                "MERCADOPAGO_ACCESS_TOKEN": os.getenv("MERCADOPAGO_ACCESS_TOKEN", "dummy"),
                "BASE_URL": os.getenv("BASE_URL", "http://localhost"),
                "DOMAIN": os.getenv("DOMAIN", "localhost"),
                "DB_POOL_SIZE": int(os.getenv("DB_POOL_SIZE", "5")),
                "DB_MAX_OVERFLOW": int(os.getenv("DB_MAX_OVERFLOW", "0")),
                "JWT_EXPIRATION_HOURS": int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
                "JOB_EXPIRATION_INTERVAL_SECONDS": int(os.getenv("JOB_EXPIRATION_INTERVAL_SECONDS", "60")),
                "JOB_ICAL_INTERVAL_SECONDS": int(os.getenv("JOB_ICAL_INTERVAL_SECONDS", "300")),
                "AUDIO_MODEL": os.getenv("AUDIO_MODEL", "base"),
                "AUDIO_MIN_CONFIDENCE": float(os.getenv("AUDIO_MIN_CONFIDENCE", "0.6")),
            }
            _settings = Settings(**dummy)
    return _settings