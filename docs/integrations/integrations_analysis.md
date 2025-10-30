# Análisis de Integraciones Externas - Sistema MVP CABAÑAS

## Resumen Ejecutivo

El sistema MVP de automatización de reservas para cabañas cuenta con múltiples integraciones externas críticas que permiten su funcionamiento completo. Este análisis examina en detalle cada integración, su configuración, seguridad, y estrategias de implementación.

**Fecha de análisis:** 29 de octubre de 2025
**Sistema:** SIST_CABANAS_MVP v1.0.0
**Arquitectura:** Microservicios con FastAPI, PostgreSQL 16, Redis 7, WhatsApp Business Cloud API, Mercado Pago

---

## 1. MERCADO PAGO INTEGRATION

### 1.1 Configuración General

**Arquitectura:**
- Servicio principal: `app/services/mercadopago.py`
- Router: `app/routers/mercadopago.py`
- Modelo de datos: `app/models/payment.py`
- Migración: `alembic/versions/002_create_payments_table.py`

**Variables de Entorno:**
```bash
# Credenciales requeridas
MERCADOPAGO_ACCESS_TOKEN=your_mercadopago_access_token_here
MERCADOPAGO_WEBHOOK_SECRET=optional_webhook_secret

# Configuración en .env.template
MERCADOPAGO_ACCESS_TOKEN=your_mercadopago_access_token_here
MERCADOPAGO_WEBHOOK_SECRET=optional_webhook_secret
```

**Endpoint de Webhook:**
```
POST /api/v1/mercadopago/webhook
```

### 1.2 Implementación del Webhook

**Funcionalidades principales:**
- Procesamiento idempotente de eventos de pago
- Asociación automática con reservas mediante `external_reference`
- Actualización de estados de reserva según estado de pago
- Integración con sistema de notificaciones WhatsApp

**Procesamiento de Payload:**
```python
# Estructura esperada del payload
{
    "id": "123456",                    # payment id MP
    "status": "approved|pending|rejected",
    "amount": 1234.56,
    "currency": "ARS",
    "external_reference": "<reservation_code>"
}
```

**Características de Seguridad:**
- Verificación de firma webhook opcional (si `MERCADOPAGO_WEBHOOK_SECRET` está configurado)
- Validación de `x-signature` header
- HTTP 403 para firmas inválidas
- Idempotencia basada en `external_payment_id`

**Lógica de Negocio:**
1. **Si el pago ya existe:** Incrementar `events_count`, actualizar timestamps
2. **Si es nuevo pago:** Crear registro, asociar a reserva por código
3. **Si pago aprobado:** Cambiar reserva de `PRE_RESERVED` a `CONFIRMED`
4. **Notificaciones:** Enviar WhatsApp automático según estado del pago

### 1.3 APIs de Consulta

**Métodos disponibles:**
- `get_payment_info(payment_id)`: Consulta completa del pago
- `get_payment_status(payment_id)`: Consulta solo del estado

**Manejo de Errores:**
- Retry automático (3 intentos) para errores transitorios (429, 500, 502, 503, 504)
- Sin retry para errores de cliente (400, 401, 403, 404)
- Timeouts configurables (10s por defecto)

**URLs de API:**
```
https://api.mercadopago.com/v1/payments/{payment_id}
```

### 1.4 Esquema de Base de Datos

```sql
CREATE TABLE payments (
    id INTEGER PRIMARY KEY,
    uuid UUID NOT NULL,
    reservation_id INTEGER NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
    provider VARCHAR(30) NOT NULL DEFAULT 'mercadopago',
    external_payment_id VARCHAR(80) NOT NULL,
    external_reference VARCHAR(80),
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    currency VARCHAR(10) NOT NULL DEFAULT 'ARS',
    event_first_received_at TIMESTAMP WITH TIME ZONE,
    event_last_received_at TIMESTAMP WITH TIME ZONE,
    events_count INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Índices para optimización
CREATE INDEX idx_payment_reservation ON payments (reservation_id);
CREATE INDEX idx_payment_external_ref ON payments (external_reference);
CREATE UNIQUE CONSTRAINT uq_payment_external_id ON payments (external_payment_id);
```

### 1.5 Integración con Notificaciones

**Estados de Pago y Acciones:**
- `approved`: Confirma reserva, envía confirmación definitiva
- `rejected`: Notifica rechazo del pago
- `pending`: Notifica pago en procesamiento

