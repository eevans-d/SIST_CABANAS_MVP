#!/bin/bash
# Script para generar secretos seguros para producción
# Sistema MVP Alojamientos

set -e

echo "🔐 Generando Secretos Seguros para Producción"
echo "=============================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Generando secretos aleatorios seguros...${NC}"
echo ""

# JWT Secret (32 bytes, base64url)
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo -e "${GREEN}✓ JWT_SECRET=${NC}"
echo "JWT_SECRET=$JWT_SECRET"
echo ""

# ICS Salt (16 bytes hex)
ICS_SALT=$(python3 -c "import secrets; print(secrets.token_hex(16))")
echo -e "${GREEN}✓ ICS_SALT=${NC}"
echo "ICS_SALT=$ICS_SALT"
echo ""

# WhatsApp Verify Token (32 bytes)
WHATSAPP_VERIFY_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo -e "${GREEN}✓ WHATSAPP_VERIFY_TOKEN=${NC}"
echo "WHATSAPP_VERIFY_TOKEN=$WHATSAPP_VERIFY_TOKEN"
echo ""

# PostgreSQL Password (24 bytes)
POSTGRES_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
echo -e "${GREEN}✓ POSTGRES_PASSWORD=${NC}"
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
echo ""

# Redis Password (24 bytes)
REDIS_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
echo -e "${GREEN}✓ REDIS_PASSWORD=${NC}"
echo "REDIS_PASSWORD=$REDIS_PASSWORD"
echo ""

# Grafana Admin Password (16 bytes)
GRAFANA_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
echo -e "${GREEN}✓ GRAFANA_ADMIN_PASSWORD=${NC}"
echo "GRAFANA_ADMIN_PASSWORD=$GRAFANA_PASSWORD"
echo ""

echo "=============================================="
echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
echo "1. Guarda estos secretos en un lugar SEGURO"
echo "2. NO los commitees al repositorio"
echo "3. Actualiza el archivo .env de producción"
echo ""
echo -e "${BLUE}Archivo sugerido para guardar:${NC}"
echo "   ~/secrets/alojamientos-prod-secrets.txt"
echo ""

# Opción para guardar en archivo
read -p "¿Deseas guardar estos secretos en un archivo? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]
then
    SECRETS_DIR="$HOME/secrets"
    mkdir -p "$SECRETS_DIR"
    SECRETS_FILE="$SECRETS_DIR/alojamientos-prod-secrets-$(date +%Y%m%d-%H%M%S).txt"

    cat > "$SECRETS_FILE" << EOF
# Secretos de Producción - Sistema MVP Alojamientos
# Generado: $(date)
# MANTENER SEGURO - NO COMMITEAR

# JWT
JWT_SECRET=$JWT_SECRET

# iCal
ICS_SALT=$ICS_SALT

# WhatsApp
WHATSAPP_VERIFY_TOKEN=$WHATSAPP_VERIFY_TOKEN

# Database
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# Redis
REDIS_PASSWORD=$REDIS_PASSWORD

# Grafana
GRAFANA_ADMIN_PASSWORD=$GRAFANA_PASSWORD

# === PENDIENTES DE CONFIGURACIÓN EXTERNA ===
# Estos deben obtenerse de las plataformas respectivas:

# WhatsApp Business API (Meta Business Suite)
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token_here
WHATSAPP_APP_SECRET=your_whatsapp_app_secret_here
WHATSAPP_PHONE_ID=your_whatsapp_phone_id_here

# Mercado Pago (Developer Dashboard)
MERCADOPAGO_ACCESS_TOKEN=your_mercadopago_access_token_here
MERCADOPAGO_WEBHOOK_SECRET=optional_webhook_secret

# Email/SMTP (Provider)
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USERNAME=your_email@domain.com
SMTP_PASSWORD=your_smtp_password

# Slack (para alertas - opcional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# === CONFIGURACIÓN DEL SERVIDOR ===
DOMAIN=your-domain.com
BASE_URL=https://your-domain.com
EOF

    chmod 600 "$SECRETS_FILE"
    echo -e "${GREEN}✓ Secretos guardados en: $SECRETS_FILE${NC}"
    echo -e "${YELLOW}⚠️  Permisos establecidos a 600 (solo lectura por propietario)${NC}"
    echo ""
fi

echo -e "${BLUE}Siguiente paso:${NC}"
echo "1. Copia estos secretos a tu archivo .env de producción"
echo "2. Completa las credenciales externas (WhatsApp, MP, SMTP)"
echo "3. Configura DOMAIN y BASE_URL con tu dominio real"
echo ""
echo -e "${GREEN}✓ Generación de secretos completada${NC}"
