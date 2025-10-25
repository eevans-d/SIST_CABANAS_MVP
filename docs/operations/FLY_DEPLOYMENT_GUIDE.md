# 📖 Guía Completa de Deployment en Fly.io

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura](#arquitectura)
3. [Instalación Inicial](#instalación-inicial)
4. [Configuración de Recursos](#configuración-de-recursos)
5. [Deployment](#deployment)
6. [Verificación](#verificación)
7. [Operaciones](#operaciones)
8. [Troubleshooting](#troubleshooting)
9. [Performance Tuning](#performance-tuning)
10. [Seguridad](#seguridad)

---

## Introducción

### ¿Por qué Fly.io?

- ✅ **Free tier generoso**: 3 máquinas shared-cpu-1x, 256MB RAM, 3GB storage
- ✅ **Múltiples regiones**: Buenos Aires (eze), São Paulo (gru), Miami (mia)
- ✅ **IPv6 nativo**: Mejor conectividad global
- ✅ **PostgreSQL integrado**: Managed Postgres con backups automáticos
- ✅ **Deploy desde Git**: CI/CD con GitHub Actions
- ✅ **Edge Runtime**: Mejor performance para LATAM

### Alternativas Consideradas

| Plataforma | Free | PostgreSQL | Redis | Regiones | Elegido |
|-----------|------|-----------|-------|----------|---------|
| **Fly.io** | Sí   | Sí        | No*   | 10+      | ✅      |
| Railway   | No   | Plugins   | Plugins | 5      | ❌      |
| Render    | Sí   | Sí        | Sí    | 5        | ⏸️      |
| Heroku    | No   | Sí        | Sí    | 5        | ❌      |

*Redis via Upstash (externo, gratis)

---

## Arquitectura

### Stack

```
┌─────────────────────────────────────────┐
│       Fly.io (Global Anycast)           │
├─────────────────────────────────────────┤
│  Region: eze (Buenos Aires, Argentina)  │
├─────────────────────────────────────────┤
│  Frontend                               │
│  ├─ React 18 + Vite (Build estático)   │
│  └─ Hosted en: Vercel / Netlify        │
├─────────────────────────────────────────┤
│  Backend (Docker)                       │
│  ├─ FastAPI + Gunicorn + Uvicorn       │
│  ├─ Port: 8080                          │
│  ├─ Workers: 2 (configurable)           │
│  └─ Health: /api/v1/healthz              │
├─────────────────────────────────────────┤
│  PostgreSQL 16 (Managed)                │
│  ├─ Region: eze                          │
│  ├─ Shared-cpu-1x 256MB                 │
│  └─ Backup: Diario (7 días)              │
├─────────────────────────────────────────┤
│  Redis (Upstash - Externo)              │
│  ├─ Free: 10,000 comandos/día            │
│  ├─ Región: us-east-1 (baja latencia)   │
│  └─ SSL/TLS: Sí                          │
└─────────────────────────────────────────┘
```

### Flujo de Deployment

```
Local Development
        ↓
    git push
        ↓
GitHub Actions CI/CD (tests)
        ↓
Build Docker Image
        ↓
Push a Fly.io Registry
        ↓
Deploy Rolling (zero-downtime)
        ↓
Health Checks
        ↓
Monitoreo
```

---

## Instalación Inicial

### Paso 1: Preparar Entorno Local

```bash
# Clonar repositorio
git clone https://github.com/eevans-d/SIST_CABANAS_MVP.git
cd SIST_CABANAS_MVP

# Copiar variables de entorno
cp .env.template .env

# Editar .env con valores reales
nano .env
```

### Paso 2: Instalar flyctl

```bash
# macOS
brew install flyctl

# Linux (Ubuntu/Debian)
curl -L https://fly.io/install.sh | sh
export PATH="$HOME/.fly/bin:$PATH"

# Verificar
flyctl version
```

### Paso 3: Autenticarse

```bash
# Login
flyctl auth login

# Se abrirá navegador, completa el signup
# Verifica autenticación
flyctl auth whoami
```

### Paso 4: Configurar Git (opcional para CI/CD)

```bash
# Generar token GitHub (si usas CI/CD)
# https://github.com/settings/tokens
# Necesita: repo, workflow

# Guardar en GitHub Secrets:
# FLY_API_TOKEN: Obtenido de flyctl
flyctl auth token
```

---

## Configuración de Recursos

### A. PostgreSQL

#### Opción 1: Managed Postgres en Fly.io

```bash
# Crear instancia PostgreSQL
flyctl postgres create \
  --name sist-cabanas-db \
  --region eze \
  --vm-size shared-cpu-1x \
  --initial-cluster-size 1 \
  --volume-size 20

# Esperará a que se cree la instancia (3-5 min)

# Ver detalles
flyctl postgres show sist-cabanas-db

# Obtener URL conexión
flyctl postgres app sist-cabanas-db

# Será algo como:
# postgresql://app:password@sist-cabanas-db.internal:5432/postgres
```

#### Opción 2: PostgreSQL Externo (e.g., Neon, Supabase)

```bash
# Si usas Supabase o Neon:
# 1. Copia DATABASE_URL de tu proveedor
# 2. Asegúrate de que la región sea cercana a eze
# 3. Configura secreto en Fly.io (ver "Secrets")
```

#### Verificar Conectividad

```bash
# Proxy local a DB (desarrollo)
flyctl proxy 5432:5432 -a sist-cabanas-db

# Desde otra terminal
psql "postgresql://app:password@localhost/postgres"

# Ejecutar query de prueba
\d  # Ver tablas
\q  # Salir
```

### B. Redis (Upstash)

#### Crear en Upstash

1. Ve a https://upstash.com/console/redis
2. Crea un nuevo database:
   - **Name**: sist-cabanas-redis
   - **Region**: us-east-1 (latencia baja a Argentina)
   - **Eviction Policy**: allkeys-lru
   - **TLS/SSL**: Enabled
3. Copia la URL de conexión: `redis://:password@host:port`

#### Alternativa: Redis Gratuito Local

```bash
# Para desarrollo solamente (NO producción)
# Docker local:
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

#### Verificar Conectividad

```bash
# Instalar redis-cli (macOS)
brew install redis

# Test conexión
redis-cli -u "redis://:password@host:port" PING
# Respuesta esperada: PONG
```

### C. Configurar fly.toml

```toml
# El archivo ya está en root: /fly.toml
# Personalizar si es necesario:

app = "sist-cabanas-mvp"  # Nombre de la app
primary_region = "eze"     # Buenos Aires

[build]
  dockerfile = "backend/Dockerfile"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = false

[vm]
  size = "shared-cpu-1x"  # Free tier

[deploy]
  strategy = "rolling"
  max_unavailable = 0    # Zero-downtime

[env]
  ENVIRONMENT = "production"
  PORT = "8080"
  # Más variables públicas...
```

---

## Deployment

### Paso 1: Crear App en Fly.io

```bash
# Primer deploy (crea app)
flyctl launch --name sist-cabanas-mvp --region eze --no-deploy

# Responde las preguntas:
# - Copy configuration from existing fly.toml? → yes
# - Would you like to set up a PostgreSQL cluster? → yes (ya lo hicimos)
```

### Paso 2: Configurar Secretos

```bash
# Cargar secretos desde .env.template (valores generados)
flyctl secrets set \
  DATABASE_URL="postgresql://app:password@sist-cabanas-db.internal:5432/postgres" \
  REDIS_URL="redis://:password@host:port/0" \
  JWT_SECRET="P9LQYGSuJVjvdJSrJ3sS-MjLEMJXVFWVaq1uA4Z2FLw" \
  WHATSAPP_VERIFY_TOKEN="wtVXh-tsGWiVlna_xSez7_2aghQi8aFGXFTBGiL2Hh0" \
  WHATSAPP_ACCESS_TOKEN="your_whatsapp_token_here" \
  WHATSAPP_APP_SECRET="your_whatsapp_app_secret" \
  WHATSAPP_PHONE_ID="your_whatsapp_phone_id" \
  MERCADOPAGO_ACCESS_TOKEN="your_mp_token_here" \
  ADMIN_ALLOWED_EMAILS="admin@example.com" \
  ADMIN_CSRF_SECRET="WIWaM_CbERF1PW3zMYRrvsbL7IirUnOK" \
  ICS_SALT="9bf35066c0404c0734c6a7348333f4dd" \
  SMTP_PASS="vdi8SL4XinSD563HNR4xEcWzrKFSgCdnPshWom7e5z8="

# Verificar que se configuraron
flyctl secrets list
```

### Paso 3: Deploy Inicial

```bash
# Deployar (construye imagen Docker y despliega)
flyctl deploy

# Verá output como:
# Creating image...
# Pushing to registry...
# Release v1 created
# Deploying...

# Seguir progreso
flyctl logs -f

# Esperado: "INFO:     Application startup complete"
```

### Paso 4: Migraciones BD

```bash
# SSH a la instancia
flyctl ssh console

# Dentro de la consola:
$ cd /app
$ python3 -m alembic upgrade head
# Ejecuta migraciones

# Salir
$ exit
```

---

## Verificación

### 1. Health Check

```bash
# Debe responder 200 OK
curl https://sist-cabanas-mvp.fly.dev/api/v1/healthz

# Esperado:
{
  "status": "healthy",
  "checks": {
    "database": {"status": "ok", "latency_ms": 32},
    "redis": {"status": "ok", "latency_ms": 8},
    "ical_sync": {"status": "ok", "last_sync_minutes": 1}
  }
}
```

### 2. Métricas

```bash
# Verificar Prometheus metrics
curl https://sist-cabanas-mvp.fly.dev/metrics | grep up

# Esperado: 1 (aplicación UP)
```

### 3. Admin Dashboard

```bash
# Ver si frontend está disponible (si desplegaste)
curl https://sist-cabanas-mvp.fly.dev/admin

# O usar navegador:
# https://sist-cabanas-mvp.fly.dev/admin
```

### 4. Crear Reserva Test

```bash
# Generate JWT token para test (si tienes admin auth)
TOKEN=$(flyctl ssh console -c 'python3 -c "import jwt; print(jwt.encode({\"sub\": \"test@example.com\"}, \"'"$JWT_SECRET"'\"))" | head -1)

# Crear reserva
curl -X POST https://sist-cabanas-mvp.fly.dev/api/v1/reservations \
  -H "Content-Type: application/json" \
  -d '{
    "accommodation_id": 1,
    "check_in": "2025-11-20",
    "check_out": "2025-11-23",
    "guests": 2,
    "contact_name": "Test User",
    "contact_phone": "+5491155443322",
    "channel": "web"
  }'
```

---

## Operaciones

### Escalado

```bash
# Aumentar RAM
flyctl scale memory 512 -a sist-cabanas-mvp

# Cambiar tipo de VM
flyctl scale vm shared-cpu-2x -a sist-cabanas-mvp

# Aumentar replicas
flyctl scale count 2 -a sist-cabanas-mvp
```

### Logs

```bash
# Todos
flyctl logs -f

# Últimas 100 líneas
flyctl logs --lines 100

# Solo errores
flyctl logs | grep ERROR

# Con timestamps
flyctl logs --pretty
```

### SSH/Console

```bash
# Entrar en shell
flyctl ssh console

# Ejecutar comando
flyctl ssh console -c "python3 --version"

# Salida a archivo
flyctl ssh console -c "alembic current" > db_version.txt
```

### Restart/Redeploy

```bash
# Restart (sin redeploy)
flyctl restart

# Redeploy (de código actual)
flyctl deploy

# Rollback a versión anterior
flyctl scale stable
```

### Backups

```bash
# Para Managed Postgres (automático)
# Backups diarios, retención 7 días
# Dashboard Fly.io → Postgres → Backups

# Para Upstash Redis (manual):
# https://upstash.com/console/redis → Database → Export
```

---

## Troubleshooting

### App No Arranca

**Síntoma**: Deploy "failed" o timeout

**Diagnóstico**:
```bash
# Ver logs de build
flyctl build-log sist-cabanas-mvp

# Ver logs de runtime
flyctl logs --lines 200 | tail

# Buscar ERROR
flyctl logs | grep -i error
```

**Soluciones Comunes**:

1. **Docker build error**:
   ```bash
   # Rebuilding
   flyctl deploy --strategy=canary
   ```

2. **Missing dependencies**:
   - Verificar `requirements.txt`
   - Rebuild sin cache: `flyctl deploy --no-cache`

3. **Health check failing**:
   ```bash
   # Ver health check setup en fly.toml
   # Aumentar timeout:
   [http_service]
     start_period = "30s"  # Aumentar a 60s si es necesario
   ```

### Database Connection Failed

**Síntoma**: `psycopg2.OperationalError: could not connect to server`

**Diagnóstico**:
```bash
# Verificar DATABASE_URL
flyctl secrets list | grep DATABASE

# Test conexión local
flyctl proxy 5432:5432 -a sist-cabanas-db
psql "postgresql://..."

# Ver logs de DB
flyctl postgres logs sist-cabanas-db
```

**Soluciones**:

1. **URL incorrecta**:
   ```bash
   # Obtener URL correcta
   flyctl postgres app sist-cabanas-db

   # Actualizar
   flyctl secrets set DATABASE_URL="nueva_url"
   flyctl deploy
   ```

2. **DB no está corriendo**:
   ```bash
   # Reiniciar
   flyctl restart -a sist-cabanas-db
   ```

3. **Firewall/Security groups**:
   - Verificar que postgres accept conexiones de la app

### Redis Timeout

**Síntoma**: `redis.exceptions.TimeoutError`

**Diagnóstico**:
```bash
# Verificar REDIS_URL
flyctl secrets list | grep REDIS

# Test desde app
flyctl ssh console -c "python3 -c 'import redis; print(redis.Redis.from_url(\"redis://...\").ping())'"
```

**Soluciones**:

1. **URL incorrecta o expirada**:
   - Regenerar en Upstash y actualizar secreto

2. **Redis quota excedida**:
   - Upgrade plan Upstash o limpiar keys
   ```bash
   redis-cli -u "redis://..." FLUSHDB
   ```

3. **Network latency**:
   - Cambiar región Redis a us-east-1

### Out of Memory (OOM)

**Síntoma**: Process killed, status 137

**Diagnóstico**:
```bash
# Ver uso de memoria
flyctl metrics

# Logs antes del crash
flyctl logs --lines 500
```

**Soluciones**:

1. **Aumentar RAM**:
   ```bash
   flyctl scale memory 512
   ```

2. **Reducir workers Gunicorn**:
   ```bash
   # En .env:
   GUNICORN_WORKERS=1
   flyctl deploy
   ```

3. **Memory leak**:
   - Revisar código por variables globales
   - Usar profiler: `python3 -m memory_profiler app.py`

---

## Performance Tuning

### Database Optimization

```sql
-- Conectarse a PostgreSQL
psql "postgresql://..."

-- Ver queries lentas
SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;

-- Crear índices faltantes
CREATE INDEX idx_reservations_accommodation_status ON reservations(accommodation_id, reservation_status);

-- Vacuum & Analyze
VACUUM ANALYZE;
```

### Redis Optimization

```bash
# Monitorar uso
redis-cli -u "redis://..." INFO stats

# Limpiar keys expiradas
redis-cli -u "redis://..." BGREWRITEAOF

# Ver memoria
redis-cli -u "redis://..." INFO memory
```

### Gunicorn Tuning

```bash
# En .env:
GUNICORN_WORKERS=2           # CPUs * 2
GUNICORN_TIMEOUT=120         # segundos
GUNICORN_GRACEFUL_TIMEOUT=30 # segundos para shutdown
GUNICORN_KEEP_ALIVE=75       # segundos keep-alive

# Deploy con nuevos valores
flyctl deploy
```

---

## Seguridad

### HTTPS/TLS

```bash
# Automático en Fly.io
# Certificado Let's Encrypt renovado automáticamente

# Verificar
curl -vI https://sist-cabanas-mvp.fly.dev/healthz | grep SSL
```

### Secrets Management

```bash
# NUNCA commitear .env a git
echo ".env" >> .gitignore
git add .gitignore
git commit

# Para deploying local changes:
# 1. Actualizar secreto
flyctl secrets set VAR="value"

# 2. Verificar (sin mostrar valor)
flyctl secrets list | grep VAR

# 3. Rotate periódicamente
flyctl secrets set JWT_SECRET="new_random_value"
```

### Firewalls & Rate Limiting

```bash
# Configurado en backend:
# - Rate limit: 60 req/min por IP
# - Bypass: /healthz, /readyz, /metrics

# Ver métricas
curl https://sist-cabanas-mvp.fly.dev/metrics | grep rate_limit
```

---

## CI/CD (GitHub Actions)

Ver `.github/workflows/fly-deploy.yml` para configuración automática de deployment.

---

## Monitoreo en Producción

### Métricas Importantes

```bash
# Ver dashboard
flyctl dashboard -a sist-cabanas-mvp

# HTTP errors
curl https://sist-cabanas-mvp.fly.dev/metrics | grep http_requests_total

# Database latency
curl https://sist-cabanas-mvp.fly.dev/metrics | grep pg_latency

# iCal sync
curl https://sist-cabanas-mvp.fly.dev/metrics | grep ical_sync_age
```

### Alertas Recomendadas

- Error rate > 5%
- Health check timeout > 10s
- Database latency > 500ms
- iCal sync age > 30 minutos

---

## Próximos Pasos

- [ ] Configurar custom domain
- [ ] Setup GitHub Actions para CI/CD automático
- [ ] Configurar Datadog o New Relic para monitoreo avanzado
- [ ] Backup estrategia para PostgreSQL
- [ ] Disaster recovery plan

---

**Última actualización**: Octubre 2025
**Versión**: 1.0 - MVP
**Status**: Production Ready ✅
