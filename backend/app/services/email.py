"""Email Service - Básico para MVP.""""""Email Service - Async SMTP notifications for reservations."""Email Service - SMTP notifications for reservations.



import structlog

from typing import Optional

from prometheus_client import CounterImplementa notificaciones automáticas vía SMTP para:Implementa notificaciones automáticas vía SMTP para:



logger = structlog.get_logger()- Pre-reserva creada (confirmación con código y expiración)- Pre-reserva creada (confirmación con código y expiración)



# Métricas simples- Reserva confirmada (datos check-in/check-out)- Reserva confirmada (datos check-in/check-out)

EMAIL_SENT_TOTAL = Counter("email_sent_total", "Emails enviados", ["type", "status"])

- Reserva expirada (recordatorio si hay email del huésped)- Reserva expirada (recordatorio si hay email del huésped)



class EmailService:- Recordatorios de pago (24h antes de expiración)- Recordatorios de pago (24h antes de expiración)

    """Email service básico para MVP."""



    def __init__(self):

        self.configured = False  # Para MVP, emails deshabilitadosCaracterísticas:Filosofía:



    async def send_prereservation_confirmation(- Async con aiosmtplib- SMTP-only (no IMAP reception en MVP)

        self,

        guest_email: str,- Templates Jinja2 responsive- Templates Jinja2 responsive

        guest_name: str,

        reservation_code: str,- Métricas Prometheus para observabilidad- Metrics Prometheus para observabilidad

        accommodation_name: str,

        check_in: str,- Fail-safe: error email no bloquea proceso principal- Fail-safe (error email no bloquea proceso)

        check_out: str,

        guests_count: int,- Retry con backoff exponencial"""

        total_amount: float,

        expires_at: str,"""

    ) -> bool:

        """Enviar confirmación de pre-reserva (placeholder MVP)."""from __future__ import annotations

        logger.info(

            "email_placeholder_prereservation",from __future__ import annotations

            guest_email=guest_email[:20] + "...",

            reservation_code=reservation_code,import structlog

            accommodation_name=accommodation_name,

        )import osfrom datetime import datetime, timezone

        EMAIL_SENT_TOTAL.labels(type="prereservation", status="placeholder").inc()

        return True  # Simular éxito para MVPimport structlogfrom decimal import Decimal



    async def send_reservation_confirmed(from datetime import datetime, timezonefrom email.mime.multipart import MIMEMultipart

        self,

        guest_email: str,from decimal import Decimalfrom email.mime.text import MIMEText

        guest_name: str,

        reservation_code: str,from email.mime.multipart import MIMEMultipartfrom typing import Any, Dict, Optional

        accommodation_name: str,

        check_in: str,from email.mime.text import MIMEText

        check_out: str,

        guests_count: int,from typing import Any, Dict, Optionalimport aiosmtplib

        total_amount: float,

        accommodation_address: Optional[str] = None,from jinja2 import Environment, FileSystemLoader, select_autoescape

        check_in_instructions: Optional[str] = None,

    ) -> bool:import aiosmtplibfrom prometheus_client import Counter, Histogram

        """Enviar confirmación de reserva (placeholder MVP)."""

        logger.info(from jinja2 import Environment, FileSystemLoader, select_autoescape

            "email_placeholder_confirmed",

            guest_email=guest_email[:20] + "...",from prometheus_client import Counter, Histogramfrom app.core.config import get_settings

            reservation_code=reservation_code,

        )

        EMAIL_SENT_TOTAL.labels(type="confirmed", status="placeholder").inc()

        return Truefrom app.core.config import get_settingslogger = structlog.get_logger()



    async def send_reservation_expired(settings = get_settings()

        self,

        guest_email: str,logger = structlog.get_logger()

        guest_name: str,

        reservation_code: str,settings = get_settings()# Métricas de email

        accommodation_name: str,

        check_in: str,EMAIL_SENT = Counter(

        check_out: str,

    ) -> bool:# Métricas Prometheus    "email_sent_total", "Emails enviados", ["type"]

        """Enviar notificación de expiración (placeholder MVP)."""

        logger.info(EMAIL_SENT_TOTAL = Counter()  # type: pre_reserved|confirmed|expired|custom

            "email_placeholder_expired",

            guest_email=guest_email[:20] + "...",    "email_sent_total",EMAIL_FAILED = Counter("email_failed_total", "Emails fallidos", ["type"])  # idem

            reservation_code=reservation_code,

        )    "Total de emails enviados",

        EMAIL_SENT_TOTAL.labels(type="expired", status="placeholder").inc()

        return True    ["type", "status"],



)class EmailService:

