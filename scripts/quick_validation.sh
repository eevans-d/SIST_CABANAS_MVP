#!/bin/bash
# Validación rápida del estado del sistema para producción

set -e

echo "🔍 VALIDACIÓN RÁPIDA - SISTEMA MVP ALOJAMIENTOS"
echo "=============================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_ok() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Verificar archivos críticos
echo "📁 ARCHIVOS CRÍTICOS:"
if [ -f ".env.template" ]; then
    check_ok ".env.template existe"
else
    check_error ".env.template NO EXISTE"
fi

if [ -f ".env.production" ]; then
    check_ok ".env.production generado"
else
    check_error ".env.production NO GENERADO"
fi

if [ -f "docker-compose.yml" ]; then
    check_ok "docker-compose.yml existe"
else
    check_error "docker-compose.yml NO EXISTE"
fi

echo ""

# 2. Verificar puertos cerrados
echo "🔒 SEGURIDAD - PUERTOS:"
if grep -q "^[[:space:]]*#.*5433:5432" docker-compose.yml; then
    check_ok "Puerto PostgreSQL (5433) cerrado"
elif grep -q "5433:5432" docker-compose.yml; then
    check_error "Puerto PostgreSQL (5433) EXPUESTO - CERRAR"
else
    check_warning "Puerto PostgreSQL - verificar manualmente"
fi

if grep -q "^[[:space:]]*#.*6379:6379" docker-compose.yml; then
    check_ok "Puerto Redis (6379) cerrado"
elif grep -q "6379:6379" docker-compose.yml; then
    check_error "Puerto Redis (6379) EXPUESTO - CERRAR"
else
    check_warning "Puerto Redis - verificar manualmente"
fi

echo ""

# 3. Verificar sintaxis docker-compose
echo "🐳 DOCKER COMPOSE:"
if docker-compose config >/dev/null 2>&1; then
    check_ok "Sintaxis docker-compose válida"
else
    check_error "Sintaxis docker-compose INVÁLIDA"
fi

echo ""

# 4. Verificar secretos en .env.production
echo "🔐 SECRETOS (.env.production):"
if [ -f ".env.production" ]; then
    if grep -q "JWT_SECRET=.*[A-Za-z0-9_-]\{20,\}" .env.production; then
        check_ok "JWT_SECRET generado"
    else
        check_error "JWT_SECRET falta o muy corto"
    fi

    if grep -q "POSTGRES_PASSWORD=.*[A-Za-z0-9_-]\{15,\}" .env.production; then
        check_ok "POSTGRES_PASSWORD generado"
    else
        check_error "POSTGRES_PASSWORD falta o muy corto"
    fi

    if grep -q "REDIS_PASSWORD=.*[A-Za-z0-9_-]\{15,\}" .env.production; then
        check_ok "REDIS_PASSWORD generado"
    else
        check_error "REDIS_PASSWORD falta o muy corto"
    fi
else
    check_error ".env.production no existe"
fi

echo ""

# 5. Verificar estado de contenedores (si están corriendo)
echo "📦 CONTENEDORES (si están corriendo):"
if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "alojamientos"; then

    if docker ps | grep -q "alojamientos_api.*healthy"; then
        check_ok "API container healthy"
    elif docker ps | grep -q "alojamientos_api"; then
        check_warning "API container corriendo pero no healthy"
    else
        check_error "API container no encontrado"
    fi

    if docker ps | grep -q "alojamientos_postgres.*healthy"; then
        check_ok "PostgreSQL container healthy"
    elif docker ps | grep -q "alojamientos_postgres"; then
        check_warning "PostgreSQL container corriendo pero no healthy"
    else
        check_error "PostgreSQL container no encontrado"
    fi

    if docker ps | grep -q "alojamientos_redis.*healthy"; then
        check_ok "Redis container healthy"
    elif docker ps | grep -q "alojamientos_redis"; then
        check_warning "Redis container corriendo pero no healthy"
    else
        check_error "Redis container no encontrado"
    fi
else
    check_warning "Contenedores no están corriendo (normal si no se han iniciado)"
fi

echo ""

# 6. Verificar endpoint health (si está corriendo)
echo "🏥 HEALTH CHECK:"
if curl -s http://localhost:8000/api/v1/healthz >/dev/null 2>&1; then
    HEALTH_STATUS=$(curl -s http://localhost:8000/api/v1/healthz | python3 -c "import json,sys; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "error")
    if [ "$HEALTH_STATUS" = "healthy" ]; then
        check_ok "Health endpoint: healthy"
    elif [ "$HEALTH_STATUS" = "degraded" ]; then
        check_warning "Health endpoint: degraded"
    else
        check_error "Health endpoint: unhealthy o error"
    fi
else
    check_warning "Health endpoint no accesible (normal si no está corriendo)"
fi

echo ""

# 7. Resumen y próximos pasos
echo "🎯 PRÓXIMOS PASOS PARA PRODUCCIÓN:"
echo "=================================="
echo "1. 📝 Editar .env.production:"
echo "   - DOMAIN=tu-dominio-real.com"
echo "   - BASE_URL=https://tu-dominio-real.com"
echo "   - WHATSAPP_ACCESS_TOKEN (desde Meta)"
echo "   - WHATSAPP_APP_SECRET (desde Meta)"
echo "   - WHATSAPP_PHONE_ID (desde Meta)"
echo "   - MERCADOPAGO_ACCESS_TOKEN (desde MP)"
echo ""
echo "2. 🌐 Configurar SSL:"
echo "   - ./scripts/setup_ssl.sh"
echo ""
echo "3. 🚀 Deploy:"
echo "   - cp .env.production .env"
echo "   - docker-compose down"
echo "   - docker-compose up -d"
echo ""
echo "4. 📱 Configurar webhooks:"
echo "   - WhatsApp en Meta Business"
echo "   - Mercado Pago en Dashboard"
echo ""

echo "✅ Validación completada!"