**Funciones de Notificación:**
```python
# Automáticamente llamado desde process_webhook
await send_payment_approved(phone, guest_name, reservation_code, check_in, check_out, accommodation_name)
await send_payment_rejected(phone, guest_name, reservation_code, amount)
await send_payment_pending(phone, guest_name, reservation_code, amount)
```

---

## 2. WHATSAPP BUSINESS CLOUD API

### 2.1 Configuración General

**Arquitectura:**
- Servicio principal: `app/services/whatsapp.py`
- Router: `app/routers/whatsapp.py`
- Configuración de mensajes: `app/services/messages.py`
- Handlers interactivos: `app/services/interactive_buttons.py`

**Variables de Entorno:**
```bash
# Credenciales requeridas
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token_here
WHATSAPP_APP_SECRET=your_whatsapp_app_secret_here
WHATSAPP_PHONE_ID=your_whatsapp_phone_id_here

# Token de verificación del webhook
WHATSAPP_VERIFY_TOKEN=wtVXh-tsGWiVlna_xSez7_2aghQi8aFGXFTBGiL2Hh0

# Configuración en .env.template
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token_here
WHATSAPP_APP_SECRET=your_whatsapp_app_secret_here
WHATSAPP_PHONE_ID=your_whatsapp_phone_id_here
WHATSAPP_VERIFY_TOKEN=wtVXh-tsGWiVlna_xSez7_2aghQi8aFGXFTBGiL2Hh0
```

**Endpoints de Webhook:**
```
GET  /api/v1/webhooks/whatsapp  # Verificación inicial
POST /api/v1/webhooks/whatsapp  # Recepción de mensajes
```

### 2.2 Verificación del Webhook

**Proceso de Onboarding:**
```python
@router.get("/webhooks/whatsapp")
async def whatsapp_verify(hub_mode, hub_challenge, hub_verify_token):
    # Validar que hub_mode="subscribe"
    # Comparar hub_verify_token con WHATSAPP_VERIFY_TOKEN
    # Retornar hub_challenge como texto plano
```

**Validación de Firma:**
```python
async def verify_whatsapp_signature(request: Request) -> bytes:
    # Verificar X-Hub-Signature-256 header
    # Validar con WHATSAPP_APP_SECRET
    # Hash SHA256 del body
```

### 2.3 Funcionalidades de Envío

**Tipos de Mensaje Soportados:**

1. **Mensajes de Texto:**
   - Texto plano con formato Markdown
   - Retry automático (3 intentos)
   - Timeouts configurables (10s)

2. **Mensajes con Imágenes:**
   - URLs públicas HTTPS
   - Caption opcional
   - Manejo de errores de rate limiting

3. **Mensajes Interactivos:**
   - Botones de respuesta (hasta 3 botones)
   - Listas interactivas (hasta 10 opciones por sección)
   - Headers y footers opcionales

**URLs de API:**
```
https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_ID}/messages
```

### 2.4 Manejo de Mensajes Entrantes

**Tipos de Mensaje Soportados:**
- `text`: Texto plano
- `audio`: Mensajes de voz (con metadata)
- `image`: Imágenes con caption
- `document`: PDFs y documentos
- `interactive`: Respuestas a botones y listas

**Procesamiento de Mensajes:**
```python
# Normalización de payload entrante
{
    "message_id": "wamid.xxx",
    "canal": "whatsapp",
    "user_id": "5491123456789",
    "timestamp_iso": "2025-10-29T13:21:22Z",
    "tipo": "text|audio|image|interactive",
    "texto": "Texto del mensaje o button_id",
    "media_url": "URL del media",
    "metadata": {...}
}
```

**Flujo de Procesamiento:**
1. Validación de firma y estructura
2. Normalización del mensaje
3. Si es callback de botón → Handler de botones
4. Si es texto → NLU para extraer intent y slots
5. Si faltan slots → Prompt al usuario
6. Si están todos los slots → Crear pre-reserva
7. Enviar respuesta automática

### 2.5 Sistema de Retry y Resiliencia

**Estrategia de Retry:**
- 3 intentos automáticos para errores transitorios
- Exponential backoff (1.0s, 2.0s, 4.0s)
- Errores transitorios: 429 (rate limit), 5xx (server error)
- Errores permanentes: 4xx (client error) - sin retry

**Manejo de Errores:**
- No-op en desarrollo/staging para evitar spam
- Logging detallado de todos los intentos
- Métricas de éxito/fallo para monitoring

**Funciones de Alto Nivel:**
```python
# Mensajes de texto
await send_text_message(to_phone, body)

# Imágenes con caption
await send_image_message(to_phone, image_url, caption=None)

# Botones interactivos
await send_interactive_buttons(to_phone, body_text, buttons, header_text, footer_text)

# Listas interactivas
await send_interactive_list(to_phone, body_text, button_text, sections, header_text, footer_text)
```

### 2.6 Integración con Flujo de Reservas

**Mensajes Automáticos:**
- `send_prereservation_confirmation`: Detalles + link de pago
- `send_reservation_confirmed`: Confirmación post-pago
- `send_payment_reminder`: Recordatorio de pago pendiente
- `send_reservation_expired`: Notificación de expiración

**Mensajes de Error:**
- `send_error_date_overlap`: Fechas no disponibles
- `send_error_no_availability`: Sin disponibilidad general

**Mensajes de Consultas:**
- `send_availability_response`: Respuesta de disponibilidad
- `send_accommodation_info_with_photo`: Info + foto del alojamiento

---

## 3. CONFIGURACIÓN POSTGRESQL

### 3.1 Configuración General

**Versión:** PostgreSQL 16-alpine
**Provider:** Fly.io PostgreSQL o Docker Compose local

**Variables de Entorno:**
```bash
DATABASE_URL=postgresql+asyncpg://alojamientos:password@host:5432/alojamientos_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0

# Docker Compose compatibility
DB_NAME=alojamientos_db
DB_USER=alojamientos
DB_PASSWORD=6tRM6bDRok5uy7nibJsNhLZH4YvEemYnqZcUawyvct4=
POSTGRES_PASSWORD=6tRM6bDRok5uy7nibJsNhLZH4YvEemYnqZcUawyvct4=
```

### 3.2 Configuración de Docker

```yaml
# docker-compose.yml
db:
  image: postgres:16-alpine
  environment:
    - POSTGRES_DB=alojamientos_db
    - POSTGRES_USER=alojamientos
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./init-db.sql:/docker-entrypoint-initdb.d/init-db.sql:ro
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U alojamientos -d alojamientos_db"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 30s
```

### 3.3 Configuración de Conexión

**Configuración SQLAlchemy:**
```python
# app/core/database.py
from sqlalchemy import create_engine, pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# AsyncPG driver para PostgreSQL
DATABASE_URL = "postgresql+asyncpg://..."

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,  # Validar conexiones antes de usar
    echo=False,  # True para debugging SQL
    connect_args={
        "server_settings": {
            "jit": "off",  # Disable JIT para mejor compatibilidad
            "timezone": "UTC"
        }
    }
)
```

### 3.4 Esquemas y Migraciones

**Herramienta de Migración:** Alembic
**Directorio:** `backend/alembic/`

**Estructura de Migraciones:**
```
alembic/
├── versions/
│   ├── 001_initial_schema.py
│   └── 002_create_payments_table.py
├── env.py
├── script.py.mako
└── alembic.ini
```

**Esquema Principal (001_initial_schema.py):**
- Tablas: `accommodations`, `reservations`, `users`, `payment_methods`
- Índices para optimización de consultas
- Constraints de integridad referencial

**Esquema de Pagos (002_create_payments_table.py):**
- Tabla `payments` con soporte para múltiples providers
- UUID para referencia externa
- Timestamps para auditoría de eventos
- Índices optimizados para búsquedas por reservation y external_reference

### 3.5 Configuración de Performance

**Pool de Conexiones:**
- Tamaño: 20 conexiones (configurable via `DB_POOL_SIZE`)
- Max overflow: 0 (conexiones adicionales limitadas)
- Pre-ping: Habilitado para detectar conexiones muertas

**Optimizaciones Aplicadas:**
```sql
-- Configuración PostgreSQL optimizada
shared_preload_libraries = 'pg_stat_statements'
log_statement = 'none'  # Deshabilitado en producción
log_duration = off
log_min_duration_statement = 1000  # Solo queries > 1s

-- Optimizaciones de memoria
work_mem = 16MB
maintenance_work_mem = 256MB
effective_cache_size = 1GB

-- Autovacuum tuning
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 1min
```

### 3.6 Configuración Fly.io

**Creación de PostgreSQL:**
```bash
flyctl postgres create --name sist-cabanas-db
flyctl postgres attach sist-cabanas-db
```

**Variables de Conexión Automáticas:**
```bash
# Fly.io genera automáticamente:
DATABASE_URL=postgres://user:password@host:5432/db
```

**Health Checks:**
```toml
# fly.toml - usando health check de la aplicación
[[http_service.checks]]
grace_period = "30s"
interval = "15s"
method = "GET"
timeout = "5s"
path = "/api/v1/healthz"
```

---

## 4. CONFIGURACIÓN REDIS

### 4.1 Configuración General

**Versión:** Redis 7-alpine
**Provider:** Fly.io Upstash Redis o Docker Compose local

**Variables de Entorno:**
```bash
REDIS_URL=redis://:password@host:6379/0
REDIS_PASSWORD=b1G8yiRwm1i9eflgUG8Wt4J2tBf0qAoyXVfed2AHBF4=
```

### 4.2 Configuración de Docker

```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${REDIS_PASSWORD}", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 30s
```

### 4.3 Gestión de Conexiones

**Pool de Conexiones:**
```python
# app/core/redis.py
redis_pool: Optional[redis.ConnectionPool] = None

def get_redis_pool() -> redis.ConnectionPool:
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=50,
            decode_responses=True,
        )
    return redis_pool

async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """Dependency injection para endpoints FastAPI"""
    pool = get_redis_pool()
    client = redis.Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.close()
```

### 4.4 Estrategias de Cache

**Casos de Uso Actuales:**

1. **Locks Distribuidos:**
   - Prevención de double-booking
   - TTL: 30 minutos por defecto
   - Scripts Lua para atomicidad

2. **Cache de Sesiones:**
   - Rate limiting por IP/usuario
   - Sesiones de conversación WhatsApp
   - Estados temporales de NLU

3. **Cola de Trabajos:**
   - Limpieza de pre-reservas expiradas
   - Sincronización iCal periódica
   - Jobs de notificaciones

**Estructura de Claves (Naming Conventions):**
```
# Locks
lock:reservation:{reservation_id}           # Lock para operaciones de reserva
lock:accommodation:{acc_id}:{dates}         # Lock para disponibilidad

# Rate Limiting
rate_limit:user:{phone}                     # Contador de requests por usuario
rate_limit:ip:{ip_address}                  # Contador de requests por IP

# Sesiones de Conversación
session:whatsapp:{phone}                    # Estado de conversación activa
nlu:conversation:{phone}                    # Slots extraídos de NLU

# Cache Temporal
cache:accommodation:{id}                    # Cache de datos de alojamiento
cache:availability:{acc_id}:{dates}         # Cache de disponibilidad

# Jobs y Tareas
job:expiration:{timestamp}                  # Jobs de limpieza programada
job:ical_sync:{timestamp}                   # Jobs de sincronización iCal
```

### 4.5 Sistema de Locks Distribuidos

**Funciones Principales:**
```python
async def acquire_lock(redis_client: redis.Redis, key: str, value: str, ttl: int = 1800) -> bool:
    """Adquirir lock distribuido con TTL"""
    return await redis_client.set(key, value, nx=True, ex=ttl)

async def release_lock(redis_client: redis.Redis, key: str, value: str) -> bool:
    """Liberar lock solo si lo poseemos (script Lua)"""
    lua_script = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    else
        return 0
    end
    """
    script = redis_client.register_script(lua_script)
    result = await script(keys=[key], args=[value])
    return bool(result)

async def extend_lock(redis_client: redis.Redis, key: str, value: str, ttl: int = 900) -> bool:
    """Extender TTL del lock si lo poseemos"""
    # Script Lua similar para extender atomicamente
```

### 4.6 Configuración de Performance

**Configuración del Servidor:**
- Max memory: 256MB (Docker) / 512MB (Upstash)
- Policy: `allkeys-lru` (remover claves menos usadas)
- Persistencia: RDB snapshots cada 15 minutos

