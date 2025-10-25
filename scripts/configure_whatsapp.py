#!/usr/bin/env python3
"""
Configurador de Webhooks de WhatsApp Business Cloud API
Este script automatiza la configuración de webhooks para el sistema de alojamientos.
"""

import json
import os
import sys
import time
from urllib.parse import urlparse

import requests


# Colores para output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_status(message, status="INFO"):
    colors = {
        "SUCCESS": Colors.GREEN + "✅",
        "ERROR": Colors.RED + "❌",
        "WARNING": Colors.YELLOW + "⚠️ ",
        "INFO": Colors.BLUE + "ℹ️ ",
        "STEP": Colors.BOLD + "🔧",
    }
    color = colors.get(status, "")
    print(f"{color} {message}{Colors.END}")


def load_env_file():
    """Cargar variables de entorno desde .env"""
    env_vars = {}
    env_file = ".env"

    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")

    return env_vars


def validate_webhook_url(url):
    """Validar que la URL del webhook sea accesible"""
    try:
        parsed = urlparse(url)
        if not parsed.scheme in ["http", "https"]:
            return False, "URL debe usar HTTP o HTTPS"

        if parsed.scheme == "http":
            print_status("Advertencia: usando HTTP en lugar de HTTPS", "WARNING")

        # Verificar que el endpoint responda
        test_url = f"{url.rstrip('/')}/webhooks/whatsapp"
        response = requests.get(test_url, timeout=10)

        if response.status_code == 405:  # Method Not Allowed es esperado para GET
            return True, "Endpoint accesible"
        elif response.status_code == 200:
            return True, "Endpoint accesible"
        else:
            return False, f"Endpoint no accesible (status: {response.status_code})"

    except requests.exceptions.RequestException as e:
        return False, f"Error de conectividad: {str(e)}"


def configure_webhook(app_id, access_token, webhook_url, verify_token):
    """Configurar webhook en WhatsApp Business Cloud API"""

    # URL para configurar webhook
    config_url = f"https://graph.facebook.com/v18.0/{app_id}/subscriptions"

    # Datos del webhook
    webhook_data = {
        "object": "whatsapp_business_account",
        "callback_url": f"{webhook_url.rstrip('/')}/webhooks/whatsapp",
        "verify_token": verify_token,
        "fields": "messages,message_status,messaging_seen,messaging_product",
    }

    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    print_status("Configurando webhook en WhatsApp...", "STEP")

    try:
        response = requests.post(config_url, json=webhook_data, headers=headers)

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print_status("Webhook configurado exitosamente", "SUCCESS")
                return True, result
            else:
                return False, f"Error en configuración: {result}"
        else:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = error_data.get("error", {}).get("message", "")
            except:
                error_detail = response.text

            return False, f"HTTP {response.status_code}: {error_detail}"

    except requests.exceptions.RequestException as e:
        return False, f"Error de red: {str(e)}"


def verify_webhook_subscription(app_id, access_token):
    """Verificar el estado de la suscripción del webhook"""

    url = f"https://graph.facebook.com/v18.0/{app_id}/subscriptions"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            subscriptions = data.get("data", [])

            print_status("Estado de suscripciones:", "INFO")

            if not subscriptions:
                print_status("No hay suscripciones configuradas", "WARNING")
                return False

            for sub in subscriptions:
                object_type = sub.get("object")
                callback_url = sub.get("callback_url")
                status = sub.get("status", "unknown")

                print(f"  📡 Objeto: {object_type}")
                print(f"  🔗 URL: {callback_url}")
                print(f"  📊 Estado: {status}")

                if object_type == "whatsapp_business_account" and status == "active":
                    print_status("Webhook activo y funcionando", "SUCCESS")
                    return True

            return False

        else:
            print_status(f"Error verificando suscripciones: HTTP {response.status_code}", "ERROR")
            return False

    except requests.exceptions.RequestException as e:
        print_status(f"Error de red verificando suscripciones: {str(e)}", "ERROR")
        return False


