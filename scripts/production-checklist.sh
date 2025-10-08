#!/bin/bash
# Checklist Interactivo de Preparación para Producción
# Sistema MVP Alojamientos

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║   🚀 PREPARACIÓN PARA PRODUCCIÓN - MVP ALOJAMIENTOS  ║${NC}"
echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

COMPLETED=0
TOTAL=12

# Función para marcar item como completado
check_item() {
    local item=$1
    local status=$2

    if [ "$status" = "done" ]; then
        echo -e "${GREEN}✓${NC} $item"
        COMPLETED=$((COMPLETED + 1))
    elif [ "$status" = "pending" ]; then
        echo -e "${YELLOW}○${NC} $item ${YELLOW}(Pendiente)${NC}"
    else
        echo -e "${RED}✗${NC} $item ${RED}(No completado)${NC}"
    fi
}

echo -e "${BOLD}═══ FASE 1: SEGURIDAD Y CONFIGURACIÓN ═══${NC}"
echo ""

# 1. Verificar puertos cerrados
if grep -q "^[[:space:]]*#.*ports:" docker-compose.yml && \
   grep -A1 "postgres:" docker-compose.yml | grep -q "#.*5433:5432" && \
   grep -A1 "redis:" docker-compose.yml | grep -q "#.*6379:6379"; then
    check_item "1. Puertos DB/Redis cerrados en docker-compose.yml" "done"
else
    check_item "1. Puertos DB/Redis cerrados en docker-compose.yml" "fail"
fi

# 2. Verificar .env existe
if [ -f ".env" ]; then
    check_item "2. Archivo .env existe" "done"
else
    check_item "2. Archivo .env existe" "fail"
fi

# 3. Verificar secretos no por defecto
if [ -f ".env" ]; then
    source .env 2>/dev/null || true
    if [[ "$POSTGRES_PASSWORD" != "supersecret" ]] && \
       [[ "$POSTGRES_PASSWORD" != "change_this_secure_password" ]] && \
       [[ "$REDIS_PASSWORD" != "redispass" ]] && \
       [[ "$REDIS_PASSWORD" != "change_this_redis_password" ]]; then
        check_item "3. Secretos actualizados (no valores por defecto)" "done"
    else
        check_item "3. Secretos actualizados (no valores por defecto)" "fail"
        echo -e "   ${YELLOW}→ Ejecuta: ./scripts/generate-secrets.sh${NC}"
    fi
else
    check_item "3. Secretos actualizados" "fail"
fi

# 4. Verificar dominio configurado
if [ -f ".env" ]; then
    source .env 2>/dev/null || true
    if [[ "$DOMAIN" != "your-domain.com" ]] && [[ "$DOMAIN" != "" ]]; then
        check_item "4. Dominio configurado en .env" "done"
    else
        check_item "4. Dominio configurado en .env" "fail"
        echo -e "   ${YELLOW}→ Edita .env y configura DOMAIN=tu-dominio.com${NC}"
    fi
else
    check_item "4. Dominio configurado" "fail"
fi

echo ""
echo -e "${BOLD}═══ FASE 2: INFRAESTRUCTURA ═══${NC}"
echo ""

# 5. Docker instalado
if command -v docker &> /dev/null; then
    check_item "5. Docker instalado" "done"
else
    check_item "5. Docker instalado" "fail"
fi

# 6. Docker Compose instalado
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    check_item "6. Docker Compose instalado" "done"
else
    check_item "6. Docker Compose instalado" "fail"
fi

# 7. Validar sintaxis docker-compose
if docker-compose config > /dev/null 2>&1; then
    check_item "7. docker-compose.yml sintácticamente correcto" "done"
else
    check_item "7. docker-compose.yml sintácticamente correcto" "fail"
fi

echo ""
echo -e "${BOLD}═══ FASE 3: SSL/HTTPS ═══${NC}"
echo ""

# 8. SSL configurado
if [ -d "nginx/ssl" ] && [ -f "nginx/ssl/fullchain.pem" ]; then
    check_item "8. Certificados SSL configurados" "done"