# Instancia global

email_service = EmailService()    """Servicio simple de envío de emails vía SMTP.

EMAIL_SEND_DURATION = Histogram(

    "email_send_duration_seconds",    Requiere variables de entorno:

    "Duración del envío de email",      - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM

    ["type"],    """

    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],

)    def __init__(self):

        self.host = settings.__dict__.get("SMTP_HOST")

EMAIL_TEMPLATE_RENDER_DURATION = Histogram(        self.port = int(settings.__dict__.get("SMTP_PORT", 587))

    "email_template_render_duration_seconds",        self.user = settings.__dict__.get("SMTP_USER")

    "Duración del render de template",        self.password = settings.__dict__.get("SMTP_PASS")

    ["template"],        self.sender = settings.__dict__.get("SMTP_FROM")

    buckets=[0.01, 0.05, 0.1, 0.2, 0.5],

)    def _ensure_config(self):

        if not all([self.host, self.port, self.user, self.password, self.sender]):

# Configuración Jinja2            raise RuntimeError(

TEMPLATES_DIR = os.path.abspath(                "SMTP configuration missing. Set SMTP_HOST/PORT/USER/PASS/FROM in environment"

    os.path.join(os.path.dirname(__file__), "..", "..", "templates", "email")            )

)

    def render(self, template_name: str, context: Dict) -> str:

