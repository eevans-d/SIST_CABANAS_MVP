from __future__ import annotations

from decimal import Decimal
import uuid
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Date, DateTime, Text,
    NUMERIC, CheckConstraint, Index, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import ReservationStatus, PaymentStatus


class Reservation(Base, TimestampMixin):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)

    accommodation_id = Column(Integer, ForeignKey("accommodations.id", ondelete="CASCADE"), nullable=False, index=True)

    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)

    guest_name = Column(String(100), nullable=False)
    guest_phone = Column(String(20), nullable=False, index=True)
    guest_email = Column(String(100))
    guest_document = Column(String(20))
    guests_count = Column(Integer, nullable=False)

    nights = Column(Integer, nullable=False)
    base_price_per_night = Column(NUMERIC(12, 2), nullable=False)
    total_price = Column(NUMERIC(12, 2), nullable=False)
    deposit_percentage = Column(Integer, nullable=False, default=30)
    deposit_amount = Column(NUMERIC(12, 2), nullable=False)
    paid_amount = Column(NUMERIC(12, 2), nullable=False, default=Decimal('0'))

    reservation_status = Column(String(20), nullable=False, default=ReservationStatus.PRE_RESERVED.value)
    payment_status = Column(String(20), nullable=False, default=PaymentStatus.PENDING.value)

    channel_source = Column(String(50))

    expires_at = Column(DateTime(timezone=True))
    extended_once = Column(Boolean, default=False)
    lock_value = Column(String(36))

    confirmed_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    internal_notes = Column(Text)
    special_requests = Column(Text)

    accommodation = relationship("Accommodation", backref="reservations")

    __table_args__ = (
        CheckConstraint('check_in < check_out', name='ck_reservation_dates'),
        CheckConstraint('guests_count > 0', name='ck_guests_positive'),
        CheckConstraint('total_price >= 0', name='ck_total_price_positive'),
        Index('idx_reservation_dates', 'accommodation_id', 'check_in', 'check_out'),
        Index('idx_reservation_expires', 'expires_at'),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Reservation code={self.code} acc={self.accommodation_id}>"
