import structlog
import logging
import sys
from app.core.config import get_settings

settings = get_settings()


def setup_logging():
    """Configure structured logging for the application"""

    # Configure structlog with trace_id support
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,  # Incluye trace_id de contextvars
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            mask_sensitive_data,
            (
                structlog.processors.JSONRenderer()
                if settings.ENVIRONMENT == "production"
                else structlog.dev.ConsoleRenderer()
            ),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG,
    )

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def mask_sensitive_data(logger, method_name, event_dict):
    """Mask sensitive data in logs"""
    sensitive_fields = [
        "password",
        "token",
        "secret",
        "phone",
        "email",
        "guest_phone",
        "guest_email",
    ]

    for field in sensitive_fields:
        if field in event_dict:
            value = event_dict[field]
            if value and isinstance(value, str) and len(value) > 4:
                event_dict[field] = value[:4] + "****"

    return event_dict
