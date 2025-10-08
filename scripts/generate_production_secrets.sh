#!/bin/bash
# Script para generar secretos de producción seguros

set -e

echo "🔐 Generando secretos de producción seguros..."
echo ""

# Función para generar secretos
generate_secret() {
    python3 -c "import secrets; print('$1=' + secrets.token_urlsafe(32))"
}

generate_hex_secret() {
    python3 -c "import secrets; print('$1=' + secrets.token_hex(16))"
}

generate_password() {
    python3 -c "import secrets; print('$1=' + secrets.token_urlsafe(24))"
}

echo "# ==================================="
echo "# SECRETOS DE PRODUCCIÓN GENERADOS"
echo "# Copiar y pegar en .env de producción"
echo "# ==================================="
echo ""

echo "# JWT y tokens de aplicación"
generate_secret "JWT_SECRET"
generate_secret "WHATSAPP_VERIFY_TOKEN"
generate_hex_secret "ICS_SALT"
echo ""

echo "# Passwords de base de datos"
generate_password "POSTGRES_PASSWORD"
generate_password "REDIS_PASSWORD"
echo ""

echo "# Webhook secrets (opcionales pero recomendados)"
generate_secret "MERCADOPAGO_WEBHOOK_SECRET"
echo ""

echo "# ==================================="
echo "# PRÓXIMOS PASOS:"
echo "# 1. Copiar estos valores a .env"
echo "# 2. Configurar variables de terceros:"
echo "#    - WHATSAPP_ACCESS_TOKEN (desde Meta)"
echo "#    - WHATSAPP_APP_SECRET (desde Meta)"
echo "#    - WHATSAPP_PHONE_ID (desde Meta)"
echo "#    - MERCADOPAGO_ACCESS_TOKEN (desde MP)"
echo "#    - DOMAIN (tu dominio real)"
echo "#    - BASE_URL (https://tu-dominio.com)"
echo "# 3. Ejecutar: docker-compose down && docker-compose up -d"
echo "# ==================================="
