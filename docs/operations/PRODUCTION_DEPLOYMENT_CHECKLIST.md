# 🚀 PRODUCTION DEPLOYMENT CHECKLIST - Sistema de Reservas Cabañas

**Versión:** v1.0.0
**Fecha de Creación:** 17 de Octubre 2025
**Estado:** READY FOR DEPLOYMENT

---

## ✅ PRE-DEPLOYMENT CHECKLIST

### 1️⃣ REQUISITOS DE INFRAESTRUCTURA

**Antes de proceder, verificar que todos estos están disponibles:**

- [ ] **Servidor de Producción**
  - [ ] VPS o servidor dedicado (4vCPU, 8GB RAM mínimo)
  - [ ] SSH access configurado
  - [ ] Ubuntu 22.04 LTS o similar
  - [ ] Docker y Docker Compose instalados
  - [ ] Puertos abiertos: 80 (HTTP), 443 (HTTPS)

- [ ] **Base de Datos**
  - [ ] PostgreSQL 16 (local o managed)
  - [ ] Backup automático configurado (daily, 7-day retention)
  - [ ] Usuario y password para producción
  - [ ] Extensión `btree_gist` habilitada

- [ ] **Redis**
  - [ ] Redis 7 (local o managed)
  - [ ] Password configurado
  - [ ] Persistencia habilitada

- [ ] **Dominio**
  - [ ] Dominio registrado y apuntado a IP del servidor
  - [ ] DNS A record actualizado
  - [ ] TTL configurado

- [ ] **Certificado SSL**
  - [ ] Let's Encrypt certificate (free, auto-renewable)
  - [ ] Auto-renewal script activo

### 2️⃣ SECRETOS Y CREDENCIALES

**Antes de proceder, tener todos estos secretos preparados:**

```bash
# DATABASE
DATABASE_URL=postgresql://user:password@host:5432/reservas_prod

# REDIS
REDIS_URL=redis://:password@host:6379/0

# JWT (Generar: openssl rand -hex 32)
JWT_SECRET=<random-256-bit-hex>
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# WHATSAPP
WHATSAPP_BUSINESS_ACCOUNT_ID=<tu-account-id>
WHATSAPP_PHONE_NUMBER_ID=<tu-phone-id>
WHATSAPP_TOKEN=<tu-access-token>
WHATSAPP_APP_SECRET=<tu-app-secret>

# MERCADO PAGO
MERCADOPAGO_ACCESS_TOKEN=<tu-access-token>
MERCADOPAGO_PUBLIC_KEY=<tu-public-key>

# ADMIN
ADMIN_ALLOWED_EMAILS=admin@tudominio.com,owner@tudominio.com

# GENERAL
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=https://tudominio.com
```

- [ ] Todos los secretos obtenidos y validados
- [ ] Guardados en `.env.prod` (NUNCA commitear)
- [ ] Backup de secrets en lugar seguro

### 3️⃣ CÓDIGO Y BUILDS

- [ ] Branch `main` limpio (sin cambios sin commitear)
- [ ] Último commit en GitHub
- [ ] Build local exitoso: `npm run build` (frontend)
- [ ] Tests pasando: `make test` (backend)
- [ ] Sin CVEs: `trivy scan`

---

## 📋 PASOS DE DEPLOYMENT

### PASO 1: Preparar Servidor

```bash
# 1.1 Conectar al servidor
ssh root@ip-servidor

# 1.2 Actualizar sistema
apt update && apt upgrade -y

# 1.3 Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh

# 1.4 Instalar Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 1.5 Crear directorio de aplicación
mkdir -p /opt/cabanas-reservas && cd /opt/cabanas-reservas
mkdir -p data/postgres data/redis logs
```

**Checklist:**
- [ ] SSH acceso verificado
- [ ] Docker funcionando
- [ ] Directorios creados

### PASO 2: Transferir Código

```bash
# 2.1 Desde local, clonar repositorio
cd /tmp && git clone https://github.com/eevans-d/SIST_CABANAS_MVP.git

# 2.2 Copiar a servidor
scp -r SIST_CABANAS_MVP/* root@ip-servidor:/opt/cabanas-reservas/

# 2.3 En servidor, crear .env.prod
ssh root@ip-servidor
cd /opt/cabanas-reservas
# [Crear .env.prod con secretos reales]
chmod 600 .env.prod
```

