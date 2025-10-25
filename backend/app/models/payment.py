from __future__ import annotations

import uuid
from decimal import Decimal

from app.models.base import Base, TimestampMixin
from sqlalchemy import (
    NUMERIC,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    # Nullable para permitir notificaciones huérfanas (cuando no existe la reserva) en el MVP
    reservation_id = Column(
        Integer, ForeignKey("reservations.id", ondelete="CASCADE"), nullable=True, index=True
    )

    provider = Column(String(30), nullable=False, default="mercadopago")
    external_payment_id = Column(String(80), nullable=False)  # id notificación MP
    external_reference = Column(String(80), nullable=True)  # referencia nuestra (reservation code)

    status = Column(
        String(30), nullable=False, default="pending"
    )  # pending, approved, rejected, refunded
    amount = Column(NUMERIC(12, 2), nullable=False, default=Decimal("0"))
    currency = Column(String(10), nullable=False, default="ARS")

    event_first_received_at = Column(DateTime(timezone=True))
    event_last_received_at = Column(DateTime(timezone=True))
    events_count = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("external_payment_id", name="uq_payment_external_id"),
        Index("idx_payment_reservation", "reservation_id"),
        Index("idx_payment_external_ref", "external_reference"),
    )

    def __repr__(self):  # pragma: no cover
        return f"<Payment provider=MP external_id={self.external_payment_id}>"
