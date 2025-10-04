# 🚀 Guía de Deploy a Staging - Sistema MVP Alojamientos

**Versión:** v1.0
**Fecha:** 4 de Octubre, 2025
**Duración estimada:** 2-3 horas
**Nivel:** Intermedio

---

## 📋 Tabla de Contenidos

1. [Pre-requisitos](#pre-requisitos)
2. [Provisión del Servidor](#provisión-del-servidor)
3. [Configuración Inicial del Servidor](#configuración-inicial-del-servidor)
4. [Deploy de la Aplicación](#deploy-de-la-aplicación)
5. [Configuración de SSL](#configuración-de-ssl)
6. [Verificación Post-Deploy](#verificación-post-deploy)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Pre-requisitos

### En tu máquina local:

- [ ] Git configurado con acceso al repo
- [ ] SSH key generada (`~/.ssh/id_rsa.pub`)
- [ ] Docker instalado (para build local si es necesario)
- [ ] Dominio registrado con acceso a DNS

### Información que necesitarás:

- [ ] IP del servidor staging
- [ ] Dominio o subdominio (ej: `staging.alojamientos.com`)
- [ ] Credenciales de WhatsApp Business API
- [ ] Credenciales de Mercado Pago (sandbox)
- [ ] Credenciales SMTP para emails

---

## 🖥️ Provisión del Servidor

### Opción A: DigitalOcean (Recomendado para MVP)

```bash
# Specs mínimas para staging:
# - 2 vCPUs
# - 2 GB RAM
# - 50 GB SSD
# - Ubuntu 22.04 LTS

# 1. Crear Droplet desde el panel web
# 2. Seleccionar Ubuntu 22.04
# 3. Agregar tu SSH key
# 4. Habilitar backups semanales
# 5. Seleccionar región más cercana a tus usuarios
```

**Costo aproximado:** $12-18 USD/mes

### Opción B: AWS EC2

```bash
# Instance type: t3.small
# AMI: Ubuntu 22.04 LTS
# Storage: 30 GB gp3
# Security Group: Abrir puertos 22, 80, 443
```

### Opción C: Hetzner Cloud (Más económico)

```bash
# Cloud Server CX21
# 2 vCPU, 4 GB RAM, 40 GB SSD
# ~€5.50/mes (~$6 USD)
```

### Configurar DNS

Una vez que tengas la IP del servidor:

```bash
# En tu proveedor de DNS (Cloudflare, NameCheap, etc.)
# Agregar registro A:

staging.alojamientos.com  A  <IP_DEL_SERVIDOR>

# Verificar propagación (puede tardar 5-30 min)
dig staging.alojamientos.com +short
# Debe devolver la IP del servidor
```

---

## ⚙️ Configuración Inicial del Servidor

### 1. Conectarse al servidor

```bash
# Desde tu máquina local
ssh root@<IP_DEL_SERVIDOR>

# O si configuraste usuario personalizado
ssh ubuntu@<IP_DEL_SERVIDOR>
```

### 2. Actualizar sistema

```bash
# Actualizar paquetes
sudo apt update && sudo apt upgrade -y

# Instalar dependencias básicas
sudo apt install -y \
    curl \
    git \
    ufw \
    fail2ban \
    htop \
    vim \
    wget \
    ca-certificates \
    gnupg \
    lsb-release
```

### 3. Configurar firewall

```bash
# Habilitar UFW
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Verificar reglas
sudo ufw status
```

### 4. Instalar Docker

```bash
# Agregar repositorio oficial de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verificar instalación
docker --version
docker compose version

# Agregar usuario al grupo docker (opcional)
sudo usermod -aG docker $USER
newgrp docker
```

### 5. Configurar fail2ban (protección SSH)

```bash
# Configurar jail para SSH
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Editar configuración
sudo nano /etc/fail2ban/jail.local

# Buscar [sshd] y asegurar:
# enabled = true
# maxretry = 3
# bantime = 3600

# Reiniciar servicio
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
```

---

## 📦 Deploy de la Aplicación

### 1. Clonar el repositorio

```bash
# Crear directorio de aplicaciones
sudo mkdir -p /opt/apps
sudo chown $USER:$USER /opt/apps

# Clonar repo (necesitarás SSH key o PAT configurado)
cd /opt/apps
git clone git@github.com:eevans-d/SIST_CABANAS_MVP.git
cd SIST_CABANAS_MVP

# Verificar branch
git branch
```

### 2. Configurar variables de entorno

```bash
# Copiar template
cp .env.template .env

# Editar con valores de staging
nano .env
```

**Variables CRÍTICAS para staging:**

```bash
# Entorno
ENVIRONMENT=staging

# Dominio
DOMAIN=staging.alojamientos.com

# Base de datos
DB_HOST=postgres
DB_PORT=5432
DB_NAME=alojamientos_staging
DB_USER=alojamientos
DB_PASSWORD=<GENERAR_PASSWORD_SEGURO>  # Usar: openssl rand -base64 32

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<GENERAR_PASSWORD_SEGURO>

# JWT
JWT_SECRET=<GENERAR_SECRET_64_CHARS>  # Usar: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=10080  # 7 días

# iCal
ICS_SALT=<GENERAR_SALT_32_CHARS>

# WhatsApp (usar sandbox/test)
WHATSAPP_BUSINESS_ACCOUNT_ID=<TU_ID>
WHATSAPP_PHONE_NUMBER_ID=<TU_PHONE_ID>
WHATSAPP_ACCESS_TOKEN=<TU_TOKEN>
WHATSAPP_VERIFY_TOKEN=<GENERAR_TOKEN>  # openssl rand -hex 16
WHATSAPP_APP_SECRET=<TU_APP_SECRET>

# Mercado Pago (SANDBOX)
MERCADOPAGO_ACCESS_TOKEN=TEST-<TU_TOKEN>
MERCADOPAGO_PUBLIC_KEY=TEST-<TU_PUBLIC_KEY>
MERCADOPAGO_WEBHOOK_SECRET=<GENERAR_SECRET>

# Email (puede ser Gmail con App Password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<TU_EMAIL>
SMTP_PASSWORD=<APP_PASSWORD>
SMTP_FROM_EMAIL=staging@alojamientos.com
SMTP_FROM_NAME="Alojamientos Staging"

# URLs base
BASE_URL=https://staging.alojamientos.com
FRONTEND_URL=https://staging.alojamientos.com

# Rate limiting (más permisivo en staging)
RATE_LIMIT_PER_MINUTE=120

# Logs
LOG_LEVEL=INFO
```

**Generar passwords seguros:**

```bash
# Password DB
openssl rand -base64 32

# Password Redis
openssl rand -base64 32

# JWT Secret
openssl rand -hex 32

# iCal Salt
openssl rand -hex 16

# WhatsApp Verify Token
openssl rand -hex 16

# MP Webhook Secret
openssl rand -hex 32
```

### 3. Verificar configuración de Docker

```bash
# Revisar docker-compose.yml
cat docker-compose.yml

# Verificar que los puertos están correctos
# - API: 8000:8000
# - Postgres: NO expuesto externamente (comentar ports si está expuesto)
# - Redis: NO expuesto externamente
```

### 4. Build y deploy inicial

```bash
# Verificar pre-requisitos
bash scripts/pre-deploy-check.sh

# Build de imágenes
docker compose build

# Levantar servicios
docker compose up -d

# Verificar que todos los contenedores están corriendo
docker compose ps

# Debería mostrar:
# alojamientos_postgres  running
# alojamientos_redis     running
# alojamientos_api       running
# alojamientos_nginx     running (si existe)
```

### 5. Ejecutar migraciones

```bash
# Ejecutar migraciones de Alembic
docker compose exec api alembic upgrade head

# Verificar que las tablas fueron creadas
docker compose exec postgres psql -U alojamientos -d alojamientos_staging -c "\dt"

# Debería mostrar:
# accommodations
# reservations
# payments
# alembic_version
```

### 6. Seed de datos inicial (opcional)

```bash
# Si tienes script de seed
docker compose exec api python -m app.scripts.seed_data

# O crear manualmente un alojamiento de prueba
docker compose exec api python -c "
from app.core.database import get_db_session
from app.models.accommodation import Accommodation
# ... crear accommodation ...
"
```

---

## 🔐 Configuración de SSL

### Opción A: Let's Encrypt con Certbot (RECOMENDADO)

```bash
# Instalar certbot
sudo apt install -y certbot python3-certbot-nginx

# Detener Nginx si está corriendo
docker compose stop nginx  # Si existe contenedor nginx

# Obtener certificado
sudo certbot certonly --standalone \
    -d staging.alojamientos.com \
    --non-interactive \
    --agree-tos \
    --email tu@email.com

# Certificados se guardan en:
# /etc/letsencrypt/live/staging.alojamientos.com/fullchain.pem
# /etc/letsencrypt/live/staging.alojamientos.com/privkey.pem

# Configurar renovación automática
sudo certbot renew --dry-run
```

### Configurar Nginx

```bash
# Editar configuración de Nginx
nano nginx/nginx.conf
```

**nginx/nginx.conf para staging:**

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log warn;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript;

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name staging.alojamientos.com;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name staging.alojamientos.com;

        # SSL certificates
        ssl_certificate /etc/letsencrypt/live/staging.alojamientos.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/staging.alojamientos.com/privkey.pem;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers on;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;

            proxy_pass http://api:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Health check (bypass rate limit)
        location /api/v1/healthz {
            proxy_pass http://api:8000;
            proxy_set_header Host $host;
            access_log off;
        }

        # Metrics (solo desde IPs internas)
        location /metrics {
            allow 10.0.0.0/8;
            allow 172.16.0.0/12;
            allow 192.168.0.0/16;
            deny all;

            proxy_pass http://api:8000;
            proxy_set_header Host $host;
        }

        # Root
        location / {
            return 200 '{"status": "Staging API Running", "version": "0.9.9"}';
            add_header Content-Type application/json;
        }
    }
}
```

### Actualizar docker-compose.yml para Nginx

```bash
# Editar docker-compose.yml
nano docker-compose.yml
```

Agregar servicio nginx:

```yaml
  nginx:
    image: nginx:1.25-alpine
    container_name: alojamientos_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - /var/www/certbot:/var/www/certbot:ro
    depends_on:
      - api
    restart: unless-stopped
    networks:
      - backend
```

### Reiniciar servicios con Nginx

```bash
# Levantar Nginx
docker compose up -d

# Verificar logs
docker compose logs -f nginx
docker compose logs -f api
```

---

## ✅ Verificación Post-Deploy

### 1. Health Check

```bash
# Desde el servidor
curl -k https://staging.alojamientos.com/api/v1/healthz

# Desde tu máquina local
curl https://staging.alojamientos.com/api/v1/healthz

# Respuesta esperada:
{
  "status": "healthy",
  "timestamp": "2025-10-04T...",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "ical_sync": "ok"
  }
}
```

### 2. Verificar SSL

```bash
# Test SSL Labs
# Ir a: https://www.ssllabs.com/ssltest/
# Ingresar: staging.alojamientos.com
# Objetivo: Rating A o A+

# O desde CLI:
curl -I https://staging.alojamientos.com

# Verificar headers:
# Strict-Transport-Security: max-age=31536000
# X-Frame-Options: SAMEORIGIN
# X-Content-Type-Options: nosniff
```

### 3. Test de endpoints críticos

```bash
# Test webhook WhatsApp (GET para verificación)
curl "https://staging.alojamientos.com/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.challenge=test&hub.verify_token=<TU_VERIFY_TOKEN>"

# Debe devolver: test

# Test de creación de pre-reserva (requiere datos válidos)
curl -X POST https://staging.alojamientos.com/api/v1/reservations/prereserve \
  -H "Content-Type: application/json" \
  -d '{
    "accommodation_id": 1,
    "check_in": "2025-11-01",
    "check_out": "2025-11-03",
    "guests_count": 2,
    "guest_name": "Test User",
    "guest_phone": "+5491112345678",
    "guest_email": "test@example.com"
  }'
```

### 4. Verificar métricas

```bash
# Desde el servidor (o tunelizar para Prometheus)
curl http://localhost:8000/metrics | grep reservation

# Métricas esperadas:
# reservation_creations_total
# reservation_confirmations_total
# ical_last_sync_age_minutes
```

### 5. Verificar logs

```bash
# API logs
docker compose logs -f api | grep -i error

# Postgres logs
docker compose logs postgres | grep -i error

# Redis logs
docker compose logs redis | grep -i error

# Nginx logs
docker compose logs nginx | tail -100
```

### 6. Test de smoke completo

```bash
# Ejecutar suite de smoke tests
bash scripts/smoke-test-prod.sh staging.alojamientos.com

# O manualmente:
# 1. Health check ✓
# 2. Crear pre-reserva ✓
# 3. Consultar disponibilidad ✓
# 4. Test webhook WhatsApp ✓
# 5. Test webhook Mercado Pago ✓
```

---

## 🔧 Troubleshooting

### Problema: Contenedores no inician

```bash
# Ver logs detallados
docker compose logs api
docker compose logs postgres

# Común: Password de DB incorrecta
# Solución: Verificar .env y recrear contenedores
docker compose down -v  # CUIDADO: borra volúmenes
docker compose up -d
```

### Problema: Migraciones fallan

```bash
# Verificar conexión a DB
docker compose exec api python -c "from app.core.database import engine; print(engine)"

# Ejecutar migraciones con verbose
docker compose exec api alembic upgrade head --sql

# Si falla con constraint btree_gist:
docker compose exec postgres psql -U alojamientos -d alojamientos_staging
\c alojamientos_staging
CREATE EXTENSION IF NOT EXISTS btree_gist;
\q
```

### Problema: SSL no funciona

```bash
# Verificar certificados
sudo ls -la /etc/letsencrypt/live/staging.alojamientos.com/

# Renovar certificado
sudo certbot renew --force-renewal

# Verificar configuración de Nginx
docker compose exec nginx nginx -t

# Recargar configuración
docker compose restart nginx
```

### Problema: Webhooks no reciben eventos

```bash
# Verificar que el dominio resuelve correctamente
dig staging.alojamientos.com

# Test manual de webhook
curl -X POST https://staging.alojamientos.com/api/v1/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=<GENERAR_FIRMA>" \
  -d '{"object":"whatsapp_business_account","entry":[...]}'

# Verificar logs de API
docker compose logs -f api | grep webhook
```

### Problema: Rate limiting demasiado agresivo

```bash
# Ajustar temporalmente en nginx.conf
# Cambiar: rate=60r/m
# A: rate=120r/m

# Recargar Nginx
docker compose restart nginx
```

---

## 📊 Métricas de Éxito

Checklist post-deploy:

- [ ] Health check retorna `healthy`
- [ ] SSL Labs rating A o superior
- [ ] Todos los contenedores en estado `running`
- [ ] Migraciones ejecutadas exitosamente
- [ ] Logs sin errores críticos en últimos 5 minutos
- [ ] Webhook WhatsApp recibe verificación correctamente
- [ ] Pre-reserva de prueba se crea exitosamente
- [ ] Métricas `/metrics` accesibles
- [ ] Email de confirmación se envía (test manual)
- [ ] Backups automáticos configurados

---

## 🔗 Recursos Adicionales

- [Security Audit Checklist](../security/AUDIT_CHECKLIST.md)
- [Production Setup](../../PRODUCTION_SETUP.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)
- [API Reference](../API_REFERENCE.md)

---

## 📝 Próximos Pasos

Una vez que staging esté funcionando:

1. **Semana 2:** Configurar integraciones reales (WhatsApp, Mercado Pago)
2. **Semana 2:** Setup de monitoreo (Prometheus + Alertmanager)
3. **Semana 3:** User Acceptance Testing (UAT)
4. **Semana 3:** Deploy a producción

---

**¡Deploy exitoso!** 🎉

Si encuentras problemas, consulta el [Troubleshooting Guide](../TROUBLESHOOTING.md) o abre un issue en GitHub.
