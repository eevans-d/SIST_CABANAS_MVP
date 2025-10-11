"""
Modelo para manejo de idempotencia de requests.

Permite detectar y evitar el procesamiento duplicado de webhooks y requests críticos,
especialmente importante para webhooks de MercadoPago y WhatsApp.
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, TimestampMixin


class IdempotencyKey(Base, TimestampMixin):
    """
    Almacena claves de idempotencia para prevenir procesamiento duplicado.

    Cada request crítico (webhooks, pagos) genera una clave única basada en:
    - Contenido del request (hash SHA-256)
    - Headers relevantes (opcional)
    - Endpoint específico

    TTL: 48 horas (configurable)
    """

    __tablename__ = "idempotency_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Clave única de idempotencia (SHA-256 del contenido)
    key = Column(String(64), unique=True, nullable=False, index=True)

    # Endpoint donde se originó el request
    endpoint = Column(String(255), nullable=False, index=True)

    # Método HTTP del request original
    method = Column(String(10), nullable=False)

    # Hash del contenido completo del request (body + headers relevantes)
    content_hash = Column(String(64), nullable=False)

    # Response status code del request original
    response_status = Column(Integer, nullable=True)

    # Response body del request original (para casos exitosos)
    response_body = Column(Text, nullable=True)

    # Timestamp de expiración (TTL)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Metadatos adicionales (JSON string)
    extra_metadata = Column(Text, nullable=True)

    def __init__(self, **kwargs):
        """Inicializa una nueva clave de idempotencia con TTL por defecto de 48h."""
        super().__init__(**kwargs)
        if "expires_at" not in kwargs:
            # TTL por defecto: 48 horas
            self.expires_at = datetime.now(UTC) + timedelta(hours=48)

    @classmethod
    def create_key(cls, endpoint: str, method: str, content_hash: str, ttl_hours: int = 48) -> str:
        """
        Genera clave de idempotencia única.

        Args:
            endpoint: Endpoint del request (/api/v1/webhooks/mercadopago)
            method: Método HTTP (POST, GET, etc.)
            content_hash: Hash SHA-256 del contenido
            ttl_hours: Tiempo de vida en horas

        Returns:
            Clave única de idempotencia
        """
        import hashlib

        # Combinar elementos para generar clave única
        key_content = f"{method}:{endpoint}:{content_hash}"
        return hashlib.sha256(key_content.encode()).hexdigest()

    def is_expired(self) -> bool:
        """Verifica si la clave ha expirado."""
        from datetime import UTC, datetime

        # Obtener el valor actual de expires_at
        expires_at_value = getattr(self, "expires_at", None)
        if expires_at_value is None:
            return True  # Si no hay fecha de expiración, considerarlo expirado

        # Para instancias cargadas desde DB, expires_at será datetime
        if isinstance(expires_at_value, datetime):
            return datetime.now(UTC) > expires_at_value

        return False  # Si no es datetime, no está expirado (caso edge)

    def __repr__(self):
        """Representación string del modelo."""
        return f"<IdempotencyKey(key='{self.key[:16]}...', endpoint='{self.endpoint}')>"


# Índices para optimizar queries frecuentes
Index("idx_idempotency_key_endpoint", "key", "endpoint", mysql_length={"key": 16})
Index("idx_idempotency_expires", "expires_at")
