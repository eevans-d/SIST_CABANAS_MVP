from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional
import secrets

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=0, env="DB_MAX_OVERFLOW")
    
    # Redis
    REDIS_URL: str = Field(..., env="REDIS_URL")
    
    # WhatsApp
    WHATSAPP_ACCESS_TOKEN: str = Field(..., env="WHATSAPP_ACCESS_TOKEN")
    WHATSAPP_VERIFY_TOKEN: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="WHATSAPP_VERIFY_TOKEN")
    WHATSAPP_APP_SECRET: str = Field(..., env="WHATSAPP_APP_SECRET")
    WHATSAPP_PHONE_ID: str = Field(..., env="WHATSAPP_PHONE_ID")
    
    # Mercado Pago
    MERCADOPAGO_ACCESS_TOKEN: str = Field(..., env="MERCADOPAGO_ACCESS_TOKEN")
    MERCADOPAGO_WEBHOOK_SECRET: Optional[str] = Field(None, env="MERCADOPAGO_WEBHOOK_SECRET")
    
    # Application
    BASE_URL: str = Field(..., env="BASE_URL")
    JWT_SECRET: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="JWT_SECRET")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION_HOURS: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    JOB_EXPIRATION_INTERVAL_SECONDS: int = Field(default=60, env="JOB_EXPIRATION_INTERVAL_SECONDS")
    
    # iCal
    ICS_SALT: str = Field(default_factory=lambda: secrets.token_hex(16), env="ICS_SALT")
    
    # Security
    ALLOWED_ORIGINS: str = Field(default="http://localhost:3000", env="ALLOWED_ORIGINS")
    
    # Domain
    DOMAIN: str = Field(default="localhost", env="DOMAIN")
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        # Convert to asyncpg if needed
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://")
        return v
    
    @validator("REDIS_URL")
    def validate_redis_url(cls, v):
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must be a Redis URL")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Singleton instance
_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings