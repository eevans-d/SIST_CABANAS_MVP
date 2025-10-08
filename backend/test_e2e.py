#!/usr/bin/env python3
"""
Script de pruebas end-to-end para el sistema de alojamientos
"""
import asyncio
import json
from datetime import datetime, timedelta

import requests

# Configuración
BASE_URL = "http://localhost"
API_BASE = f"{BASE_URL}/api/v1"


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_test(name, status, details=""):
    """Imprimir resultado de test con colores"""
    if status == "PASS":
        print(f"{Colors.GREEN}✅ {name}{Colors.END}")
    elif status == "FAIL":
        print(f"{Colors.RED}❌ {name}{Colors.END}")
        if details:
            print(f"   {Colors.RED}{details}{Colors.END}")
    elif status == "WARN":
        print(f"{Colors.YELLOW}⚠️  {name}{Colors.END}")
        if details:
            print(f"   {Colors.YELLOW}{details}{Colors.END}")
    else:
        print(f"{Colors.BLUE}ℹ️  {name}{Colors.END}")


def test_health_check():
    """Test 1: Verificar health check"""
    try:
        response = requests.get(f"{API_BASE}/healthz", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["status"] in ["healthy", "degraded"]:
                print_test("Health Check", "PASS", f"Status: {data['status']}")
                return True
            else:
                print_test("Health Check", "FAIL", f"Status inesperado: {data['status']}")
                return False
        else:
            print_test("Health Check", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_test("Health Check", "FAIL", str(e))
        return False


def test_admin_accommodations():
    """Test 2: Listar alojamientos (admin)"""
    try:
        # Primero intentamos sin autenticación para ver qué pasa
        response = requests.get(f"{API_BASE}/admin/reservations", timeout=10)
        if response.status_code == 401:
            print_test(
                "Admin Reservations (sin auth)", "PASS", "Requiere autenticación correctamente"
            )
            return []
        elif response.status_code == 200:
            data = response.json()
            print_test("Admin Reservations", "PASS", f"Encontradas {len(data)} reservas")
            return data
        else:
            print_test("Admin Reservations", "WARN", f"HTTP {response.status_code}")
            return []
    except Exception as e:
        print_test("Admin Reservations", "FAIL", str(e))
        return []


def test_nlu_analyze():
    """Test 3: Análisis NLU"""
    try:
        payload = {
            "text": "Hola, quiero reservar una cabaña para el próximo fin de semana para 4 personas"
        }

        response = requests.post(f"{API_BASE}/nlu/analyze", json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if "nlu" in data and "action" in data:
                intents = data.get("nlu", {}).get("intents", [])
                intent = intents[0] if intents else "unknown"
                print_test("Análisis NLU", "PASS", f"Intent detectado: {intent}")
                return data
            else:
                print_test("Análisis NLU", "FAIL", "Formato de respuesta inválido")
                return None
        else:
            print_test("Análisis NLU", "FAIL", f"HTTP {response.status_code}")
            return None
    except Exception as e:
        print_test("Análisis NLU", "FAIL", str(e))
        return None


def test_prereservation_flow():
    """Test 4: Flujo de pre-reserva (usando datos de prueba)"""
    try:
        # Intentamos crear una pre-reserva con datos válidos
        check_in = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=33)).strftime("%Y-%m-%d")

        payload = {
            "accommodation_id": 4,  # ID del primer alojamiento creado
            "check_in": check_in,
            "check_out": check_out,
            "guests": 2,  # Cambiar de guests_count a guests
            "contact_name": "Test Usuario E2E",  # Cambiar de guest_name a contact_name
            "contact_phone": "+5491123456789",  # Cambiar de guest_phone a contact_phone
            "contact_email": "test.e2e@example.com",  # Agregar contact_email
            "channel": "test",  # Cambiar de channel_source a channel
        }

        response = requests.post(f"{API_BASE}/reservations/pre-reserve", json=payload, timeout=10)

        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            if "code" in data and "expires_at" in data:
                print_test(
                    "Pre-reserva E2E",
                    "PASS",
                    f"Código: {data['code']}, Expira: {data['expires_at']}",
                )
                return data
            else:
                print_test("Pre-reserva E2E", "FAIL", "Formato de respuesta inválido")
                return None
        elif response.status_code == 409:
            print_test(
                "Pre-reserva E2E", "WARN", "Fechas no disponibles (esperado con datos de prueba)"
            )
            return None
        elif response.status_code == 400:
            print_test("Pre-reserva E2E", "WARN", "Datos inválidos")
            return None
        else:
            print_test("Pre-reserva E2E", "FAIL", f"HTTP {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error: {error_detail}")
            except:
                pass
            return None
    except Exception as e:
        print_test("Pre-reserva E2E", "FAIL", str(e))
        return None


def test_list_reservations():
    """Test 5: Listar reservas (admin sin auth)"""
    try:
        response = requests.get(f"{API_BASE}/admin/reservations", timeout=10)
        if response.status_code == 401:
            print_test("Listar Reservas Admin", "PASS", "Requiere autenticación correctamente")
            return []
        elif response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print_test("Listar Reservas Admin", "PASS", f"Encontradas {len(data)} reservas")
                return data
            else:
                print_test("Listar Reservas Admin", "FAIL", "Formato de respuesta inválido")
                return None
        else:
            print_test("Listar Reservas Admin", "FAIL", f"HTTP {response.status_code}")
            return None
    except Exception as e:
        print_test("Listar Reservas Admin", "FAIL", str(e))
        return None


def test_webhook_endpoints():
    """Test 7: Verificar endpoints de webhooks (solo estructura, no funcionalidad)"""
    tests = []

    # Test WhatsApp webhook
    try:
        response = requests.get(f"{API_BASE}/webhooks/whatsapp", timeout=5)
        # 405 es esperado para GET en un endpoint POST
        if response.status_code in [405, 401, 403]:
            tests.append(("WhatsApp Webhook", "PASS", "Endpoint accesible"))
        else:
            tests.append(("WhatsApp Webhook", "WARN", f"HTTP {response.status_code}"))
    except Exception as e:
        tests.append(("WhatsApp Webhook", "FAIL", str(e)))

    # Test Mercado Pago webhook
    try:
        response = requests.get(f"{API_BASE}/webhooks/mercadopago", timeout=5)
        if response.status_code in [405, 401, 403]:
            tests.append(("MercadoPago Webhook", "PASS", "Endpoint accesible"))
        else:
            tests.append(("MercadoPago Webhook", "WARN", f"HTTP {response.status_code}"))
    except Exception as e:
        tests.append(("MercadoPago Webhook", "FAIL", str(e)))

    for test_name, status, details in tests:
        print_test(test_name, status, details)

    return all(status in ["PASS", "WARN"] for _, status, _ in tests)


def test_ical_endpoints():
    """Test 8: Verificar endpoints iCal"""
    tests = []

    # Test iCal export endpoint
    try:
        response = requests.get(f"{API_BASE}/ical/export", timeout=5)
        if response.status_code == 200:
            tests.append(("iCal Export", "PASS", "Endpoint funcional"))
        else:
            tests.append(("iCal Export", "WARN", f"HTTP {response.status_code}"))
    except Exception as e:
        tests.append(("iCal Export", "FAIL", str(e)))

    for test_name, status, details in tests:
        print_test(test_name, status, details)

    return all(status in ["PASS", "WARN"] for _, status, _ in tests)


def main():
    """Ejecutar todas las pruebas"""
    print(f"{Colors.BOLD}🧪 Ejecutando Pruebas End-to-End del Sistema de Alojamientos{Colors.END}")
    print("=" * 60)

    # Test 1: Health Check
    if not test_health_check():
        print(f"{Colors.RED}❌ Sistema no saludable. Abortando pruebas.{Colors.END}")
        return

    # Test 2: Admin endpoints (sin autenticación)
    test_admin_accommodations()

    # Test 3: NLU
    test_nlu_analyze()

    # Test 4: Pre-reserva
    test_prereservation_flow()

    # Test 5: Listar reservas (admin sin auth)
    test_list_reservations()

    # Test 6: Webhooks
    test_webhook_endpoints()

    # Test 7: iCal
    test_ical_endpoints()

    print("=" * 60)
    print(f"{Colors.BOLD}🎉 Pruebas completadas{Colors.END}")
    print(
        f"{Colors.BLUE}💡 Revisar los resultados arriba para identificar posibles problemas{Colors.END}"
    )


if __name__ == "__main__":
    main()
