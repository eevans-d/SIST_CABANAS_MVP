#!/bin/bash

# 🚀 Deploy Script - Sistema Alojamientos MVP
# ==========================================
# Script para deployment en producción con Docker Compose + Nginx + SSL

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
DOMAIN="${DOMAIN:-alojamientos.example.com}"
EMAIL="${EMAIL:-admin@example.com}"
BACKUP_DIR="/opt/backups/alojamientos"
COMPOSE_FILE="docker-compose.yml"

# Funciones de utilidad
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Verificando requisitos del sistema..."

    # Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        exit 1
    fi

    # Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose no está instalado"
        exit 1
    fi

    # Certbot (para SSL)
    if ! command -v certbot &> /dev/null; then
        log_warning "Certbot no encontrado, instalando..."
        sudo apt update && sudo apt install -y certbot python3-certbot-nginx
    fi

    log_success "Requisitos verificados"
}

setup_ssl() {
    log_info "Configurando certificados SSL para $DOMAIN..."

    # Crear directorio SSL
    sudo mkdir -p ./ssl

    # Verificar si ya existen certificados
    if [[ -f "./ssl/fullchain.pem" && -f "./ssl/privkey.pem" ]]; then
        log_success "Certificados SSL ya existen"
        return 0
    fi

    # Generar certificado temporal para primer arranque
    log_info "Generando certificado temporal..."
    sudo openssl req -x509 -nodes -days 1 -newkey rsa:2048 \
        -keyout ./ssl/privkey.pem \
        -out ./ssl/fullchain.pem \
        -subj "/C=AR/ST=Buenos Aires/L=Buenos Aires/O=Alojamientos/CN=$DOMAIN"

    # Arrancar nginx temporalmente para validación
    log_info "Arrancando nginx temporal para validación Let's Encrypt..."
    docker-compose up -d nginx
    sleep 10

    # Obtener certificado real de Let's Encrypt
    log_info "Obteniendo certificado Let's Encrypt..."
    sudo certbot certonly --webroot \
        --webroot-path=/var/www/html \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN

    # Copiar certificados
    sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ./ssl/
    sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ./ssl/
    sudo chown $(whoami):$(whoami) ./ssl/*.pem

    log_success "Certificados SSL configurados"
}

validate_env() {
    log_info "Validando variables de entorno..."

    if [[ ! -f ".env" ]]; then
        log_error "Archivo .env no encontrado. Crear desde .env.template"
        exit 1
    fi

    # Variables críticas
    required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "JWT_SECRET"
        "WHATSAPP_ACCESS_TOKEN"
        "WHATSAPP_APP_SECRET"
        "MERCADOPAGO_ACCESS_TOKEN"
    )

    source .env

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Variable $var no está configurada en .env"
            exit 1
        fi
    done

    # Verificar que no sean valores por defecto
    if [[ "$POSTGRES_PASSWORD" == "change_this_secure_password" ]]; then
        log_error "POSTGRES_PASSWORD sigue siendo el valor por defecto"
        exit 1
    fi

    if [[ "$REDIS_PASSWORD" == "change_this_redis_password" ]]; then
        log_error "REDIS_PASSWORD sigue siendo el valor por defecto"
        exit 1
    fi

    log_success "Variables de entorno validadas"
}

setup_backup() {
    log_info "Configurando sistema de backups..."

    sudo mkdir -p $BACKUP_DIR

    # Script de backup
    cat > backup.sh << 'EOF'
#!/bin/bash
# Backup automático PostgreSQL + Redis

BACKUP_DIR="/opt/backups/alojamientos"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker-compose exec -T db pg_dump -U alojamientos alojamientos_db | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Backup Redis
docker-compose exec -T redis redis-cli --rdb /data/dump.rdb
docker cp alojamientos_redis:/data/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"

# Limpiar backups antiguos (mantener 30 días)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete

echo "Backup completado: $DATE"
EOF

    chmod +x backup.sh

    # Crontab para backup diario a las 2 AM
    (crontab -l 2>/dev/null; echo "0 2 * * * $(pwd)/backup.sh") | crontab -

    log_success "Sistema de backups configurado"
}

deploy() {
    log_info "Iniciando deploy..."

    # Pull última versión del código
    if [[ -d ".git" ]]; then
        git pull origin main
    fi

    # Build imágenes
    log_info "Construyendo imágenes Docker..."
    docker-compose build

    # Detener servicios existentes
    log_info "Deteniendo servicios existentes..."
    docker-compose down || true

    # Arrancar servicios
    log_info "Arrancando servicios..."
    docker-compose up -d

    # Esperar que los servicios estén listos
    log_info "Esperando que los servicios estén listos..."
    sleep 30

    # Verificar salud de servicios
    log_info "Verificando salud de servicios..."

    # PostgreSQL
    if docker-compose exec db pg_isready -U alojamientos -d alojamientos_db; then
        log_success "PostgreSQL: OK"
    else
        log_error "PostgreSQL: FAILED"
        exit 1
    fi

    # Redis
    if docker-compose exec redis redis-cli ping | grep -q PONG; then
        log_success "Redis: OK"
    else
        log_error "Redis: FAILED"
        exit 1
    fi

    # API Health
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_success "API Health: OK"
    else
        log_error "API Health: FAILED"
        exit 1
    fi

    log_success "Deploy completado exitosamente!"
}

rollback() {
    log_warning "Iniciando rollback..."

    # Obtener backup más reciente
    LATEST_DB_BACKUP=$(ls -t $BACKUP_DIR/postgres_*.sql.gz | head -1)
    LATEST_REDIS_BACKUP=$(ls -t $BACKUP_DIR/redis_*.rdb | head -1)

    if [[ -z "$LATEST_DB_BACKUP" ]]; then
        log_error "No se encontró backup de base de datos"
        exit 1
    fi

    log_info "Restaurando desde: $LATEST_DB_BACKUP"

    # Detener servicios
    docker-compose down

    # Restaurar PostgreSQL
    docker-compose up -d db
    sleep 10
    zcat "$LATEST_DB_BACKUP" | docker-compose exec -T db psql -U alojamientos -d alojamientos_db

    # Restaurar Redis si existe backup
    if [[ -n "$LATEST_REDIS_BACKUP" ]]; then
        docker cp "$LATEST_REDIS_BACKUP" alojamientos_redis:/data/dump.rdb
    fi

    # Arrancar todos los servicios
    docker-compose up -d

    log_success "Rollback completado"
}

# Menú principal
case "${1:-}" in
    "deploy")
        check_requirements
        validate_env
        setup_ssl
        setup_backup
        deploy
        ;;
    "rollback")
        rollback
        ;;
    "backup")
        ./backup.sh
        ;;
    "logs")
        docker-compose logs -f "${2:-}"
        ;;
    "status")
        docker-compose ps
        curl -s http://localhost/health | jq .
        ;;
    "update-ssl")
        certbot renew --quiet
        docker-compose restart nginx
        ;;
    *)
        echo "Uso: $0 {deploy|rollback|backup|logs|status|update-ssl}"
        echo ""
        echo "deploy    - Deploy completo en producción"
        echo "rollback  - Rollback al último backup"
        echo "backup    - Ejecutar backup manual"
        echo "logs      - Ver logs (opcional: servicio específico)"
        echo "status    - Ver estado de servicios"
        echo "update-ssl - Renovar certificados SSL"
        exit 1
        ;;
esac
