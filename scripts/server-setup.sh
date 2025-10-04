#!/bin/bash
#
# Setup Script para Servidor Staging - Sistema MVP Alojamientos
#
# Este script automatiza la configuración inicial de un servidor Ubuntu 22.04
# para el despliegue de la aplicación.
#
# Uso:
#   bash server-setup.sh
#
# Ejecutar como root o con sudo
#

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
DOCKER_VERSION="24.0"
COMPOSE_VERSION="v2.23.0"

# Funciones de utilidad
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Este script debe ejecutarse como root"
        exit 1
    fi
}

# Verificar sistema operativo
check_os() {
    log_info "Verificando sistema operativo..."

    if [[ ! -f /etc/os-release ]]; then
        log_error "No se puede determinar el sistema operativo"
        exit 1
    fi

    source /etc/os-release

    if [[ "$ID" != "ubuntu" ]]; then
        log_error "Este script solo soporta Ubuntu. Detectado: $ID"
        exit 1
    fi

    if [[ "$VERSION_ID" != "22.04" ]] && [[ "$VERSION_ID" != "24.04" ]]; then
        log_warn "Versión de Ubuntu no testeada: $VERSION_ID. Recomendado: 22.04 LTS"
        read -p "¿Continuar de todas formas? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    log_info "Sistema operativo: Ubuntu $VERSION_ID ✓"
}

# Actualizar sistema
update_system() {
    log_info "Actualizando sistema..."

    apt-get update -qq
    apt-get upgrade -y -qq

    log_info "Sistema actualizado ✓"
}

# Instalar dependencias básicas
install_dependencies() {
    log_info "Instalando dependencias básicas..."

    apt-get install -y -qq \
        curl \
        git \
        vim \
        wget \
        htop \
        ufw \
        fail2ban \
        ca-certificates \
        gnupg \
        lsb-release \
        software-properties-common \
        apt-transport-https

    log_info "Dependencias instaladas ✓"
}

# Configurar firewall
setup_firewall() {
    log_info "Configurando firewall (UFW)..."

    # Resetear reglas previas
    ufw --force reset

    # Políticas por defecto
    ufw default deny incoming
    ufw default allow outgoing

    # Permitir SSH (CRÍTICO: no bloquear antes de habilitar)
    ufw allow OpenSSH
    ufw allow 22/tcp

    # Permitir HTTP y HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp

    # Habilitar firewall
    ufw --force enable

    # Verificar status
    ufw status

    log_info "Firewall configurado ✓"
}

