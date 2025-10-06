#!/usr/bin/env bash
set -euo pipefail

# 🔍 Pre-Deploy Validation Script
# Verifica que todo esté listo antes del deploy a producción

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; WARNINGS=$((WARNINGS+1)); }
log_error() { echo -e "${RED}[✗]${NC} $1"; ERRORS=$((ERRORS+1)); }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔍 PRE-DEPLOY VALIDATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Verificar archivo .env
log_info "Verificando configuración de entorno..."
if [[ -f ".env" ]]; then
    log_success ".env existe"

    # Verificar variables críticas
    CRITICAL_VARS=(
        "DOMAIN"
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "JWT_SECRET"
        "ICS_SALT"
        "WHATSAPP_ACCESS_TOKEN"
        "WHATSAPP_APP_SECRET"
        "MERCADOPAGO_ACCESS_TOKEN"
    )

    source .env 2>/dev/null || true
    for var in "${CRITICAL_VARS[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Variable $var no está definida en .env"
        else
            # No mostrar valores sensibles
            log_success "Variable $var configurada"
        fi
    done

    # Verificar que no sean valores por defecto
    if [[ "${DOMAIN:-}" == "your-domain.com" ]]; then
        log_error "DOMAIN aún tiene valor por defecto"
    fi

    if [[ "${POSTGRES_PASSWORD:-}" == "change_this_secure_password" ]]; then
        log_warning "POSTGRES_PASSWORD parece ser el valor por defecto"
    fi

else
    log_error ".env no existe. Copiar desde .env.template"
fi

# 2. Verificar sintaxis docker-compose
log_info "Validando docker-compose.yml..."
cd backend 2>/dev/null || cd .
if docker-compose config > /dev/null 2>&1; then
    log_success "docker-compose.yml sintácticamente correcto"
else
    log_error "docker-compose.yml tiene errores de sintaxis"
fi

# 3. Verificar que puertos DB/Redis estén comentados
log_info "Verificando seguridad de puertos..."
if grep -q "^[[:space:]]*ports:" backend/docker-compose.yml 2>/dev/null && \
   grep -A1 "5432:5432" backend/docker-compose.yml 2>/dev/null | grep -q "^[[:space:]]*#"; then
    log_success "Puerto PostgreSQL comentado (seguro)"
else
    if grep -q "5432:5432" backend/docker-compose.yml 2>/dev/null; then
        log_warning "Puerto PostgreSQL (5432) expuesto - considerar comentar en producción"
    fi
fi

if grep -q "^[[:space:]]*ports:" backend/docker-compose.yml 2>/dev/null && \
   grep -A1 "6379:6379" backend/docker-compose.yml 2>/dev/null | grep -q "^[[:space:]]*#"; then
    log_success "Puerto Redis comentado (seguro)"
else
    if grep -q "6379:6379" backend/docker-compose.yml 2>/dev/null; then
        log_warning "Puerto Redis (6379) expuesto - considerar comentar en producción"
    fi
fi

# 4. Verificar nginx.conf generado
log_info "Verificando configuración de Nginx..."
if [[ -f "backend/nginx.conf" ]]; then
    if grep -q "\${DOMAIN}" backend/nginx.conf; then
        log_warning "nginx.conf aún tiene variable sin expandir. Ejecutar generate_nginx_conf.sh"
    else
        if grep -q "alojamientos.example.com" backend/nginx.conf; then
            log_error "nginx.conf tiene dominio placeholder"
        else
            log_success "nginx.conf generado con dominio real"
        fi
    fi
else
    if [[ -f "backend/nginx.conf.template" ]]; then
        log_success "nginx.conf.template encontrado"
        log_warning "nginx.conf no existe. Ejecutar: backend/generate_nginx_conf.sh"
    else
        log_error "nginx.conf.template no encontrado"
    fi
fi

# 5. Verificar tests
log_info "Verificando estado de tests..."
if [[ -d ".venv" ]] && [[ -f ".venv/bin/pytest" ]]; then
    log_info "Ejecutando smoke tests..."
    if .venv/bin/pytest -q backend/tests/test_journey_basic.py backend/tests/test_journey_expiration.py --tb=no 2>&1 | grep -q "passed"; then
        log_success "Smoke tests OK"
    else
        log_error "Smoke tests fallando"
    fi
else
    log_warning "Entorno virtual no encontrado, saltando tests"
fi

# 6. Verificar Git
log_info "Verificando estado de Git..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    if [[ -z $(git status --porcelain) ]]; then
        log_success "Git limpio (sin cambios pendientes)"
    else
        log_warning "Hay cambios sin commitear"
    fi

    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$CURRENT_BRANCH" == "main" ]]; then
        log_success "En rama main"
    else
        log_warning "No estás en rama main (actual: $CURRENT_BRANCH)"
    fi
else
    log_warning "No es un repositorio Git"
fi

# 7. Verificar requisitos del sistema
log_info "Verificando requisitos del sistema..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    log_success "Docker instalado (versión $DOCKER_VERSION)"
else
    log_error "Docker no instalado"
fi

if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    log_success "Docker Compose instalado (versión $COMPOSE_VERSION)"
else
    log_error "Docker Compose no instalado"
fi

# 8. Verificar certificados SSL (si existen)
log_info "Verificando certificados SSL..."
if [[ -f "nginx/ssl/fullchain.pem" ]] && [[ -f "nginx/ssl/privkey.pem" ]]; then
    log_success "Certificados SSL encontrados"

    # Verificar fecha de expiración
    if command -v openssl &> /dev/null; then
        EXPIRY=$(openssl x509 -enddate -noout -in nginx/ssl/fullchain.pem | cut -d= -f2)
        log_info "Certificado expira: $EXPIRY"
    fi
else
    log_warning "Certificados SSL no encontrados - Se generarán durante deploy"
fi

# Resumen
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📊 RESUMEN DE VALIDACIÓN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [[ $ERRORS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
    log_success "✅ TODO PERFECTO - Listo para deploy"
    exit 0
elif [[ $ERRORS -eq 0 ]]; then
    echo -e "${YELLOW}⚠️  $WARNINGS advertencias encontradas${NC}"
    echo ""
    echo "Podés proceder con el deploy, pero revisá las advertencias."
    exit 0
else
    echo -e "${RED}❌ $ERRORS errores encontrados${NC}"
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  $WARNINGS advertencias encontradas${NC}"
    fi
    echo ""
    echo "Corregí los errores antes de hacer deploy."
    exit 1
fi
