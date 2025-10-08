#!/bin/bash
# Script rápido para configurar Mercado Pago

set -e

echo "💰 CONFIGURACIÓN MERCADO PAGO"
echo "============================="

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${BLUE}📋 PASOS PARA CONFIGURAR MERCADO PAGO:${NC}"
echo ""

echo "1️⃣  OBTENER CREDENCIALES:"
echo "   👉 Ir a: https://www.mercadopago.com.ar/developers"
echo "   👉 Tus aplicaciones > [Tu App] > Credenciales"
echo "   👉 Copiar Access Token de Producción"
echo "   👉 Formato: APP_USR-xxxxxxxxxxxxxxxx"
echo ""

echo "2️⃣  CONFIGURAR WEBHOOK:"
echo "   👉 En el panel > Webhooks > Crear webhook"
echo "   👉 URL: https://TU-DOMINIO.com/api/v1/webhooks/mercadopago"
echo "   👉 Eventos: payment (✅ seleccionar)"
echo "   👉 Opcional: Configurar secreto de webhook"
echo ""

echo "3️⃣  ACTUALIZAR .env.production:"
echo ""

# Verificar si existe .env.production
if [ -f ".env.production" ]; then
    echo -e "${GREEN}✅ .env.production encontrado${NC}"

    # Extraer el webhook secret generado
    WEBHOOK_SECRET=$(grep "MERCADOPAGO_WEBHOOK_SECRET=" .env.production | cut -d'=' -f2)

    echo -e "${YELLOW}📝 Variables a actualizar:${NC}"
    echo "MERCADOPAGO_ACCESS_TOKEN=APP_USR_TU_ACCESS_TOKEN"
    echo "MERCADOPAGO_WEBHOOK_SECRET=$WEBHOOK_SECRET  # ✅ Ya generado"
    echo ""

    echo -e "${BLUE}🔗 USAR ESTE WEBHOOK SECRET EN MP (OPCIONAL):${NC}"
    echo -e "${GREEN}$WEBHOOK_SECRET${NC}"
    echo ""

else
    echo -e "${RED}❌ .env.production no encontrado${NC}"
    echo "   👉 Ejecutar primero: ./scripts/generate_production_secrets.sh"
    exit 1
fi

echo "4️⃣  FLUJO DE PAGO:"
echo "   👉 Sistema crea preferencia MP automáticamente"
echo "   👉 Cliente paga con link/QR generado"
echo "   👉 MP envía webhook al completar pago"
echo "   👉 Sistema confirma reserva automáticamente"
echo ""

echo "5️⃣  VERIFICAR WEBHOOK:"
echo "   👉 Hacer pago de prueba (monto mínimo)"
echo "   👉 Verificar logs: docker-compose logs api"
echo "   👉 Buscar: 'mercadopago_webhook_received'"
echo "   👉 Estado reserva debe cambiar: 'pending' → 'confirmed'"
echo ""

echo -e "${GREEN}🎯 ENDPOINT WEBHOOK YA IMPLEMENTADO:${NC}"
echo "   📍 POST /api/v1/webhooks/mercadopago"
echo "   🔒 Validación x-signature implementada"
echo "   🔄 Idempotencia por payment_id"
echo "   ✅ Confirmación automática de reservas"
echo ""

echo -e "${BLUE}💡 FUNCIONALIDADES IMPLEMENTADAS:${NC}"
echo "   📝 Crear preferencia de pago"
echo "   🔗 Generar link de pago"
echo "   📱 QR code automático"
echo "   💰 Cálculo de señas (30% por defecto)"
echo "   ⏰ Expiración de links (24h)"
echo "   🔄 Webhook de confirmación"
echo ""

# Verificar si el endpoint está funcionando
echo -e "${BLUE}🔍 Verificando endpoint...${NC}"
if curl -s http://localhost:8000/api/v1/healthz >/dev/null 2>&1; then
    echo -e "${GREEN}✅ API respondiendo en localhost:8000${NC}"
    echo "   👉 Webhook estará en: https://TU-DOMINIO.com/api/v1/webhooks/mercadopago"
else
    echo -e "${YELLOW}⚠️  API no accesible localmente (normal si no está corriendo)${NC}"
fi

echo ""
echo -e "${GREEN}✅ CONFIGURACIÓN LISTA${NC}"
echo "   👉 Solo falta Access Token en .env.production"
echo "   👉 Y configurar webhook en panel MP"
echo ""

echo -e "${YELLOW}🔧 PRÓXIMO PASO RECOMENDADO:${NC}"
echo "   👉 Probar con SDK de prueba primero"
echo "   👉 Usar tarjetas de test de MP"
echo "   👉 Verificar flujo completo antes de producción"
echo ""