def test_webhook_verification(webhook_url, verify_token):
    """Probar la verificación del webhook"""

    verify_url = f"{webhook_url.rstrip('/')}/webhooks/whatsapp"

    # Parámetros que WhatsApp envía para verificación
    params = {
        "hub.mode": "subscribe",
        "hub.challenge": "test_challenge_123456",
        "hub.verify_token": verify_token,
    }

    print_status("Probando verificación del webhook...", "STEP")

    try:
        response = requests.get(verify_url, params=params, timeout=10)

        if response.status_code == 200:
            if response.text == "test_challenge_123456":
                print_status("Verificación del webhook exitosa", "SUCCESS")
                return True
            else:
                print_status(f"Respuesta incorrecta: {response.text}", "ERROR")
                return False
        else:
            print_status(f"Error en verificación: HTTP {response.status_code}", "ERROR")
            return False

    except requests.exceptions.RequestException as e:
        print_status(f"Error probando verificación: {str(e)}", "ERROR")
        return False


def main():
    """Función principal"""

    print(f"{Colors.BOLD}🔗 Configurador de Webhooks WhatsApp{Colors.END}")
    print("=" * 50)

    # Cargar variables de entorno
    env_vars = load_env_file()

    # Variables requeridas
    required_vars = [
        "WHATSAPP_APP_ID",
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_VERIFY_TOKEN",
        "WEBHOOK_BASE_URL",
    ]

    missing_vars = []
    for var in required_vars:
        if var not in env_vars:
            missing_vars.append(var)

    if missing_vars:
        print_status("Variables de entorno faltantes:", "ERROR")
        for var in missing_vars:
            print(f"  ❌ {var}")

        print("\n💡 Agregue estas variables a su archivo .env:")
        print("WHATSAPP_APP_ID=su_app_id")
        print("WHATSAPP_ACCESS_TOKEN=su_access_token")
        print("WHATSAPP_VERIFY_TOKEN=token_verificacion_personalizado")
        print("WEBHOOK_BASE_URL=https://su-dominio.com")

        return False

    # Extraer variables
    app_id = env_vars["WHATSAPP_APP_ID"]
    access_token = env_vars["WHATSAPP_ACCESS_TOKEN"]
    verify_token = env_vars["WHATSAPP_VERIFY_TOKEN"]
    webhook_url = env_vars["WEBHOOK_BASE_URL"]

    print_status("Configuración detectada:", "INFO")
    print(f"  📱 App ID: {app_id}")
    print(f"  🔑 Token: {'*' * 20}...{access_token[-4:]}")
    print(f"  🔐 Verify Token: {'*' * len(verify_token)}")
    print(f"  🌐 Webhook URL: {webhook_url}")

    # Validar URL del webhook
    print_status("Validando accesibilidad del webhook...", "STEP")
    is_valid, message = validate_webhook_url(webhook_url)

    if not is_valid:
        print_status(f"Error validando webhook: {message}", "ERROR")
        print("💡 Asegúrese de que su servidor esté ejecutándose y sea accesible")
        return False

    print_status(message, "SUCCESS")

    # Probar verificación del webhook
    if not test_webhook_verification(webhook_url, verify_token):
        print_status("Verificación del webhook falló", "ERROR")
        print("💡 Revise que el endpoint /webhooks/whatsapp responda correctamente")
        return False

    # Configurar webhook
    success, result = configure_webhook(app_id, access_token, webhook_url, verify_token)

    if not success:
        print_status(f"Error configurando webhook: {result}", "ERROR")
        return False

    # Verificar configuración
    time.sleep(2)  # Esperar un poco antes de verificar
    if verify_webhook_subscription(app_id, access_token):
        print_status("Configuración completada exitosamente", "SUCCESS")

        print("\n" + "=" * 50)
        print(f"{Colors.GREEN}🎉 WhatsApp Webhook Configurado{Colors.END}")
        print("=" * 50)
        print(f"📱 URL del webhook: {webhook_url}/webhooks/whatsapp")
        print(f"🔐 Token de verificación: {verify_token}")
        print(f"📊 Estado: Activo")

        print(f"\n{Colors.YELLOW}📝 Próximos pasos:{Colors.END}")
        print("1. Probar envío de mensajes desde WhatsApp")
        print("2. Verificar logs del sistema para mensajes recibidos")
        print("3. Configurar respuestas automáticas")

        return True
    else:
        print_status("Configuración completada pero con advertencias", "WARNING")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Configuración cancelada por el usuario{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error inesperado: {str(e)}{Colors.END}")
        sys.exit(1)