try:        if _jinja_env is None:

    jinja_env = Environment(            raise RuntimeError("Jinja2 is not available for template rendering")

        loader=FileSystemLoader(TEMPLATES_DIR),        tpl = _jinja_env.get_template(template_name)

        autoescape=select_autoescape(["html", "xml"]),        return tpl.render(**context)

        trim_blocks=True,

        lstrip_blocks=True,    def send_html(

    )        self,

except Exception as e:        to_email: str,

    logger.warning("jinja_env_init_failed", error=str(e), templates_dir=TEMPLATES_DIR)        subject: str,

    jinja_env = None        html_body: str,

        headers: Optional[Dict[str, str]] = None,

        email_type: str = "custom",

class EmailService:    ) -> bool:

    """Service para envío de emails SMTP async."""        """Envía un email HTML. Retorna True si fue enviado."""

        self._ensure_config()

    def __init__(self):        msg = MIMEMultipart("alternative")

        self.smtp_host = settings.SMTP_HOST        msg["Subject"] = subject

        self.smtp_port = settings.SMTP_PORT        msg["From"] = self.sender

        self.smtp_user = settings.SMTP_USER        msg["To"] = to_email

        self.smtp_pass = settings.SMTP_PASS        if headers:

        self.smtp_from = settings.SMTP_FROM            for k, v in headers.items():

        self.smtp_use_tls = getattr(settings, "SMTP_USE_TLS", True)                msg[k] = v

        msg.attach(MIMEText(html_body, "html", "utf-8"))

    async def send_prereservation_confirmation(

        self,        # Reintentos con backoff exponencial (x3)

        guest_email: str,        delays = [0.5, 1.0, 2.0]

        guest_name: str,        last_error: Optional[Exception] = None

        reservation_code: str,        for attempt, delay in enumerate(delays, start=1):

        accommodation_name: str,            try:

        check_in: str,                with smtplib.SMTP(self.host, self.port, timeout=10) as server:

        check_out: str,                    server.starttls()

        guests_count: int,                    server.login(self.user, self.password)

        total_amount: Decimal,                    server.sendmail(self.sender, [to_email], msg.as_string())

        expires_at: datetime,                logger.info("email_sent", to=to_email, subject=subject)

    ) -> bool:                try:

        """Enviar email de confirmación de pre-reserva.                    EMAIL_SENT.labels(type=email_type).inc()

                except Exception:

        Args:                    pass

            guest_email: Email del huésped                return True

            guest_name: Nombre del huésped            except Exception as e:  # pragma: no cover (se testea con mock)

            reservation_code: Código de reserva único                last_error = e

            accommodation_name: Nombre del alojamiento                logger.warning(

            check_in: Fecha check-in (ISO string)                    "email_send_retry", to=to_email, subject=subject, attempt=attempt, error=str(e)

            check_out: Fecha check-out (ISO string)                )

            guests_count: Cantidad de huéspedes                try:

            total_amount: Monto total (Decimal)                    import time

            expires_at: Datetime de expiración

                    time.sleep(delay)

        Returns:                except Exception:

            bool: True si se envió exitosamente, False en caso contrario                    pass

        """        logger.error(

        template_data = {            "email_send_failed",

            "guest_name": guest_name,            to=to_email,

            "reservation_code": reservation_code,            subject=subject,

            "accommodation_name": accommodation_name,            error=str(last_error) if last_error else "unknown",

            "check_in": check_in,        )

            "check_out": check_out,        try:

            "guests_count": guests_count,            EMAIL_FAILED.labels(type=email_type).inc()

            "total_amount": float(total_amount),        except Exception:

            "expires_at": expires_at.strftime("%d/%m/%Y %H:%M"),            pass

            "payment_link": f"https://{settings.BASE_URL or 'localhost'}/pay/{reservation_code}",        return False

        }



        return await self._send_templated_email(email_service = EmailService()

            to_email=guest_email,
            subject=f"Pre-reserva confirmada - {accommodation_name} - Código {reservation_code}",
            template_name="confirmation.html",
            template_data=template_data,
            email_type="prereservation_confirmation",
        )

    async def send_reservation_confirmed(
        self,
        guest_email: str,
        guest_name: str,
        reservation_code: str,
        accommodation_name: str,
        check_in: str,
        check_out: str,
        guests_count: int,
        total_amount: Decimal,
        accommodation_address: Optional[str] = None,
        check_in_instructions: Optional[str] = None,
    ) -> bool:
        """Enviar email de reserva confirmada con datos de check-in."""
        template_data = {
            "guest_name": guest_name,
            "reservation_code": reservation_code,
            "accommodation_name": accommodation_name,
            "check_in": check_in,
            "check_out": check_out,
            "guests_count": guests_count,
            "total_amount": float(total_amount),
            "accommodation_address": accommodation_address,
            "check_in_instructions": check_in_instructions,
        }

        return await self._send_templated_email(
            to_email=guest_email,
            subject=f"¡Reserva confirmada! - {accommodation_name} - {reservation_code}",
            template_name="reservation_confirmed.html",
            template_data=template_data,
            email_type="reservation_confirmed",
        )

    async def send_reservation_expired(
        self,
        guest_email: str,
        guest_name: str,
        reservation_code: str,
        accommodation_name: str,
        check_in: str,
        check_out: str,
    ) -> bool:
        """Enviar email de reserva expirada."""
        template_data = {
            "guest_name": guest_name,
            "reservation_code": reservation_code,
            "accommodation_name": accommodation_name,
            "check_in": check_in,
            "check_out": check_out,
            "new_search_link": f"https://{settings.BASE_URL or 'localhost'}",
        }

        return await self._send_templated_email(
            to_email=guest_email,
            subject=f"Reserva expirada - {accommodation_name} - {reservation_code}",
            template_name="reservation_expired.html",
            template_data=template_data,
            email_type="reservation_expired",
        )

    async def send_payment_reminder(
        self,
        guest_email: str,
        guest_name: str,
        reservation_code: str,
        accommodation_name: str,
        total_amount: Decimal,
        expires_at: datetime,
    ) -> bool:
        """Enviar recordatorio de pago (24h antes de expiración)."""
        hours_remaining = (expires_at - datetime.now(timezone.utc)).total_seconds() / 3600

        template_data = {
            "guest_name": guest_name,
            "reservation_code": reservation_code,
            "accommodation_name": accommodation_name,
            "total_amount": float(total_amount),
            "hours_remaining": int(hours_remaining),
            "expires_at": expires_at.strftime("%d/%m/%Y %H:%M"),
            "payment_link": f"https://{settings.BASE_URL or 'localhost'}/pay/{reservation_code}",
        }

        return await self._send_templated_email(
            to_email=guest_email,
            subject=f"Recordatorio: Completa tu reserva - {accommodation_name}",
            template_name="payment_reminder.html",
            template_data=template_data,
            email_type="payment_reminder",
        )

    async def _send_templated_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        email_type: str,
    ) -> bool:
        """Enviar email usando template Jinja2."""
        if not self._is_configured():
            logger.warning("smtp_not_configured", type=email_type, to_email=to_email[:20] + "...")
            EMAIL_SENT_TOTAL.labels(type=email_type, status="not_configured").inc()
            return False

        try:
            # Render template
            start_time = datetime.now(timezone.utc)
            html_content = self._render_template(template_name, template_data)
            if html_content is None:
                EMAIL_SENT_TOTAL.labels(type=email_type, status="template_error").inc()
                return False

            EMAIL_TEMPLATE_RENDER_DURATION.labels(template=template_name).observe(
                (datetime.now(timezone.utc) - start_time).total_seconds()
            )

            # Enviar email
            start_time = datetime.now(timezone.utc)
            success = await self._send_smtp_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
            )
            EMAIL_SEND_DURATION.labels(type=email_type).observe(
                (datetime.now(timezone.utc) - start_time).total_seconds()
            )

            if success:
                EMAIL_SENT_TOTAL.labels(type=email_type, status="success").inc()
                logger.info(
                    "email_sent",
                    type=email_type,
                    to_email=to_email[:20] + "...",
                    subject=subject,
                )
            else:
                EMAIL_SENT_TOTAL.labels(type=email_type, status="failed").inc()

            return success

        except Exception as e:
            EMAIL_SENT_TOTAL.labels(type=email_type, status="error").inc()
            logger.error(
                "email_send_error",
                type=email_type,
                to_email=to_email[:20] + "...",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    def _render_template(self, template_name: str, template_data: Dict[str, Any]) -> Optional[str]:
        """Render Jinja2 template."""
        if jinja_env is None:
            logger.error("jinja_env_not_available", template=template_name)
            return None

        try:
            template = jinja_env.get_template(template_name)
            return template.render(**template_data)
        except Exception as e:
            logger.error("template_render_error", template=template_name, error=str(e))
            return None

    async def _send_smtp_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> bool:
        """Enviar email via aiosmtplib con retry."""
        max_retries = 3
        backoff_delays = [0.5, 1.0, 2.0]

        for attempt in range(max_retries):
            try:
                # Crear mensaje
                message = MIMEMultipart("alternative")
                message["From"] = self.smtp_from
                message["To"] = to_email
                message["Subject"] = subject

                # Adjuntar HTML
                html_part = MIMEText(html_content, "html", "utf-8")
                message.attach(html_part)

                # Configurar conexión SMTP
                smtp_kwargs = {
                    "hostname": self.smtp_host,
                    "port": self.smtp_port,
                    "use_tls": self.smtp_use_tls,
                    "timeout": 30,
                }

                # Autenticación (opcional)
                if self.smtp_user and self.smtp_pass:
                    smtp_kwargs["username"] = self.smtp_user
                    smtp_kwargs["password"] = self.smtp_pass

                # Enviar
                await aiosmtplib.send(message, **smtp_kwargs)
                return True

            except Exception as e:
                logger.warning(
                    "smtp_send_retry",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    to_email=to_email[:20] + "...",
                    error=str(e),
                )

                if attempt < max_retries - 1:
                    # Esperar antes del siguiente intento
                    import asyncio

                    await asyncio.sleep(backoff_delays[attempt])
                else:
                    # Último intento fallido
                    logger.error(
                        "smtp_send_failed",
                        host=self.smtp_host,
                        port=self.smtp_port,
                        to_email=to_email[:20] + "...",
                        error=str(e),
                    )

        return False

    def _is_configured(self) -> bool:
        """Verificar si SMTP está configurado."""
        return bool(self.smtp_host and self.smtp_from)


# Instancia global del servicio
email_service = EmailService()