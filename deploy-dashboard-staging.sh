#!/bin/bash

# Deploy Script para Dashboard Admin - Staging
# Uso: ./deploy-dashboard-staging.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funciones helper
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║         Deploy Dashboard Admin - Staging Environment         ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# 1. Verificar prerequisitos
log_info "Verificando prerequisitos..."

if ! command -v docker &> /dev/null; then
    log_error "Docker no está instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose no está instalado"
    exit 1
fi

log_info "✓ Docker y Docker Compose encontrados"

# 2. Verificar archivos necesarios
log_info "Verificando archivos necesarios..."

REQUIRED_FILES=(
    "docker-compose.yml"
    "docker-compose.dashboard.yml"
    "frontend/admin-dashboard/Dockerfile"
    "frontend/admin-dashboard/package.json"
    ".env"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        log_error "Archivo requerido no encontrado: $file"
        exit 1
    fi
done

log_info "✓ Todos los archivos necesarios presentes"

# 3. Crear .env para frontend si no existe
if [ ! -f "frontend/admin-dashboard/.env" ]; then
    log_warn ".env del frontend no encontrado, copiando desde .env.example"
    cp frontend/admin-dashboard/.env.example frontend/admin-dashboard/.env
fi

# 4. Build del frontend
log_info "Construyendo imagen del frontend..."
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml build admin-dashboard

if [ $? -ne 0 ]; then
    log_error "Falló el build del frontend"
    exit 1
fi

log_info "✓ Frontend construido exitosamente"

# 5. Detener contenedores existentes
log_info "Deteniendo contenedores existentes..."
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml down

# 6. Levantar servicios
log_info "Levantando servicios..."
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml up -d

if [ $? -ne 0 ]; then
    log_error "Falló al levantar los servicios"
    exit 1
fi

# 7. Esperar health checks
log_info "Esperando health checks (30s)..."
sleep 30

# 8. Verificar servicios
log_info "Verificando servicios..."

# Check backend
if ! docker ps | grep -q "alojamientos_api"; then
    log_error "Backend no está corriendo"
    exit 1
fi

# Check frontend
if ! docker ps | grep -q "alojamientos_admin_dashboard"; then
    log_error "Frontend no está corriendo"
    exit 1
fi

log_info "✓ Todos los servicios están corriendo"

# 9. Mostrar URLs
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║                   ✅ DEPLOY EXITOSO ✅                        ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
log_info "URLs disponibles:"
echo "  • Admin Dashboard: http://localhost:3000"
echo "  • Backend API:     http://localhost:8000"
echo "  • API Docs:        http://localhost:8000/docs"
echo ""
log_info "Ver logs:"
echo "  docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml logs -f"
echo ""
log_info "Detener servicios:"
echo "  docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml down"
echo ""
