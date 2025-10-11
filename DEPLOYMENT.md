# 🚢 Guía de Deployment - Producción

Guía paso a paso para desplegar el Sistema MVP de Reservas en producción.

## 📋 Pre-requisitos

- Servidor Linux (Ubuntu 22.04+ recomendado)
- Docker 24+ y Docker Compose 2.20+
- Dominio con DNS configurado
- Certificado SSL (Let's Encrypt)
- 2 GB RAM mínimo, 4 GB recomendado
- 20 GB espacio en disco

---

## 🔧 1. Preparación del Servidor

### Actualizar Sistema
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl vim htop
```

### Instalar Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Instalar Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## 📦 2. Clonar y Configurar

### Clonar Repositorio
```bash
cd /opt
sudo git clone https://github.com/eevans-d/SIST_CABANAS_MVP.git
cd SIST_CABANAS_MVP
sudo chown -R $USER:$USER .
```

### Configurar Variables de Entorno
```bash
cp backend/.env.template backend/.env
vim backend/.env
```

**Variables CRÍTICAS a configurar:**

```env
# AMBIENTE
ENVIRONMENT=production
DOMAIN=reservas.tudominio.com
ALLOWED_ORIGINS=https://reservas.tudominio.com

# DATABASE (usar valores seguros)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
DATABASE_URL=postgresql+asyncpg://alojamientos:${POSTGRES_PASSWORD}@postgres:5432/alojamientos_db

# REDIS
REDIS_PASSWORD=$(openssl rand -base64 32)
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# SEGURIDAD
JWT_SECRET=$(openssl rand -base64 48)
ICS_SALT=$(openssl rand -base64 24)

# WHATSAPP (Meta Developer Console)
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxx
WHATSAPP_PHONE_ID=123456789
WHATSAPP_APP_SECRET=abc123def456
WHATSAPP_VERIFY_TOKEN=$(openssl rand -base64 16)

# MERCADO PAGO
MERCADOPAGO_ACCESS_TOKEN=APP_USR-xxxxxxxxx
MERCADOPAGO_WEBHOOK_SECRET=$(openssl rand -base64 16)

# EMAIL (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASS=tu-app-password
SMTP_FROM=reservas@tudominio.com

# GUNICORN
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=60

# ADMIN
ADMIN_ALLOWED_EMAILS=admin@tudominio.com
```

---

## 🐳 3. Docker Compose Producción

### Crear docker-compose.prod.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: cabanas_postgres
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    container_name: cabanas_redis
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cabanas_backend
    restart: always
    env_file:
      - backend/.env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - backend
      - frontend
    volumes:
      - ./backend/app:/app/app:ro
      - audio_temp:/app/temp
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"

  nginx:
    image: nginx:alpine
    container_name: cabanas_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - backend
    networks:
      - frontend
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  certbot:
    image: certbot/certbot
    container_name: cabanas_certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

volumes:
  postgres_data:
  audio_temp:

networks:
  backend:
    driver: bridge
  frontend:
    driver: bridge
```

---

## 🔐 4. Configurar Nginx y SSL

### Crear nginx/conf.d/api.conf
```nginx
upstream backend_api {
    server backend:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name reservas.tudominio.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name reservas.tudominio.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/reservas.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/reservas.tudominio.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    # Client Body Size
    client_max_body_size 10M;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    # API Endpoints
    location /api/ {
        proxy_pass http://backend_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Docs (opcional: proteger con basic auth)
    location /docs {
        proxy_pass http://backend_api;
        proxy_set_header Host $host;
    }

    # Metrics (solo IP local)
    location /metrics {
        allow 127.0.0.1;
        deny all;
        proxy_pass http://backend_api;
    }

    # Health Check
    location /api/v1/healthz {
        proxy_pass http://backend_api;
        access_log off;
    }
}
```

### Obtener Certificado SSL
```bash
# Primera vez (HTTP challenge)
docker-compose -f docker-compose.prod.yml up -d nginx
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path /var/www/certbot \
  -d reservas.tudominio.com \
  --email admin@tudominio.com \
  --agree-tos \
  --no-eff-email

# Recargar Nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

---

## 🚀 5. Iniciar Servicios

### Crear Red y Volúmenes
```bash
docker network create cabanas_backend
docker network create cabanas_frontend
docker volume create postgres_data
```

### Iniciar Servicios
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Verificar Salud
```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f backend

# Health check
curl https://reservas.tudominio.com/api/v1/healthz
```

### Ejecutar Migraciones
```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

## 📊 6. Monitoring con Prometheus

### Agregar prometheus a docker-compose.prod.yml
```yaml
  prometheus:
    image: prom/prometheus:latest
    container_name: cabanas_prometheus
    restart: always
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    networks:
      - backend
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    container_name: cabanas_grafana
    restart: always
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_SERVER_ROOT_URL: https://grafana.tudominio.com
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/dashboards:/etc/grafana/provisioning/dashboards
    networks:
      - backend
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
```

### Crear monitoring/prometheus.yml
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi_backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

---

## 🔄 7. Backups Automáticos

### Script de Backup PostgreSQL
```bash
#!/bin/bash
# backup-db.sh

BACKUP_DIR="/opt/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

mkdir -p $BACKUP_DIR

docker-compose -f /opt/SIST_CABANAS_MVP/docker-compose.prod.yml exec -T postgres \
  pg_dump -U alojamientos alojamientos_db | gzip > $BACKUP_FILE

# Mantener solo últimos 7 días
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completado: $BACKUP_FILE"
```

### Crontab para Backups Diarios
```bash
crontab -e

# Backup diario a las 3 AM
0 3 * * * /opt/SIST_CABANAS_MVP/backup-db.sh >> /var/log/backup.log 2>&1
```

---

## 🔒 8. Seguridad Adicional

### Firewall (UFW)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Fail2ban para SSH
```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Actualizar Secrets Regularmente
```bash
# Rotar JWT secret cada 90 días
NEW_JWT=$(openssl rand -base64 48)
# Actualizar .env y reiniciar
docker-compose -f docker-compose.prod.yml restart backend
```

---

## 📝 9. Logs y Debugging

### Ver Logs
```bash
# Logs en tiempo real
docker-compose -f docker-compose.prod.yml logs -f backend

# Logs de últimas 100 líneas
docker-compose -f docker-compose.prod.yml logs --tail=100 backend

# Buscar por trace-id
docker-compose -f docker-compose.prod.yml logs backend | grep "trace_id=abc123"
```

### Logs Estructurados
```bash
# Parsear JSON logs con jq
docker-compose -f docker-compose.prod.yml logs backend | jq -r 'select(.level=="ERROR")'
```

---

## 🔄 10. Updates y Rollbacks

### Update
```bash
cd /opt/SIST_CABANAS_MVP
git pull origin main
docker-compose -f docker-compose.prod.yml build --no-cache backend
docker-compose -f docker-compose.prod.yml up -d backend
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Rollback
```bash
# Volver a versión anterior
git checkout v1.0.0
docker-compose -f docker-compose.prod.yml up -d backend
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade -1
```

---

## ✅ Checklist Final

- [ ] Dominio DNS apuntando al servidor
- [ ] Certificado SSL configurado y renovación automática
- [ ] Variables de entorno con valores seguros (32+ chars)
- [ ] Backups automáticos configurados
- [ ] Firewall activo (UFW)
- [ ] Monitoring (Prometheus + Grafana) funcionando
- [ ] Health checks pasando
- [ ] Logs rotando correctamente
- [ ] Webhooks configurados en WhatsApp y Mercado Pago
- [ ] Rate limiting activo en Nginx
- [ ] Email SMTP funcionando (si aplicable)

---

## 📞 Soporte

Para issues de deployment: https://github.com/eevans-d/SIST_CABANAS_MVP/issues

---

**🚀 Sistema Listo para Producción**