**Checklist:**
- [ ] Código transferido
- [ ] `.env.prod` creado
- [ ] Permisos correctos (600)

### PASO 3: Configurar Nginx y SSL

```bash
# 3.1 Instalar certbot
apt install -y certbot python3-certbot-nginx

# 3.2 Generar certificado SSL
certbot certonly --standalone -d tudominio.com -d www.tudominio.com

# 3.3 Configurar auto-renewal
systemctl enable certbot.timer && systemctl start certbot.timer
```

**Checklist:**
- [ ] Nginx configurado
- [ ] Certificado SSL obtenido
- [ ] Auto-renewal activo

### PASO 4: Iniciar Servicios

```bash
# 4.1 Levantar con Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# 4.2 Verificar contenedores
docker-compose ps

# 4.3 Aplicar migraciones
sleep 20
docker-compose exec app python -m alembic upgrade head
```

**Checklist:**
- [ ] Contenedores levantados
- [ ] PostgreSQL inicializado
- [ ] Migraciones aplicadas
- [ ] Sin errores en logs

### PASO 5: Health Checks

```bash
# 5.1 Verificar API
curl -i https://tudominio.com/api/v1/healthz
# Respuesta: HTTP 200 + {"status": "healthy"}

# 5.2 Verificar Dashboard
open https://tudominio.com
# Debe cargar login page

# 5.3 Verificar login
curl -X POST https://tudominio.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@tudominio.com","password":"..."}'
# Debe retornar JWT token
```

**Checklist:**
- [ ] API `/healthz` → HTTP 200
- [ ] Dashboard → HTTP 200
- [ ] Login → JWT token recibido
- [ ] Métricas accesibles

---

## 🔄 ROLLBACK PLAN

Si algo falla:

```bash
# 1. Detener servicios
docker-compose down

# 2. Restaurar DB si es necesario
docker-compose exec postgres pg_restore -U postgres -d reservas_prod /backups/backup.sql

# 3. Revertir código
git revert <commit-hash>

# 4. Levantar nuevamente
docker-compose -f docker-compose.prod.yml up -d

# 5. Verificar health
curl https://tudominio.com/api/v1/healthz
```

---

## 📊 POST-DEPLOYMENT MONITORING

**Primera hora:**
- [ ] Logs limpios (sin errores frecuentes)
- [ ] CPU/RAM dentro de límites
- [ ] Error rate < 1%

**Primera semana:**
- [ ] Revisar error logs diariamente
- [ ] Monitorear database performance
- [ ] Verificar Redis memory
- [ ] Configurar alertas:
  - [ ] HTTP error rate > 5%
  - [ ] Response time P95 > 5s
  - [ ] Database connections > 90
  - [ ] Disk space < 20%

---

## 🔒 SEGURIDAD POST-DEPLOYMENT

- [ ] Firewall: solo puertos 80, 443, 22 abiertos
- [ ] SSH hardening: cambiar puerto 22, desabilitar root
- [ ] SSL validado: https://sslcheck.globalsign.com
- [ ] Headers de seguridad en Nginx
- [ ] Rate limiting activo
- [ ] Backup de DB diario verificado

---

## 📝 DOCUMENTACIÓN FINAL

- [ ] Actualizar guía de credenciales con IPs reales
- [ ] Crear runbook de producción
- [ ] Documentar deployment en summary
- [ ] Informar al equipo

---

## ✅ FINAL CHECKLIST

- [ ] Health checks pasando
- [ ] Smoke tests exitosos
- [ ] Backups funcionando
- [ ] Alertas configuradas
- [ ] Runbook documentado
- [ ] Equipo informado
- [ ] Monitoreo 24/7 activo

---

## 📞 EMERGENCIA

Si algo falla:
1. Revisar logs: `docker-compose logs app`
2. Verificar health: `curl https://tudominio.com/api/v1/healthz`
3. Ejecutar rollback si es necesario
4. Contactar soporte

---

**Documento:** 17 de Octubre 2025
**Mantener actualizado primeros 30 días de producción**