elif [ -f "./scripts/setup_ssl.sh" ]; then
    check_item "8. Certificados SSL configurados" "pending"
    echo -e "   ${YELLOW}→ Ejecuta: ./scripts/setup_ssl.sh${NC}"
else
    check_item "8. Certificados SSL configurados" "fail"
fi

echo ""
echo -e "${BOLD}═══ FASE 4: INTEGRACIONES EXTERNAS ═══${NC}"
echo ""

# 9. WhatsApp configurado
if [ -f ".env" ]; then
    source .env 2>/dev/null || true
    if [[ "$WHATSAPP_ACCESS_TOKEN" != "your_whatsapp_access_token_here" ]] && \
       [[ "$WHATSAPP_ACCESS_TOKEN" != "" ]]; then
        check_item "9. WhatsApp Business API configurado" "done"
    else
        check_item "9. WhatsApp Business API configurado" "pending"
        echo -e "   ${YELLOW}→ Configura en Meta Business Suite${NC}"
    fi
else
    check_item "9. WhatsApp Business API configurado" "fail"
fi

# 10. Mercado Pago configurado
if [ -f ".env" ]; then
    source .env 2>/dev/null || true
    if [[ "$MERCADOPAGO_ACCESS_TOKEN" != "your_mercadopago_access_token_here" ]] && \
       [[ "$MERCADOPAGO_ACCESS_TOKEN" != "" ]]; then
        check_item "10. Mercado Pago configurado" "done"
    else
        check_item "10. Mercado Pago configurado" "pending"
        echo -e "   ${YELLOW}→ Obtén token de MP Developer Dashboard${NC}"
    fi
else
    check_item "10. Mercado Pago configurado" "fail"
fi

echo ""
echo -e "${BOLD}═══ FASE 5: VALIDACIÓN ═══${NC}"
echo ""

# 11. Tests pasando
if [ -f "backend/pytest.ini" ] || [ -f "pytest.ini" ]; then
    check_item "11. Tests disponibles" "done"
    echo -e "   ${BLUE}ℹ  Ejecuta: make test (para validar)${NC}"
else
    check_item "11. Tests configurados" "fail"
fi

# 12. Scripts de deploy listos
if [ -f "./scripts/deploy.sh" ] && [ -x "./scripts/deploy.sh" ]; then
    check_item "12. Scripts de deploy preparados" "done"
else
    check_item "12. Scripts de deploy preparados" "fail"
fi

echo ""
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo -e "${BOLD}Progreso: ${GREEN}$COMPLETED${NC}/${TOTAL} completados${NC}"
echo ""

PERCENTAGE=$((COMPLETED * 100 / TOTAL))

if [ $COMPLETED -eq $TOTAL ]; then
    echo -e "${GREEN}${BOLD}🎉 ¡LISTO PARA PRODUCCIÓN!${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "1. Ejecuta pre-deploy check: ./scripts/pre-deploy-check.sh"
    echo "2. Deploy: ./scripts/deploy.sh"
    echo "3. Smoke tests: ./scripts/smoke-test-prod.sh"
elif [ $PERCENTAGE -ge 75 ]; then
    echo -e "${YELLOW}${BOLD}⚠️  CASI LISTO ($PERCENTAGE%)${NC}"
    echo ""
    echo "Completa los items pendientes arriba para continuar."
elif [ $PERCENTAGE -ge 50 ]; then
    echo -e "${YELLOW}${BOLD}🔧 EN PROGRESO ($PERCENTAGE%)${NC}"
    echo ""
    echo "Sigue completando los items de configuración."
else
    echo -e "${RED}${BOLD}❌ REQUIERE ATENCIÓN ($PERCENTAGE%)${NC}"
    echo ""
    echo "Varios items críticos sin completar. Revisa la lista arriba."
fi

echo ""
echo -e "${BLUE}═══ RECURSOS ÚTILES ═══${NC}"
echo "• Generar secretos: ./scripts/generate-secrets.sh"
echo "• Setup SSL: ./scripts/setup_ssl.sh"
echo "• Ver estado: make status"
echo "• Documentación: cat QUE_RESTA_POR_HACER.md"
echo ""
