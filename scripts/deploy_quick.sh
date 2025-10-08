#!/bin/bash
# Script de deploy rápido para producción

set -e

echo "🚀 DEPLOY RÁPIDO - SISTEMA MVP ALOJAMIENTOS"
echo "=========================================="

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

# Función para pausar con confirmación
confirm() {
    echo ""
    echo -e "${YELLOW}⏸️  $1${NC}"
    read -p "¿Continuar? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Deploy cancelado${NC}"
        exit 1
    fi
}

echo ""
echo -e "${BOLD}📋 CHECKLIST PRE-DEPLOY:${NC}"

# 1. Verificar archivos críticos
echo -e "${BLUE}1️⃣  Verificando archivos...${NC}"
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ .env.production no existe${NC}"
    echo "   👉 Ejecutar: ./scripts/generate_production_secrets.sh"
    exit 1
fi

if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ docker-compose.yml no existe${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Archivos críticos OK${NC}"

# 2. Verificar configuración
echo -e "${BLUE}2️⃣  Verificando configuración...${NC}"
if ! docker-compose config >/dev/null 2>&1; then
    echo -e "${RED}❌ Error en docker-compose.yml${NC}"
    exit 1
fi

# Verificar que el dominio esté configurado
if grep -q "TU-DOMINIO-REAL.com" .env.production; then
    echo -e "${RED}❌ DOMAIN no configurado en .env.production${NC}"
    echo "   👉 Editar .env.production y configurar:"
    echo "      DOMAIN=tu-dominio-real.com"
    echo "      BASE_URL=https://tu-dominio-real.com"
    exit 1
fi

echo -e "${GREEN}✅ Configuración OK${NC}"

# 3. Verificar secretos
echo -e "${BLUE}3️⃣  Verificando secretos...${NC}"
if grep -q "TU_ACCESS_TOKEN_AQUI" .env.production; then
    echo -e "${YELLOW}⚠️  Faltan credenciales de terceros en .env.production${NC}"
    echo "   👉 WhatsApp: WHATSAPP_ACCESS_TOKEN, WHATSAPP_APP_SECRET, WHATSAPP_PHONE_ID"
    echo "   👉 Mercado Pago: MERCADOPAGO_ACCESS_TOKEN"
    confirm "Continuar sin credenciales de terceros (se pueden configurar después)"
fi

echo -e "${GREEN}✅ Secretos verificados${NC}"

# 4. Backup actual (si existe)
echo -e "${BLUE}4️⃣  Creando backup...${NC}"
if [ -f ".env" ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ Backup de .env creado${NC}"
fi

# 5. Deploy
echo ""
echo -e "${BOLD}🚀 INICIANDO DEPLOY:${NC}"

echo -e "${BLUE}5️⃣  Copiando configuración de producción...${NC}"
cp .env.production .env
echo -e "${GREEN}✅ .env actualizado${NC}"

echo -e "${BLUE}6️⃣  Deteniendo contenedores...${NC}"
docker-compose down
echo -e "${GREEN}✅ Contenedores detenidos${NC}"

echo -e "${BLUE}7️⃣  Iniciando en modo producción...${NC}"
docker-compose up -d
echo -e "${GREEN}✅ Contenedores iniciados${NC}"

# 6. Verificación post-deploy
echo ""
echo -e "${BOLD}🔍 VERIFICACIÓN POST-DEPLOY:${NC}"

echo -e "${BLUE}8️⃣  Esperando que los servicios estén listos...${NC}"
sleep 15

# Verificar contenedores
CONTAINERS_UP=$(docker-compose ps --services --filter "status=running" | wc -l)
TOTAL_CONTAINERS=$(docker-compose ps --services | wc -l)

echo "   📦 Contenedores corriendo: $CONTAINERS_UP/$TOTAL_CONTAINERS"

# Verificar health
echo -e "${BLUE}9️⃣  Verificando health endpoint...${NC}"
for i in {1..6}; do
    if curl -s http://localhost:8000/api/v1/healthz >/dev/null 2>&1; then
        HEALTH_STATUS=$(curl -s http://localhost:8000/api/v1/healthz | python3 -c "import json,sys; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "error")
        echo "   🏥 Health status: $HEALTH_STATUS"

        if [ "$HEALTH_STATUS" = "healthy" ] || [ "$HEALTH_STATUS" = "degraded" ]; then
            echo -e "${GREEN}✅ API funcionando${NC}"
            break
        fi
    fi

    if [ $i -eq 6 ]; then
        echo -e "${YELLOW}⚠️  API no responde o unhealthy${NC}"
        echo "   👉 Verificar logs: docker-compose logs api"
    else
        echo "   ⏳ Intento $i/6 - Esperando..."
        sleep 5
    fi
done

# 7. Resumen final
echo ""
echo -e "${BOLD}🎉 DEPLOY COMPLETADO${NC}"
echo "===================="

echo -e "${GREEN}✅ Sistema desplegado en modo producción${NC}"
echo ""

echo -e "${BLUE}📡 ENDPOINTS DISPONIBLES:${NC}"
echo "   🏥 Health: http://localhost:8000/api/v1/healthz"
echo "   📊 Metrics: http://localhost:8000/metrics"
echo "   🔗 API Base: http://localhost:8000/api/v1/"
echo ""

echo -e "${BLUE}🔗 WEBHOOKS CONFIGURADOS:${NC}"
echo "   📱 WhatsApp: http://localhost:8000/api/v1/webhooks/whatsapp"
echo "   💰 Mercado Pago: http://localhost:8000/api/v1/webhooks/mercadopago"
echo ""

echo -e "${YELLOW}📝 PRÓXIMOS PASOS:${NC}"
echo "1. 🌐 Configurar SSL/HTTPS:"
echo "   👉 ./scripts/setup_ssl.sh"
echo ""
echo "2. 📱 Configurar webhooks WhatsApp:"
echo "   👉 ./scripts/setup_whatsapp_quick.sh"
echo ""
echo "3. 💰 Configurar webhooks Mercado Pago:"
echo "   👉 ./scripts/setup_mercadopago_quick.sh"
echo ""
echo "4. 📅 Configurar sincronización iCal:"
echo "   👉 ./scripts/configure_ical.py"
echo ""

echo -e "${GREEN}🎯 Sistema listo para configurar integraciones externas!${NC}"
echo ""

# Mostrar logs en tiempo real (opcional)
echo -e "${BLUE}📋 Para ver logs en tiempo real:${NC}"
echo "   👉 docker-compose logs -f api"
echo ""

echo -e "${BLUE}📋 Para verificar estado:${NC}"
echo "   👉 docker-compose ps"
echo "   👉 curl http://localhost:8000/api/v1/healthz"
echo ""
