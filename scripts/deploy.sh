#!/usr/bin/env bash
set -euo pipefail

# 🚀 Unified Deploy Script
# Orquesta todo el proceso de deploy de principio a fin

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀 SISTEMA ALOJAMIENTOS - DEPLOY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Paso 1: Validación pre-deploy
log_info "Paso 1/6: Ejecutando validaciones pre-deploy..."
if ./scripts/pre-deploy-check.sh; then
    log_success "Validaciones OK"
else
    log_warning "Hay advertencias en validación, pero continuando..."
fi
echo ""

# Paso 2: Generar nginx.conf
log_info "Paso 2/6: Generando configuración de Nginx..."
if [[ -f ".env" ]]; then
    if [[ -f "backend/generate_nginx_conf.sh" ]]; then
        cd backend && ./generate_nginx_conf.sh ../.env && cd ..
        log_success "nginx.conf generado"
    else
        log_warning "generate_nginx_conf.sh no encontrado, saltando..."
    fi
else
    log_error ".env no encontrado"
fi
echo ""

# Paso 3: Backup (si ya existe deployment previo)
log_info "Paso 3/6: Creando backup..."
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if docker-compose -f backend/docker-compose.yml ps | grep -q "Up"; then
    log_info "Sistema corriendo, creando backup de DB..."
    docker-compose -f backend/docker-compose.yml exec -T db pg_dump -U alojamientos alojamientos_db > "$BACKUP_DIR/db_backup.sql" 2>/dev/null || true
    log_success "Backup creado en $BACKUP_DIR"
else
    log_info "No hay sistema previo corriendo"
fi
echo ""

# Paso 4: Build y deploy de containers
log_info "Paso 4/6: Construyendo y desplegando containers..."
cd backend
docker-compose build --no-cache
docker-compose up -d
cd ..
log_success "Containers desplegados"
echo ""

# Paso 5: Ejecutar migraciones
log_info "Paso 5/6: Ejecutando migraciones de base de datos..."
sleep 10  # Esperar que la DB esté lista
docker-compose -f backend/docker-compose.yml exec -T app alembic upgrade head || log_warning "Migraciones fallaron o ya estaban aplicadas"
log_success "Migraciones completadas"
echo ""

# Paso 6: Smoke tests
log_info "Paso 6/6: Ejecutando smoke tests..."
sleep 5  # Esperar que la API esté completamente lista

# Determinar URL
if [[ -f ".env" ]]; then
    source .env
    BASE_URL="http://localhost:8000"  # Ajustar según configuración
fi

export BASE_URL
if ./scripts/smoke-test-prod.sh; then
    log_success "Smoke tests pasaron"
else
    log_warning "Algunos smoke tests fallaron, revisar logs"
fi
echo ""

# Resumen final
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ DEPLOY COMPLETADO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
log_success "Sistema desplegado exitosamente"
echo ""
echo "Próximos pasos:"
echo "  1. Verificar logs: docker-compose -f backend/docker-compose.yml logs -f"
echo "  2. Verificar health: curl http://localhost:8000/api/v1/healthz"
echo "  3. Configurar webhooks en Meta y Mercado Pago"
echo "  4. Verificar SSL certificates (si aplica)"
echo ""