# Configurar fail2ban
setup_fail2ban() {
    log_info "Configurando fail2ban..."

    # Copiar configuración local
    cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

    # Configurar jail para SSH
    cat > /etc/fail2ban/jail.d/sshd.local <<EOF
[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
backend = %(sshd_backend)s
maxretry = 3
bantime = 3600
findtime = 600
EOF

    # Reiniciar servicio
    systemctl restart fail2ban
    systemctl enable fail2ban

    # Verificar status
    fail2ban-client status

    log_info "fail2ban configurado ✓"
}

# Instalar Docker
install_docker() {
    log_info "Instalando Docker..."

    # Verificar si Docker ya está instalado
    if command -v docker &> /dev/null; then
        CURRENT_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
        log_warn "Docker ya está instalado: $CURRENT_VERSION"
        read -p "¿Reinstalar Docker? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Saltando instalación de Docker"
            return
        fi
    fi

    # Remover versiones antiguas
    apt-get remove -y -qq docker docker-engine docker.io containerd runc 2>/dev/null || true

    # Agregar repositorio oficial de Docker
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Instalar Docker
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Verificar instalación
    docker --version
    docker compose version

    # Iniciar y habilitar servicio
    systemctl start docker
    systemctl enable docker

    log_info "Docker instalado ✓"
}

# Configurar usuario para Docker (opcional)
configure_docker_user() {
    log_info "Configurando usuario para Docker..."

    # Pedir nombre de usuario
    read -p "Ingresa el nombre del usuario para Docker (o Enter para saltar): " DOCKER_USER

    if [[ -z "$DOCKER_USER" ]]; then
        log_info "Saltando configuración de usuario Docker"
        return
    fi

    # Verificar que el usuario existe
    if ! id "$DOCKER_USER" &>/dev/null; then
        log_error "El usuario $DOCKER_USER no existe"
        return 1
    fi

    # Agregar usuario al grupo docker
    usermod -aG docker "$DOCKER_USER"

    log_info "Usuario $DOCKER_USER agregado al grupo docker ✓"
    log_warn "El usuario debe hacer logout/login para que los cambios tomen efecto"
}

# Crear estructura de directorios
create_directories() {
    log_info "Creando estructura de directorios..."

    mkdir -p /opt/apps
    mkdir -p /var/log/alojamientos
    mkdir -p /var/backups/alojamientos

    # Permisos
    chmod 755 /opt/apps
    chmod 755 /var/log/alojamientos
    chmod 700 /var/backups/alojamientos

    log_info "Directorios creados ✓"
}

# Configurar swapfile (opcional pero recomendado)
setup_swap() {
    log_info "Configurando swapfile..."

    # Verificar si ya existe swap
    if swapon --show | grep -q '/swapfile'; then
        log_warn "Swapfile ya existe"
        return
    fi

    # Crear swapfile de 2GB
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile

    # Hacer permanente
    if ! grep -q '/swapfile' /etc/fstab; then
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
    fi

    # Configurar swappiness
    sysctl vm.swappiness=10
    echo 'vm.swappiness=10' >> /etc/sysctl.conf

    log_info "Swapfile configurado ✓"
}

# Configurar límites del sistema
configure_limits() {
    log_info "Configurando límites del sistema..."

    # Aumentar file descriptors
    cat >> /etc/security/limits.conf <<EOF

# Aumentar límites para aplicación
* soft nofile 65536
* hard nofile 65536
* soft nproc 65536
* hard nproc 65536
EOF

    # Configurar kernel parameters
    cat >> /etc/sysctl.conf <<EOF

# Optimizaciones para servidor web
net.core.somaxconn = 65536
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15
EOF

    # Aplicar cambios
    sysctl -p

    log_info "Límites configurados ✓"
}

# Instalar herramientas de monitoreo
install_monitoring_tools() {
    log_info "Instalando herramientas de monitoreo..."

    apt-get install -y -qq \
        htop \
        iotop \
        nethogs \
        ncdu \
        glances

    log_info "Herramientas de monitoreo instaladas ✓"
}

# Configurar timezone
setup_timezone() {
    log_info "Configurando timezone..."

    # Preguntar timezone
    echo "Timezones comunes:"
    echo "  1) America/Argentina/Buenos_Aires"
    echo "  2) America/Mexico_City"
    echo "  3) America/Bogota"
    echo "  4) America/Santiago"
    echo "  5) UTC"
    read -p "Selecciona timezone (1-5, o Enter para mantener actual): " TZ_CHOICE

    case $TZ_CHOICE in
        1) TIMEZONE="America/Argentina/Buenos_Aires" ;;
        2) TIMEZONE="America/Mexico_City" ;;
        3) TIMEZONE="America/Bogota" ;;
        4) TIMEZONE="America/Santiago" ;;
        5) TIMEZONE="UTC" ;;
        *)
            log_info "Manteniendo timezone actual: $(timedatectl | grep "Time zone" | awk '{print $3}')"
            return
            ;;
    esac

    timedatectl set-timezone "$TIMEZONE"

    log_info "Timezone configurado: $TIMEZONE ✓"
}

# Resumen final
print_summary() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  ✅ SETUP COMPLETADO EXITOSAMENTE"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Resumen de instalación:"
    echo "  • Sistema operativo: $(lsb_release -d | cut -f2)"
    echo "  • Docker: $(docker --version | awk '{print $3}')"
    echo "  • Docker Compose: $(docker compose version | awk '{print $4}')"
    echo "  • Firewall: Activo (SSH, HTTP, HTTPS permitidos)"
    echo "  • fail2ban: Activo (protección SSH)"
    echo "  • Swap: $(free -h | grep Swap | awk '{print $2}')"
    echo ""
    echo "Próximos pasos:"
    echo "  1. Clonar repositorio en /opt/apps:"
    echo "     cd /opt/apps"
    echo "     git clone git@github.com:eevans-d/SIST_CABANAS_MVP.git"
    echo ""
    echo "  2. Configurar variables de entorno:"
    echo "     cd SIST_CABANAS_MVP"
    echo "     cp .env.template .env"
    echo "     nano .env"
    echo ""
    echo "  3. Ejecutar deploy:"
    echo "     bash scripts/deploy.sh"
    echo ""
    echo "  4. Configurar SSL:"
    echo "     sudo certbot certonly --standalone -d staging.tudominio.com"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo ""
}

# Main
main() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  🚀 Setup de Servidor Staging"
    echo "  Sistema MVP Alojamientos v0.9.9"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    check_root
    check_os

    log_info "Iniciando setup del servidor..."
    echo ""

    # Ejecutar pasos
    update_system
    install_dependencies
    setup_firewall
    setup_fail2ban
    install_docker
    configure_docker_user
    create_directories
    setup_swap
    configure_limits
    install_monitoring_tools
    setup_timezone

    # Resumen
    print_summary

    log_info "Setup completado exitosamente! 🎉"
}

# Ejecutar
main "$@"
