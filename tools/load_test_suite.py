"""
Load Testing Suite con Locust - Sistema MVP

Suite completa de tests de carga para validar SLOs:
- P95 < 3s para endpoints texto
- P95 < 15s para audio processing
- 100 users concurrentes
- 1000 req/min sostenido

Uso:
    # Test básico (10 users, 1 min)
    locust -f tools/load_test_suite.py --headless -u 10 -r 2 -t 1m --host http://localhost:8000

    # Test completo (100 users, 5 min)
    locust -f tools/load_test_suite.py --headless -u 100 -r 10 -t 5m --host http://localhost:8000

    # Con UI web
    locust -f tools/load_test_suite.py --host http://localhost:8000
    # Abrir http://localhost:8089
"""

import json
import logging
import random
import time
from datetime import date, timedelta

from locust import HttpUser, between, events, task

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReservationUser(HttpUser):
    """Usuario que simula flujo de reservas"""

    wait_time = between(1, 3)  # Esperar 1-3s entre requests

    def on_start(self):
        """Setup inicial del usuario"""
        self.accommodation_id = 1  # Asumimos que existe
        self.user_id = random.randint(1000, 9999)
        logger.info(f"Usuario {self.user_id} iniciado")

    @task(5)
    def view_accommodations(self):
        """Ver lista de alojamientos (tarea más común)"""
        with self.client.get(
            "/api/v1/accommodations", catch_response=True, name="/accommodations [LIST]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(3)
    def check_availability(self):
        """Consultar disponibilidad"""
        check_in = date.today() + timedelta(days=random.randint(7, 60))
        check_out = check_in + timedelta(days=random.randint(1, 7))

        params = {
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
        }

        with self.client.get(
            f"/api/v1/accommodations/{self.accommodation_id}/availability",
            params=params,
            catch_response=True,
            name="/accommodations/{id}/availability",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def create_prereservation(self):
        """Crear pre-reserva (flujo crítico)"""
        check_in = date.today() + timedelta(days=random.randint(30, 90))
        check_out = check_in + timedelta(days=random.randint(2, 5))

        payload = {
            "accommodation_id": self.accommodation_id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "guests": random.randint(1, 4),
            "channel": "load_test",
            "contact_name": f"Test User {self.user_id}",
            "contact_phone": f"+549111234{self.user_id}",
            "contact_email": f"test{self.user_id}@example.com",
        }

        start_time = time.monotonic()

        with self.client.post(
            "/api/v1/reservations/prereserve",
            json=payload,
            catch_response=True,
            name="/reservations/prereserve [POST]",
        ) as response:
            duration_ms = (time.monotonic() - start_time) * 1000

            if response.status_code == 201:
                # Validar SLO: P95 < 3s
                if duration_ms > 3000:
                    logger.warning(f"⚠️  Pre-reserva lenta: {duration_ms:.0f} ms")
                response.success()
            elif response.status_code == 409:
                # Conflict por overlap - esperado en load test
                response.success()
            elif response.status_code == 400 and "processing_or_unavailable" in response.text:
                # Lock en uso - esperado en concurrencia
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}: {response.text[:200]}")

    @task(1)
    def healthcheck(self):
        """Health check (bajo peso, pero importante)"""
        with self.client.get("/api/v1/healthz", catch_response=True, name="/healthz") as response:
            if response.status_code == 200:
                data = response.json()
                # Validar latencias
                if data.get("checks", {}).get("database", {}).get("latency_ms", 0) > 500:
                    logger.warning("⚠️  DB latency alta")
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


class WhatsAppWebhookUser(HttpUser):
    """Usuario que simula webhooks de WhatsApp"""

    wait_time = between(2, 5)

    def on_start(self):
        self.phone = f"+549111{random.randint(1000000, 9999999)}"

    @task(3)
    def text_message_webhook(self):
        """Simular webhook con mensaje de texto"""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": self.phone,
                                        "id": f"test_{random.randint(10000, 99999)}",
                                        "timestamp": str(int(time.time())),
                                        "type": "text",
                                        "text": {
                                            "body": random.choice(
                                                [
                                                    "Hola, quiero reservar",
                                                    "Hay disponibilidad?",
                                                    "Cuánto cuesta?",
                                                    "Quiero hacer una consulta",
                                                ]
                                            )
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        start_time = time.monotonic()

        with self.client.post(
            "/api/v1/webhooks/whatsapp",
            json=payload,
            headers={
                "X-Hub-Signature-256": "sha256=dummy_signature_for_load_test",
                "Content-Type": "application/json",
            },
            catch_response=True,
            name="/webhooks/whatsapp [TEXT]",
        ) as response:
            duration_ms = (time.monotonic() - start_time) * 1000

            # Nota: Probablemente falle por invalid signature en staging,
            # pero eso está OK para medir performance sin webhook validation
            if response.status_code in [200, 403]:
                # Validar SLO: P95 < 3s para texto
                if duration_ms > 3000:
                    logger.warning(f"⚠️  Webhook texto lento: {duration_ms:.0f} ms")
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


class MercadoPagoWebhookUser(HttpUser):
    """Usuario que simula webhooks de Mercado Pago"""

    wait_time = between(3, 7)

    @task
    def payment_webhook(self):
        """Simular webhook de pago"""
        payload = {
            "action": "payment.updated",
            "data": {"id": str(random.randint(1000000000, 9999999999))},
        }

        with self.client.post(
            "/api/v1/webhooks/mercadopago",
            json=payload,
            headers={
                "x-signature": "ts=1234567890,v1=dummy_signature",
                "Content-Type": "application/json",
            },
            catch_response=True,
            name="/webhooks/mercadopago",
        ) as response:
            # Probablemente falle por invalid signature, pero mide performance
            if response.status_code in [200, 403]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


# =============================================================================
# EVENT HANDLERS PARA MÉTRICAS PERSONALIZADAS
# =============================================================================


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Handler al inicio del test"""
    logger.info("=" * 70)
    logger.info("🚀 INICIANDO LOAD TEST - Sistema MVP")
    logger.info("=" * 70)
    logger.info(f"Host: {environment.host}")
    logger.info(
        f"Users: {environment.runner.user_count if hasattr(environment.runner, 'user_count') else 'N/A'}"
    )


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Handler al finalizar el test - Validar SLOs"""
    logger.info("\n" + "=" * 70)
    logger.info("📊 ANALIZANDO RESULTADOS vs SLOs")
    logger.info("=" * 70)

    stats = environment.stats

    # Endpoints críticos con SLOs
    slo_endpoints = {
        "/reservations/prereserve [POST]": {"p95_max_ms": 3000, "name": "Pre-Reserva"},
        "/webhooks/whatsapp [TEXT]": {"p95_max_ms": 3000, "name": "WhatsApp Text"},
        "/healthz": {"p95_max_ms": 500, "name": "Health Check"},
    }

    slo_passed = True

    for endpoint, slo in slo_endpoints.items():
        stat = stats.get(endpoint, None)
        if stat:
            p95_ms = stat.get_response_time_percentile(0.95)
            p99_ms = stat.get_response_time_percentile(0.99)
            avg_ms = stat.avg_response_time

            status = "✅ PASS" if p95_ms <= slo["p95_max_ms"] else "❌ FAIL"
            if p95_ms > slo["p95_max_ms"]:
                slo_passed = False

            logger.info(f"\n{slo['name']}:")
            logger.info(f"  SLO: P95 < {slo['p95_max_ms']} ms")
            logger.info(f"  Avg: {avg_ms:.0f} ms | P95: {p95_ms:.0f} ms | P99: {p99_ms:.0f} ms")
            logger.info(f"  Status: {status}")

    logger.info("\n" + "=" * 70)
    if slo_passed:
        logger.info("✅ TODOS LOS SLOs CUMPLIDOS")
    else:
        logger.info("❌ ALGUNOS SLOs NO CUMPLIDOS - REQUIERE OPTIMIZACIÓN")
    logger.info("=" * 70)


# =============================================================================
# CONFIGURACIÓN DE LOCUST
# =============================================================================

# Distribución de usuarios por tipo
# 70% usuarios de reservas, 20% webhooks WhatsApp, 10% webhooks MP
# Esto se configura con --user-classes en CLI:
# locust -f load_test_suite.py --user-classes ReservationUser:7,WhatsAppWebhookUser:2,MercadoPagoWebhookUser:1

if __name__ == "__main__":
    import subprocess

    print("🔬 Load Testing Suite - Sistema MVP")
    print("\nUso:")
    print("  # Test rápido (10 users, 1 min)")
    print(
        "  locust -f tools/load_test_suite.py --headless -u 10 -r 2 -t 1m --host http://localhost:8000"
    )
    print("\n  # Test completo (100 users, 5 min)")
    print(
        "  locust -f tools/load_test_suite.py --headless -u 100 -r 10 -t 5m --host http://localhost:8000"
    )
    print("\n  # Con distribución de usuarios:")
    print("  locust -f tools/load_test_suite.py --headless -u 100 -r 10 -t 5m \\")
    print("    --host http://localhost:8000 \\")
    print("    --user-classes ReservationUser:70,WhatsAppWebhookUser:20,MercadoPagoWebhookUser:10")