**Optimizaciones:**
```bash
# Configuración Redis optimizada
maxmemory 256mb
maxmemory-policy allkeys-lru
tcp-keepalive 300
timeout 300
save 900 1  # Snapshot cada 15 min si hay 1 cambio
save 300 10 # Snapshot cada 5 min si hay 10 cambios
save 60 1000 # Snapshot cada 1 min si hay 1000 cambios
```

### 4.7 Health Check y Monitoring

**Health Check Implementado:**
```python
async def check_redis_health() -> dict:
    """Verificar conectividad Redis y estadísticas"""
    try:
        pool = get_redis_pool()
        client = redis.Redis(connection_pool=pool)
        await client.ping()
        info = await client.info()
        return {
            "status": "ok",
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown"),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

**Métricas Clave:**
- Clientes conectados
- Memoria utilizada
- Hit rate del cache
- Operaciones por segundo

### 4.8 Configuración Fly.io

**Upstash Redis (Recomendado):**
```bash
# Crear instancia
flyctl redis create --name sist-cabanas-redis
flyctl redis attach sist-cabanas-redis

# Variables automáticas
FLY_REDIS_URL=redis://default:password@host:6379
```

**Configuración de Secretos:**
```bash
flyctl secrets set REDIS_URL="redis://default:password@host:6379"
flyctl secrets set REDIS_PASSWORD="secure-password"
```

---

## 5. CONFIGURACIÓN DESPLIEGUE FLY.IO

### 5.1 Configuración General

**Aplicación Principal:** `sist-cabanas-mvp`
**Región Primaria:** EZE (Ezeiza, Buenos Aires, Argentina)
**Estrategia de Deploy:** Rolling updates con zero-downtime

### 5.2 Configuración fly.toml

**Build Configuration:**
```toml
[build]
  dockerfile = "backend/Dockerfile"
  ignorefile = ".dockerignore"

[app]
  primary_region = "eze"
```

**Environment Variables:**
```toml
[env]
  ENVIRONMENT = "production"
  PORT = "8080"
  GUNICORN_WORKERS = "2"
  GUNICORN_THREADS = "1"
  GUNICORN_TIMEOUT = "120"
  LOG_LEVEL = "info"

  # Rate Limiting
  RATE_LIMIT_ENABLED = "true"
  RATE_LIMIT_REQUESTS = "100"
  RATE_LIMIT_WINDOW_SECONDS = "60"

  # Background Jobs
  JOB_EXPIRATION_INTERVAL_SECONDS = "60"
  JOB_ICAL_INTERVAL_SECONDS = "300"

  # Audio Processing
  AUDIO_MODEL = "base"
  AUDIO_MIN_CONFIDENCE = "0.7"
