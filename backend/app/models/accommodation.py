from __future__ import annotations

from decimal import Decimal
import uuid
from sqlalchemy import (
    Column, Integer, String, Boolean, Text, JSON, NUMERIC, Index, DateTime
)
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin


class Accommodation(Base, TimestampMixin):
    __tablename__ = "accommodations"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    name = Column(String(100), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # cabin | apartment | house | room
    capacity = Column(Integer, nullable=False)
    base_price = Column(NUMERIC(12, 2), nullable=False)
    weekend_multiplier = Column(NUMERIC(4, 2), nullable=False, default=Decimal('1.2'))
    description = Column(Text)

    amenities = Column(JSON, default=dict)
    photos = Column(JSON, default=list)
    location = Column(JSON, default=dict)
    policies = Column(JSON, default=dict)
    ical_export_token = Column(String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    ical_import_urls = Column(JSON, default=dict)
    # Última sincronización iCal (import)
    last_ical_sync_at = Column(DateTime(timezone=True), nullable=True)

    active = Column(Boolean, nullable=False, default=True, index=True)

    __table_args__ = (
        Index('idx_accommodation_type', 'type'),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Accommodation id={self.id} name={self.name!r}>"
