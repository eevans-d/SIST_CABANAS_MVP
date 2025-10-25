"""Email Service - MVP placeholder for notifications."""

from typing import Optional

import structlog
from prometheus_client import Counter

logger = structlog.get_logger()

EMAIL_SENT = Counter("email_sent_total", "Emails sent", ["type", "status"])


class EmailService:
    """Email service placeholder for MVP."""

    def __init__(self):
        self.enabled = False

    async def send_prereservation_confirmation(
        self,
        guest_email: str,
        guest_name: str,
        reservation_code: str,
        accommodation_name: str,
        check_in: str,
        check_out: str,
        guests_count: int,
        total_amount: float,
        expires_at: str,
    ) -> bool:
        """Send pre-reservation confirmation."""
        logger.info(
            "email_prereservation",
            email=guest_email[:15] + "...",
            code=reservation_code,
        )
        EMAIL_SENT.labels(type="prereservation", status="logged").inc()
        return True

    async def send_reservation_confirmed(
        self,
        guest_email: str,
        guest_name: str,
        reservation_code: str,
        accommodation_name: str,
        check_in: str,
        check_out: str,
        guests_count: int,
        total_amount: float,
        accommodation_address: Optional[str] = None,
        check_in_instructions: Optional[str] = None,
    ) -> bool:
        """Send reservation confirmed."""
        logger.info("email_confirmed", email=guest_email[:15] + "...", code=reservation_code)
        EMAIL_SENT.labels(type="confirmed", status="logged").inc()
        return True

    async def send_reservation_expired(
        self,
        guest_email: str,
        guest_name: str,
        reservation_code: str,
        accommodation_name: str,
        check_in: str,
        check_out: str,
    ) -> bool:
        """Send reservation expired."""
        logger.info("email_expired", email=guest_email[:15] + "...", code=reservation_code)
        EMAIL_SENT.labels(type="expired", status="logged").inc()
        return True


email_service = EmailService()