```

### 5.3 Configuración de Servicios

**HTTP Service:**
```toml
[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = false  # Mantener activo para webhooks
  auto_start_machines = true
  min_machines_running = 1

  [http_service.concurrency]
    type = "requests"
    hard_limit = 250
    soft_limit = 200
```

**Health Checks:**
```toml
[[http_service.checks]]
  grace_period = "30s"
  interval = "15s"
  method = "GET"
  timeout = "5s"
  path = "/api/v1/healthz"
  protocol = "http"
```

**Resources VM:**
```toml
[vm]
  size = "shared-cpu-1x"  # 1 vCPU, 256MB RAM
  # Upgrade options:
  # - shared-cpu-2x: 2 vCPU, 512MB RAM
  # - dedicated-cpu-1x: 1 vCPU, 2GB RAM
```

### 5.4 Configuración de Deploy

**Deploy Strategy:**
```toml
[deploy]
  strategy = "rolling"  # rolling, canary, immediate
  max_unavailable = 0   # Zero-downtime deploys

[experimental]
  auto_rollback = true  # Rollback automático si health check falla
```

**Process Groups:**
```toml
[processes]
  app = "/app/start-fly.sh"

[[services]]
  internal_port = 8080
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"
```

### 5.5 Configuración de Secrets

**Variables Sensibles (requieren `flyctl secrets set`):**
```bash
# Base de datos
DATABASE_URL # Automático con flyctl postgres attach

# Redis
REDIS_URL # Automático con flyctl redis create

# Seguridad
JWT_SECRET
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ICS_SALT

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN
WHATSAPP_APP_SECRET
WHATSAPP_PHONE_ID
WHATSAPP_VERIFY_TOKEN

# Mercado Pago
MERCADOPAGO_ACCESS_TOKEN
MERCADOPAGO_WEBHOOK_SECRET

# Admin Panel
ADMIN_ALLOWED_EMAILS
ADMIN_CSRF_SECRET

# SMTP
SMTP_HOST
SMTP_PORT=587
SMTP_USER
SMTP_PASS
SMTP_FROM
SMTP_USE_TLS=true
```

**Script de Configuración:**
```bash
# ops/set_fly_secrets.sh - Configuración automatizada de secrets
#!/bin/bash

# Generar secrets únicos
JWT_SECRET=$(openssl rand -base64 32)
ICS_SALT=$(openssl rand -hex 16)
ADMIN_CSRF_SECRET=$(openssl rand -base64 16)
WHATSAPP_VERIFY_TOKEN=$(openssl rand -base64 32)

# Configurar en Fly.io
flyctl secrets set JWT_SECRET="$JWT_SECRET"
flyctl secrets set ICS_SALT="$ICS_SALT"
flyctl secrets set ADMIN_CSRF_SECRET="$ADMIN_CSRF_SECRET"
flyctl secrets set WHATSAPP_VERIFY_TOKEN="$WHATSAPP_VERIFY_TOKEN"

# WhatsApp (requieren valores reales)
flyctl secrets set WHATSAPP_ACCESS_TOKEN="your_token_here"
flyctl secrets set WHATSAPP_APP_SECRET="your_app_secret_here"
flyctl secrets set WHATSAPP_PHONE_ID="your_phone_id_here"

# Mercado Pago (requieren valores reales)
flyctl secrets set MERCADOPAGO_ACCESS_TOKEN="your_access_token_here"
flyctl secrets set MERCADOPAGO_WEBHOOK_SECRET="your_webhook_secret_here"
```

### 5.6 Servicios Complementarios

**PostgreSQL:**
```bash
flyctl postgres create --name sist-cabanas-db --region eze
flyctl postgres attach sist-cabanas-db
```

**Redis (Upstash):**
```bash
flyctl redis create --name sist-cabanas-redis --region eze
flyctl redis attach sist-cabanas-redis
```

**Monitoring:**
```toml
[metrics]
  port = 8080
  path = "/metrics"
```

### 5.7 Comandos de Deploy

**Deploy Completo:**
```bash
# Primera vez
flyctl launch

# Deploys subsecuentes
flyctl deploy

# Verificar status
flyctl status

# Ver logs
flyctl logs

# Conectar a consola
flyctl ssh console
```

**Configuración de Dominios:**
```bash
# Configurar dominio personalizado
flyctl certs add your-domain.com
flyctl certs add www.your-domain.com

# Verificar certificados
flyctl certs list
```

### 5.8 Scaling y Monitoreo

**Scaling Manual:**
```bash
flyctl scale count 2  # Duplicar instancias
flyctl scale memory 512  # Aumentar RAM a 512MB

# Scaling automático por métricas (futuro)
flyctl autoscale random-meetric --min 1 --max 3
```

**Monitoreo y Alertas:**
- Health checks cada 15s
- Auto-rollback en caso de falla
- Métricas Prometheus en `/metrics`
- Logs centralizados con `flyctl logs`

---

## 6. CONFIGURACIÓN DOCKER

### 6.1 Dockerfile Principal

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Exponer puerto
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/healthz || exit 1

# Comando por defecto
CMD ["gunicorn", "app.main:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]
```

### 6.2 Configuración Docker Compose

**Servicios Configurados:**
- `app`: API FastAPI con Gunicorn
- `db`: PostgreSQL 16 con health checks
- `redis`: Redis 7 con límites de memoria
- `nginx`: Proxy reverso con SSL/TLS
- `scheduler`: Jobs programados (iCal, cleanup)

**Network:**
```yaml
networks:
  alojamientos_network:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.25.0.0/16
```

**Volumes Persistentes:**
```yaml
volumes:
  postgres_data:    # Datos de PostgreSQL
  redis_data:       # Datos de Redis
  nginx_logs:       # Logs de Nginx
```

### 6.3 Variables de Entorno

**Configuración por Servicio:**
```yaml
# Aplicación principal
environment:
  - ENVIRONMENT=production
  - DATABASE_URL=postgresql://alojamientos:${POSTGRES_PASSWORD}@db:5432/alojamientos_db
  - REDIS_URL=${REDIS_URL}
  - GUNICORN_WORKERS=2
  - GUNICORN_TIMEOUT=60
  - RATE_LIMIT_ENABLED=${RATE_LIMIT_ENABLED}

# PostgreSQL
environment:
  - POSTGRES_DB=alojamientos_db
  - POSTGRES_USER=alojamientos
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
  - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256

# Redis
command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

---

## 7. ANÁLISIS DE SEGURIDAD

### 7.1 Mercado Pago

**Implementaciones de Seguridad:**
- ✅ Validación de firma webhook (opcional)
- ✅ Manejo idempotente de eventos
- ✅ Validación de payload JSON
- ✅ Rate limiting en APIs de consulta
- ✅ Timeouts configurables
- ❗ **Recomendación:** Habilitar `MERCADOPAGO_WEBHOOK_SECRET` en producción

### 7.2 WhatsApp Business API

**Implementaciones de Seguridad:**
- ✅ Validación de firma con `X-Hub-Signature-256`
- ✅ Verificación de webhook con token
- ✅ Rate limiting en envío de mensajes
- ✅ No-op en desarrollo para evitar spam
- ✅ Sanitización de inputs
- ✅ Manejo seguro de media URLs

**Configuraciones Críticas:**
```python
# Verificación obligatoria en producción
if settings.ENVIRONMENT == "production":
    assert settings.WHATSAPP_APP_SECRET, "WHATSAPP_APP_SECRET required"
    assert settings.WHATSAPP_ACCESS_TOKEN != "dummy", "Valid WhatsApp token required"
```

### 7.3 Base de Datos

**Medidas de Seguridad:**
- ✅ Conexiones cifradas via SSL/TLS
- ✅ Pool de conexiones con validación
- ✅ Parámetros preparados para prevenir SQL injection
- ✅ Constraints de integridad referencial
- ✅ Logs de auditoría en timestamps
- ⚠️ **Consideración:** Encriptación at-rest en PostgreSQL

### 7.4 Redis

**Configuraciones de Seguridad:**
- ✅ Autenticación requerida (`REDIS_PASSWORD`)
- ✅ Conexión via TLS (Upstash Redis)
- ✅ Locks distribuidos para atomicidad
- ✅ Scripts Lua para operaciones críticas
- ✅ Health checks regulares
- ⚠️ **Recomendación:** Configurar firewall para Redis self-hosted

---

## 8. MONITOREO Y ALERTAS

### 8.1 Health Checks Implementados

**Endpoints de Health:**
- `/api/v1/healthz`: Health check básico
- `/api/v1/health/detailed`: Health check detallado con DB/Redis
- `/metrics`: Métricas Prometheus

**Integrations Health:**
```python
# app/core/database.py
async def check_db_health() -> dict:
    try:
        async with get_db() as db:
            await db.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# app/core/redis.py
async def check_redis_health() -> dict:
    try:
        pool = get_redis_pool()
        client = redis.Redis(connection_pool=pool)
        await client.ping()
        info = await client.info()
        return {"status": "ok", "memory": info.get("used_memory_human")}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### 8.2 Métricas Clave

**Métricas de Negocio:**
- Reservas creadas por día
- Tasa de conversión pre-reserva → reserva confirmada
- Tiempo promedio de procesamiento de pagos
- Volumen de mensajes WhatsApp procesados

**Métricas Técnicas:**
- Latencia de APIs por endpoint
- Tasa de errores por integración
- Uso de recursos (CPU, RAM, Storage)
- Conectividad de servicios externos

### 8.3 Alertas Recomendadas

**Alertas Críticas (PagerDuty):**
- Falta de conectividad con Mercado Pago
- Falta de conectividad con WhatsApp API
- Errores en procesamiento de webhooks
- Fallos en base de datos

**Alertas de Warning (Slack):**
- Rate limiting activado
- Latencia > 2s en endpoints críticos
- Uso de memoria Redis > 80%
- Errores no críticos en logs

---

## 9. RECOMENDACIONES Y MEJORAS

### 9.1 Mejoras de Seguridad

1. **Habilitar validación de firma Mercado Pago:**
   ```bash
   MERCADOPAGO_WEBHOOK_SECRET=<valor_real_en_produccion>
   ```

2. **Configurar SSL/TLS completo:**
   - Certificados SSL para todos los dominios
   - HSTS headers en Nginx
   - Perfect Forward Secrecy

3. **Implementar WAF (Web Application Firewall):**
   - Protección contra ataques comunes
   - Rate limiting por IP
   - Geo-blocking si es necesario

### 9.2 Mejoras de Performance

1. **Optimización de base de datos:**
   ```sql
   -- Análisis de queries lentas
   SELECT query, mean_time, calls
   FROM pg_stat_statements
   ORDER BY mean_time DESC LIMIT 10;

   -- Índices adicionales para consultas frecuentes
   CREATE INDEX CONCURRENTLY idx_reservations_dates ON reservations (check_in, check_out);
   CREATE INDEX CONCURRENTLY idx_payments_status ON payments (status) WHERE status != 'approved';
   ```

2. **Cache strategy mejorada:**
   ```python
   # Implementar cache por slug para alojamientos
   async def get_accommodation_by_slug(slug: str):
       cache_key = f"accommodation:slug:{slug}"
       acc = await redis.get(cache_key)
       if acc:
           return json.loads(acc)

       acc = await db.query(Accommodation).filter_by(slug=slug).first()
       if acc:
           await redis.setex(cache_key, 3600, json.dumps(acc.dict()))
       return acc
   ```

3. **Connection pooling optimizado:**
   ```python
   # Ajustar pool size según carga esperada
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=50,  # Aumentar para alta carga
       max_overflow=20,
       pool_timeout=30,
       pool_recycle=3600,  # Reciclar conexiones cada hora
   )
   ```

### 9.3 Mejoras de Monitoreo

1. **Dashboard Grafana:**
   - Paneles de negocio (reservas, conversiones)
   - Paneles técnicos (latencia, errores)
   - Alertas visuales por threshold

2. **Logging estructurado:**
   ```python
   import structlog

   logger = structlog.get_logger()

   # Log con contexto enriquecido
   logger.info(
       "reservation_created",
       reservation_id=reservation.id,
       accommodation_id=reservation.accommodation_id,
       guest_phone=reservation.guest_phone,
       user_id=user_id
   )
   ```

3. **Tracing distribuido:**
   - Implementar OpenTelemetry
   - Trace completo de requests
   - Correlación entre servicios

### 9.4 Escalabilidad

1. **Horizontal Scaling:**
   ```bash
   # Configurar auto-scaling en Fly.io
   flyctl autoscale initial=1 min=1 max=5
   ```

2. **Database Sharding:**
   - Particionar por fecha de reserva
   - Múltiples databases por región
   - Read replicas para consultas

3. **Queue System:**
   - Implementar Celery o RQ para trabajos asíncronos
   - Queue separada para notificaciones
   - Dead letter queue para reintentos

---

## 10. CONCLUSIONES

### 10.1 Fortalezas del Sistema

1. **Arquitectura Modular:** Separación clara de responsabilidades por servicio
2. **Idempotencia:** Manejo robusto de eventos duplicados
3. **Resiliencia:** Retry automático y manejo de errores
4. **Seguridad:** Validación de firmas y autenticación robusta
5. **Observabilidad:** Health checks y métricas implementadas

### 10.2 Áreas de Mejora Prioritarias

1. **Seguridad:** Habilitar validación de firma Mercado Pago
2. **Performance:** Optimización de índices de base de datos
3. **Monitoreo:** Dashboard Grafana para métricas de negocio
4. **Escalabilidad:** Implementar auto-scaling en producción

### 10.3 Plan de Implementación

**Fase 1 (Crítica):**
- Habilitar `MERCADOPAGO_WEBHOOK_SECRET`
- Configurar SSL/TLS completo
- Monitoreo de errores críticos

**Fase 2 (Importante):**
- Optimización de base de datos
- Dashboard de monitoreo
- Auto-scaling configuración

**Fase 3 (Futuro):**
- Queue system para trabajos asíncronos
- Database sharding por región
- Tracing distribuido completo

El sistema presenta una arquitectura sólida y bien diseñada para un MVP, con integraciones externas robustas y configuraciones de seguridad apropiadas para el nivel de madurez actual.

---

**Documento generado el:** 29 de octubre de 2025
**Sistema analizado:** SIST_CABANAS_MVP v1.0.0
**Autor:** Análisis técnico automatizado
**Próxima revisión recomendada:** Al completar Fase 1 de mejoras
