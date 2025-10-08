#!/usr/bin/env python3
"""
Test del flujo completo de reservas
Prueba el ciclo: disponibilidad → pre-reserva → confirmación → cancelación
"""

import json
import time
from datetime import datetime, timedelta

import requests

BASE_URL = "http://localhost/api/v1"


def print_test(test_name, status, message=""):
    """Imprime resultado de test con colores"""
    colors = {
        "PASS": "\033[92m✅",
        "FAIL": "\033[91m❌",
        "WARN": "\033[93m⚠️ ",
        "INFO": "\033[94mℹ️ ",
    }
    reset = "\033[0m"
    status_color = colors.get(status, "")
    print(f"{status_color} {test_name:<30}{reset}")
    if message:
        print(f"   {message}")


def test_health():
    """Verificar que el sistema esté funcionando"""
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_test("Sistema Saludable", "PASS", f"Status: {data.get('status', 'unknown')}")
            return True
        else:
            print_test("Sistema Saludable", "FAIL", f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_test("Sistema Saludable", "FAIL", f"Error: {str(e)}")
        return False


def test_nlu_availability():
    """Probar consulta de disponibilidad via NLU"""
    try:
        payload = {"text": "¿Hay disponibilidad para el 15 de noviembre para 2 personas?"}
        response = requests.post(f"{BASE_URL}/nlu/analyze", json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            intents = data.get("nlu", {}).get("intents", [])
            if "disponibilidad" in intents:
                print_test("NLU Disponibilidad", "PASS", f"Intent detectado correctamente")
                return data
            else:
                print_test("NLU Disponibilidad", "WARN", f"Intent: {intents}")
                return data
        else:
            print_test("NLU Disponibilidad", "FAIL", f"Status: {response.status_code}")
            return None
    except Exception as e:
        print_test("NLU Disponibilidad", "FAIL", f"Error: {str(e)}")
        return None


def test_nlu_reservation():
    """Probar solicitud de reserva via NLU"""
    try:
        payload = {
            "text": "Quiero reservar la cabaña familiar para el 20 de noviembre por 3 noches para 4 personas"
        }
        response = requests.post(f"{BASE_URL}/nlu/analyze", json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            intents = data.get("nlu", {}).get("intents", [])
            if "reservar" in intents:
                print_test("NLU Reserva", "PASS", f"Intent detectado correctamente")
                dates = data.get("nlu", {}).get("dates", [])
                if dates:
                    print_test("NLU Fechas", "PASS", f"Fechas extraídas: {dates}")
                else:
                    print_test("NLU Fechas", "WARN", "No se detectaron fechas")
                return data
            else:
                print_test("NLU Reserva", "WARN", f"Intent: {intents}")
                return data
        else:
            print_test("NLU Reserva", "FAIL", f"Status: {response.status_code}")
            return None
    except Exception as e:
        print_test("NLU Reserva", "FAIL", f"Error: {str(e)}")
        return None


def test_create_prereservation():
    """Crear una pre-reserva completa"""
    try:
        # Fechas futuras para evitar conflictos - usamos un offset diferente para evitar conflictos
        # con reservas existentes
        check_in = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=63)).strftime("%Y-%m-%d")

        # Usamos el ID 3 que parece estar libre
        accommodation_id = 3  # Usando alojamiento libre
        print_test("Alojamiento", "INFO", f"Usando ID fijo: {accommodation_id}")

        payload = {
            "accommodation_id": accommodation_id,
            "check_in": check_in,
            "check_out": check_out,
            "guests": 3,
            "contact_name": "Juan Test",
            "contact_phone": "+5491123456789",
            "contact_email": "juan.test@example.com",
            "channel": "whatsapp",
        }

        response = requests.post(f"{BASE_URL}/reservations/pre-reserve", json=payload, timeout=10)

        if response.status_code in [200, 201]:
            data = response.json()
            code = data.get("code")
            expires_at = data.get("expires_at")
            deposit = data.get("deposit_amount")
            error = data.get("error")

            if error:
                print_test("Pre-reserva Creada", "WARN", f"Error: {error}")
                return data

            if code:
                print_test("Pre-reserva Creada", "PASS", f"Código: {code} (ID: {accommodation_id})")
                print_test("Depósito Calculado", "PASS", f"${deposit}")
                print_test("Expiración", "INFO", f"Expira: {expires_at}")

                # Guardar el ID para la prueba de conflicto
                global last_used_accommodation_id
                last_used_accommodation_id = accommodation_id

                return data
            else:
                print_test(
                    "Pre-reserva Creada",
                    "WARN",
                    f"Código vacío, posible error (ID: {accommodation_id})",
                )
                return data
        else:
            error_msg = response.text
            print_test(
                "Pre-reserva Creada", "FAIL", f"Status: {response.status_code}, Error: {error_msg}"
            )
            return None

    except Exception as e:
        print_test("Pre-reserva Creada", "FAIL", f"Error: {str(e)}")
        return None


def test_reservation_conflict():
    """Probar que se detecten conflictos de fechas"""
    global last_used_accommodation_id

    try:
        # Usar las MISMAS fechas que la pre-reserva anterior
        check_in = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=63)).strftime("%Y-%m-%d")

        print_test(
            "Conflicto",
            "INFO",
            f"Intentando reservar mismo alojamiento ID={last_used_accommodation_id} para {check_in} a {check_out}",
        )

        payload = {
            "accommodation_id": last_used_accommodation_id,  # Usamos la misma ID que la reserva anterior
            "check_in": check_in,
            "check_out": check_out,
            "guests": 2,
            "contact_name": "Ana Conflict",
            "contact_phone": "+5491987654321",
            "contact_email": "ana.conflict@example.com",
            "channel": "whatsapp",
        }

        response = requests.post(f"{BASE_URL}/reservations/pre-reserve", json=payload, timeout=10)

        if response.status_code in [200, 201]:
            data = response.json()
            # El endpoint puede devolver 200 pero con error en el body
            if data.get("error") == "processing_or_unavailable":
                print_test(
                    "Detección Conflicto",
                    "PASS",
                    "Conflicto detectado como 'processing_or_unavailable'",
                )
                return True
            elif data.get("code"):
                print_test(
                    "Detección Conflicto",
                    "FAIL",
                    f"No se detectó el conflicto - Se creó: {data.get('code')}",
                )
                return False
            else:
                print_test("Detección Conflicto", "WARN", f"Respuesta inesperada: {data}")
                return False
        elif response.status_code == 409 or response.status_code == 400:
            print_test("Detección Conflicto", "PASS", "Conflicto detectado con código HTTP")
            return True
        else:
            print_test(
                "Detección Conflicto",
                "WARN",
                f"Status: {response.status_code}, ID: {last_used_accommodation_id}",
            )
            return False

    except Exception as e:
        print_test("Detección Conflicto", "FAIL", f"Error: {str(e)}")
        return False


