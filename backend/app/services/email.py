from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict
import structlog
from app.core.config import get_settings
from prometheus_client import Counter

try:  # opcional: usar plantillas si Jinja2 está instalada
    from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore
    import os

    TEMPLATES_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "templates", "email")
    )
    _jinja_env: Optional[Environment] = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        enable_async=False,
    )
except Exception:  # pragma: no cover
    _jinja_env = None

logger = structlog.get_logger()
settings = get_settings()

# Métricas de email
EMAIL_SENT = Counter(
    "email_sent_total", "Emails enviados", ["type"]
)  # type: pre_reserved|confirmed|expired|custom
EMAIL_FAILED = Counter("email_failed_total", "Emails fallidos", ["type"])  # idem


class EmailService:
    """Servicio simple de envío de emails vía SMTP.

    Requiere variables de entorno:
      - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
    """

    def __init__(self):
        self.host = settings.__dict__.get("SMTP_HOST")
        self.port = int(settings.__dict__.get("SMTP_PORT", 587))
        self.user = settings.__dict__.get("SMTP_USER")
        self.password = settings.__dict__.get("SMTP_PASS")
        self.sender = settings.__dict__.get("SMTP_FROM")

    def _ensure_config(self):
        if not all([self.host, self.port, self.user, self.password, self.sender]):
            raise RuntimeError(
                "SMTP configuration missing. Set SMTP_HOST/PORT/USER/PASS/FROM in environment"
            )

    def render(self, template_name: str, context: Dict) -> str:
        if _jinja_env is None:
            raise RuntimeError("Jinja2 is not available for template rendering")
        tpl = _jinja_env.get_template(template_name)
        return tpl.render(**context)

    def send_html(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        headers: Optional[Dict[str, str]] = None,
        email_type: str = "custom",
    ) -> bool:
        """Envía un email HTML. Retorna True si fue enviado."""
        self._ensure_config()
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = to_email
        if headers:
            for k, v in headers.items():
                msg[k] = v
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Reintentos con backoff exponencial (x3)
        delays = [0.5, 1.0, 2.0]
        last_error: Optional[Exception] = None
        for attempt, delay in enumerate(delays, start=1):
            try:
                with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                    server.starttls()
                    server.login(self.user, self.password)
                    server.sendmail(self.sender, [to_email], msg.as_string())
                logger.info("email_sent", to=to_email, subject=subject)
                try:
                    EMAIL_SENT.labels(type=email_type).inc()
                except Exception:
                    pass
                return True
            except Exception as e:  # pragma: no cover (se testea con mock)
                last_error = e
                logger.warning(
                    "email_send_retry", to=to_email, subject=subject, attempt=attempt, error=str(e)
                )
                try:
                    import time

                    time.sleep(delay)
                except Exception:
                    pass
        logger.error(
            "email_send_failed",
            to=to_email,
            subject=subject,
            error=str(last_error) if last_error else "unknown",
        )
        try:
            EMAIL_FAILED.labels(type=email_type).inc()
        except Exception:
            pass
        return False


email_service = EmailService()
