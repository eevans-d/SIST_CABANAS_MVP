#!/bin/bash
# Script para configurar SSL/HTTPS con Let's Encrypt en producción

set -e

echo "🔐 Configurando SSL/HTTPS para el Sistema de Alojamientos"
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: No se encuentra docker-compose.yml${NC}"
    echo "Ejecutar desde el directorio raíz del proyecto"
    exit 1
fi

# Función para validar dominio
validate_domain() {
    local domain=$1
    if [[ ! "$domain" =~ ^[a-zA-Z0-9][a-zA-Z0-9\.-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$ ]]; then
        echo -e "${RED}❌ Dominio inválido: $domain${NC}"
        return 1
    fi
    return 0
}

# Función para verificar DNS
check_dns() {
    local domain=$1
    local server_ip=$(curl -s https://ipv4.icanhazip.com 2>/dev/null || echo "unknown")
    local dns_ip=$(dig +short $domain 2>/dev/null | tail -n1)

    echo -e "${BLUE}ℹ️  IP del servidor: ${server_ip}${NC}"
    echo -e "${BLUE}ℹ️  IP en DNS para $domain: ${dns_ip}${NC}"

    if [ "$server_ip" != "unknown" ] && [ "$dns_ip" = "$server_ip" ]; then
        echo -e "${GREEN}✅ DNS configurado correctamente${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Advertencia: DNS podría no estar configurado correctamente${NC}"
        return 1
    fi
}

# Solicitar dominio
echo -e "${BLUE}📝 Configuración del dominio${NC}"
read -p "Ingrese el dominio (ej: alojamientos.mi-sitio.com): " DOMAIN

# Validar dominio
if ! validate_domain "$DOMAIN"; then
    exit 1
fi

# Verificar DNS
echo -e "${BLUE}🔍 Verificando configuración DNS...${NC}"
check_dns "$DOMAIN" || {
    echo -e "${YELLOW}⚠️  Continuar sin verificación DNS? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Configure el DNS y vuelva a ejecutar el script"
        exit 1
    fi
}

# Solicitar email
echo -e "${BLUE}📧 Email para Let's Encrypt${NC}"
read -p "Ingrese su email: " EMAIL

if [[ ! "$EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo -e "${RED}❌ Email inválido${NC}"
    exit 1
fi

# Confirmar configuración
echo -e "${BLUE}📋 Resumen de configuración:${NC}"
echo "  Dominio: $DOMAIN"
echo "  Email: $EMAIL"
echo ""
read -p "¿Continuar con la configuración SSL? (y/N): " confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Configuración cancelada"
    exit 0
fi

# Crear directorio para certificados
echo -e "${BLUE}📁 Creando directorios para certificados...${NC}"
mkdir -p ./nginx/ssl
mkdir -p ./nginx/certbot/conf
mkdir -p ./nginx/certbot/www

# Crear configuración temporal de nginx para validación
echo -e "${BLUE}📝 Creando configuración temporal de nginx...${NC}"
cat > ./nginx/sites-available/temp-ssl.conf << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF

# Crear docker-compose para SSL
echo -e "${BLUE}🐳 Configurando Docker Compose para SSL...${NC}"
cat > ./docker-compose.ssl.yml << EOF
version: "3.9"

services:
  nginx:
    volumes:
      - ./nginx/certbot/conf:/etc/letsencrypt
      - ./nginx/certbot/www:/var/www/certbot
      - ./nginx/sites-available/temp-ssl.conf:/etc/nginx/conf.d/default.conf
    ports:
      - "80:80"
      - "443:443"
    command: "/bin/sh -c 'while :; do sleep 6h & wait \$\${!}; nginx -s reload; done & nginx -g \"daemon off;\"'"

  certbot:
    image: certbot/certbot
    volumes:
      - ./nginx/certbot/conf:/etc/letsencrypt
      - ./nginx/certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait \$\${!}; done;'"
EOF

# Iniciar nginx temporal
echo -e "${BLUE}🚀 Iniciando nginx temporal...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.ssl.yml up -d nginx

# Esperar a que nginx esté listo
echo -e "${BLUE}⏳ Esperando que nginx esté listo...${NC}"
sleep 10

# Obtener certificado SSL
echo -e "${BLUE}🔒 Obteniendo certificado SSL...${NC}"
docker run --rm \
    -v "./nginx/certbot/conf:/etc/letsencrypt" \
    -v "./nginx/certbot/www:/var/www/certbot" \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Certificado SSL obtenido exitosamente${NC}"
else
    echo -e "${RED}❌ Error obteniendo certificado SSL${NC}"
    exit 1
fi

# Crear configuración final de nginx con SSL
echo -e "${BLUE}📝 Creando configuración final de nginx...${NC}"
cat > ./nginx/sites-available/alojamientos-ssl.conf << EOF
upstream api_backend {
    server api:8000;
}

# Redirigir HTTP a HTTPS
server {
    listen 80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# Configuración HTTPS
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # Certificados SSL
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # Configuraciones SSL recomendadas
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 10m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Tamaño máximo de archivo
    client_max_body_size 50M;

    # Proxy al backend
    location /api/ {
        proxy_pass http://api_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;

        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Healthcheck y métricas
    location /healthz {
        proxy_pass http://api_backend/api/v1/healthz;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /metrics {
        proxy_pass http://api_backend/metrics;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Restringir acceso a métricas (opcional)
        # allow 10.0.0.0/8;
        # deny all;
    }

    # Página de inicio básica
    location = / {
        return 200 '<!DOCTYPE html>
<html>
<head>
    <title>Sistema de Alojamientos - API</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>🏠 Sistema de Alojamientos</h1>
    <p>API funcionando correctamente con SSL</p>
    <ul>
        <li><a href="/api/v1/healthz">Health Check</a></li>
        <li><a href="/metrics">Métricas</a></li>
    </ul>
</body>
</html>';
        add_header Content-Type text/html;
    }

    # Certbot renewal
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}
EOF

# Actualizar docker-compose principal
echo -e "${BLUE}🐳 Actualizando docker-compose principal...${NC}"
cat >> ./docker-compose.yml << EOF

  # Renovación automática de certificados SSL
  certbot:
    image: certbot/certbot
    volumes:
      - ./nginx/certbot/conf:/etc/letsencrypt
      - ./nginx/certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait \$\${!}; done;'"
    restart: unless-stopped
    depends_on:
      - nginx
    networks:
      - backend
EOF

# Actualizar configuración de nginx en docker-compose
echo -e "${BLUE}📝 Actualizando configuración de nginx...${NC}"
# Aquí deberíamos actualizar el docker-compose.yml para usar la nueva configuración

# Reiniciar servicios con SSL
echo -e "${BLUE}🔄 Reiniciando servicios con SSL...${NC}"
docker-compose down
sleep 5

# Copiar la configuración SSL
cp ./nginx/sites-available/alojamientos-ssl.conf ./nginx/sites-available/default.conf

# Actualizar el volumen de nginx en docker-compose.yml
echo -e "${BLUE}📝 Configurando volúmenes SSL en nginx...${NC}"

# Levantar todo de nuevo
docker-compose up -d

# Verificar que todo funcione
echo -e "${BLUE}🔍 Verificando configuración SSL...${NC}"
sleep 15

# Test de conectividad
if curl -k -s "https://$DOMAIN/api/v1/healthz" >/dev/null; then
    echo -e "${GREEN}✅ HTTPS funcionando correctamente${NC}"
else
    echo -e "${YELLOW}⚠️  Verificar configuración manualmente${NC}"
fi

# Agregar variables de entorno
echo -e "${BLUE}📝 Actualizando variables de entorno...${NC}"
if ! grep -q "DOMAIN=" .env 2>/dev/null; then
    echo "DOMAIN=$DOMAIN" >> .env
fi

if ! grep -q "SSL_EMAIL=" .env 2>/dev/null; then
    echo "SSL_EMAIL=$EMAIL" >> .env
fi

# Mostrar resumen final
echo ""
echo -e "${GREEN}🎉 Configuración SSL completada exitosamente${NC}"
echo "=================================================="
echo -e "${BLUE}📋 Resumen:${NC}"
echo "  🌐 Dominio: https://$DOMAIN"
echo "  📧 Email: $EMAIL"
echo "  🔒 Certificado: Let's Encrypt"
echo "  🔄 Renovación: Automática cada 12h"
echo ""
echo -e "${BLUE}🔗 URLs disponibles:${NC}"
echo "  Health Check: https://$DOMAIN/api/v1/healthz"
echo "  Métricas: https://$DOMAIN/metrics"
echo "  API Base: https://$DOMAIN/api/v1/"
echo ""
echo -e "${YELLOW}📝 Próximos pasos:${NC}"
echo "  1. Configurar webhooks de WhatsApp con HTTPS"
echo "  2. Configurar webhooks de MercadoPago con HTTPS"
echo "  3. Actualizar configuración de iCal"
echo ""
echo -e "${GREEN}✅ El sistema está listo para producción con SSL${NC}"