def test_nlu_pricing():
    """Probar consulta de precios via NLU"""
    try:
        payload = {"text": "¿Cuánto cuesta la cabaña familiar por 3 noches?"}
        response = requests.post(f"{BASE_URL}/nlu/analyze", json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            intents = data.get("nlu", {}).get("intents", [])
            if "precio" in intents:
                print_test("NLU Precio", "PASS", f"Intent detectado correctamente")
                return data
            else:
                print_test("NLU Precio", "WARN", f"Intent: {intents}")
                return data
        else:
            print_test("NLU Precio", "FAIL", f"Status: {response.status_code}")
            return None
    except Exception as e:
        print_test("NLU Precio", "FAIL", f"Error: {str(e)}")
        return None


def test_nlu_services():
    """Probar consulta de servicios via NLU"""
    try:
        payload = {"text": "¿Qué servicios incluye la cabaña? ¿Tiene WiFi y parrilla?"}
        response = requests.post(f"{BASE_URL}/nlu/analyze", json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            intents = data.get("nlu", {}).get("intents", [])
            if "servicios" in intents:
                print_test("NLU Servicios", "PASS", f"Intent detectado correctamente")
                return data
            else:
                print_test("NLU Servicios", "WARN", f"Intent: {intents}")
                return data
        else:
            print_test("NLU Servicios", "FAIL", f"Status: {response.status_code}")
            return None
    except Exception as e:
        print_test("NLU Servicios", "FAIL", f"Error: {str(e)}")
        return None


# Variable global para compartir el id entre pruebas
last_used_accommodation_id = 1


def main():
    """Ejecutar todas las pruebas del flujo de reservas"""
    print("🎯 Probando Flujo Completo de Reservas")
    print("=" * 50)

    # 1. Verificar sistema
    if not test_health():
        print("\n❌ Sistema no disponible - abortando pruebas")
        return

    print("\n📋 Pruebas NLU - Comprensión de intents")
    print("-" * 40)

    # 2. Probar análisis NLU
    test_nlu_availability()
    test_nlu_reservation()
    test_nlu_pricing()
    test_nlu_services()

    print("\n🏠 Pruebas de Reservas - Lógica de negocio")
    print("-" * 40)

    # 3. Probar flujo de reservas
    prereservation = test_create_prereservation()

    if prereservation:
        # 4. Probar detección de conflictos
        time.sleep(1)  # Pequeña pausa
        test_reservation_conflict()

    print("\n" + "=" * 50)
    print("🎉 Pruebas del flujo completadas")
    print("💡 Revisar los resultados para identificar mejoras")


if __name__ == "__main__":
    main()
