#!/bin/bash
# Script rápido para configurar WhatsApp Business API

set -e

echo "📱 CONFIGURACIÓN WHATSAPP BUSINESS API"
echo "======================================"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${BLUE}📋 PASOS PARA CONFIGURAR WHATSAPP:${NC}"
echo ""

echo "1️⃣  OBTENER CREDENCIALES en Meta Business:"
echo "   👉 Ir a: https://developers.facebook.com/apps"
echo "   👉 Seleccionar tu app > WhatsApp > Configuración"
echo "   👉 Copiar:"
echo "      - Access Token"
echo "      - App Secret"
echo "      - Phone Number ID"
echo ""

echo "2️⃣  CONFIGURAR WEBHOOK:"
echo "   👉 En Meta Business > WhatsApp > Configuración > Webhook"
echo "   👉 URL del webhook: https://TU-DOMINIO.com/api/v1/webhooks/whatsapp"
echo "   👉 Token de verificación: (será generado automáticamente)"
echo "   👉 Campos: messages, message_status"
echo ""

echo "3️⃣  ACTUALIZAR .env.production:"
echo ""

# Verificar si existe .env.production
if [ -f ".env.production" ]; then
    echo -e "${GREEN}✅ .env.production encontrado${NC}"

    # Extraer el verify token generado
    VERIFY_TOKEN=$(grep "WHATSAPP_VERIFY_TOKEN=" .env.production | cut -d'=' -f2)

    echo -e "${YELLOW}📝 Variables a actualizar:${NC}"
    echo "WHATSAPP_ACCESS_TOKEN=TU_ACCESS_TOKEN_DESDE_META"
    echo "WHATSAPP_APP_SECRET=TU_APP_SECRET_DESDE_META"
    echo "WHATSAPP_PHONE_ID=TU_PHONE_ID_DESDE_META"
    echo "WHATSAPP_VERIFY_TOKEN=$VERIFY_TOKEN  # ✅ Ya generado"
    echo ""

    echo -e "${BLUE}🔗 USAR ESTE TOKEN DE VERIFICACIÓN EN META:${NC}"
    echo -e "${GREEN}$VERIFY_TOKEN${NC}"
    echo ""

else
    echo -e "${RED}❌ .env.production no encontrado${NC}"
    echo "   👉 Ejecutar primero: ./scripts/generate_production_secrets.sh"
    exit 1
fi

echo "4️⃣  VERIFICAR WEBHOOK:"
echo "   👉 Meta enviará GET request para verificar"
echo "   👉 Nuestro endpoint responderá automáticamente"
echo "   👉 Estado debe cambiar a 'Verificado' ✅"
echo ""

echo "5️⃣  PROBAR MENSAJE:"
echo "   👉 Enviar mensaje de prueba al número de WhatsApp"
echo "   👉 Verificar logs: docker-compose logs api"
echo "   👉 Buscar: 'whatsapp_webhook_received'"
echo ""

echo -e "${GREEN}🎯 ENDPOINT WEBHOOK YA IMPLEMENTADO:${NC}"
echo "   📍 GET  /api/v1/webhooks/whatsapp  -> Verificación"
echo "   📍 POST /api/v1/webhooks/whatsapp  -> Recepción mensajes"
echo "   🔒 Validación HMAC SHA-256 implementada"
echo "   📝 Normalización a contrato unificado"
echo ""

# Verificar si el endpoint está funcionando
echo -e "${BLUE}🔍 Verificando endpoint...${NC}"
if curl -s http://localhost:8000/api/v1/healthz >/dev/null 2>&1; then
    echo -e "${GREEN}✅ API respondiendo en localhost:8000${NC}"
    echo "   👉 Webhook estará en: https://TU-DOMINIO.com/api/v1/webhooks/whatsapp"
else
    echo -e "${YELLOW}⚠️  API no accesible localmente (normal si no está corriendo)${NC}"
fi

echo ""
echo -e "${GREEN}✅ CONFIGURACIÓN LISTA${NC}"
echo "   👉 Solo falta completar credenciales en .env.production"
echo "   👉 Y configurar webhook en Meta Business"
echo ""
