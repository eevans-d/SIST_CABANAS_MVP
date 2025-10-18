# 🚂 Guía de Despliegue en Railway - SIST_CABAÑAS_MVP

## 📋 Índice

1. [Pre-requisitos](#pre-requisitos)
2. [Paso 1: Crear Proyecto en Railway](#paso-1-crear-proyecto-en-railway)
3. [Paso 2: Agregar PostgreSQL](#paso-2-agregar-postgresql)
4. [Paso 3: Agregar Redis](#paso-3-agregar-redis)
5. [Paso 4: Configurar Backend](#paso-4-configurar-backend)
6. [Paso 5: Variables de Entorno](#paso-5-variables-de-entorno)
7. [Paso 6: Deploy y Validación](#paso-6-deploy-y-validación)
8. [Post-Deploy: Frontend](#post-deploy-frontend)
9. [Troubleshooting](#troubleshooting)

---

## Pre-requisitos

✅ **Cuenta en Railway**: https://railway.app (gratis para empezar)
✅ **Repositorio GitHub**: SIST_CABANAS_MVP conectado
✅ **Credenciales reales**:
  - WhatsApp Business API (Meta)
  - Mercado Pago Access Token
  - Admin emails

---

## Paso 1: Crear Proyecto en Railway

### 1.1 Crear Nuevo Proyecto

1. Ingresa a https://railway.app/dashboard
2. Click en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Autoriza Railway a acceder a tu GitHub (si es primera vez)
5. Selecciona el repositorio: **`SIST_CABANAS_MVP`**
6. Railway intentará hacer el deploy → **FALLARÁ** (esperado)

### 1.2 ¿Por qué falla inicialmente?

Railway necesita:
- ✅ **Dockerfile** → Ya existe en `backend/Dockerfile`
- ✅ **Start command** → Ahora agregado en `Procfile` y `railway.toml`
- ❌ **Variables de entorno** → Faltan (siguiente paso)
- ❌ **PostgreSQL y Redis** → Faltan (siguiente paso)

---

## Paso 2: Agregar PostgreSQL

### 2.1 Desde el Dashboard de Railway

1. En tu proyecto, click en **"+ New"**
2. Selecciona **"Database"**
3. Elige **"PostgreSQL"**
4. Railway creará automáticamente:
   - Base de datos PostgreSQL 16
   - Variable `DATABASE_URL` (auto-configurada)

### 2.2 Verificar Conexión

1. Click en el servicio **"PostgreSQL"**
2. Pestaña **"Data"** → Verás tabla vacía (normal)
3. Pestaña **"Connect"** → Copia `DATABASE_URL` (backup)

**Formato esperado:**
```
postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/railway
```

Railway transformará esto automáticamente a:
```
postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:[PORT]/railway
```

---

## Paso 3: Agregar Redis

### 3.1 Desde el Dashboard de Railway

1. En tu proyecto, click en **"+ New"**
2. Selecciona **"Database"**
3. Elige **"Redis"**
4. Railway creará automáticamente:
   - Redis 7
   - Variable `REDIS_URL` (auto-configurada)

### 3.2 Verificar Conexión

1. Click en el servicio **"Redis"**
2. Pestaña **"Connect"** → Verás `REDIS_URL`

**Formato esperado:**
```
redis://default:[PASSWORD]@[HOST]:[PORT]
```

---

## Paso 4: Configurar Backend

### 4.1 Seleccionar Servicio Backend

1. En tu proyecto, deberías ver 3 servicios:
   - `SIST_CABANAS_MVP` (el backend)
   - `PostgreSQL`
   - `Redis`

2. Click en el servicio **`SIST_CABANAS_MVP`**

### 4.2 Configurar Build

Railway detectará automáticamente:
- ✅ `Procfile` → Start command: `bash backend/start-railway.sh`
- ✅ `railway.toml` → Configuración explícita
- ✅ `backend/Dockerfile` → Build instructions

**No necesitas cambiar nada aquí**, Railway ya detectó todo correctamente.

### 4.3 Configurar Root Directory (IMPORTANTE)

⚠️ **CRÍTICO**: Railway necesita saber que el código está en el root, no en subdirectorio.

1. Ir a **"Settings"** del servicio backend
2. Buscar **"Root Directory"**
3. Dejar **VACÍO** (no poner `backend/`, el Dockerfile ya lo maneja)

### 4.4 Configurar Health Check

1. En **"Settings"** → Buscar **"Health Check"**
2. Configurar:
   - **Path**: `/api/v1/healthz`
   - **Timeout**: `30` segundos
   - **Interval**: `60` segundos

---

## Paso 5: Variables de Entorno

### 5.1 Variables Auto-Configuradas (Railway)

Railway ya configuró automáticamente:
- ✅ `DATABASE_URL` (desde PostgreSQL plugin)
- ✅ `REDIS_URL` (desde Redis plugin)
- ✅ `PORT` (Railway define puerto automático)

### 5.2 Variables que DEBES Configurar Manualmente

En **"Variables"** del servicio backend, agregar:

#### 🔐 Seguridad y Auth

```bash
ENVIRONMENT=production

# JWT Secret (generar con: openssl rand -hex 32)
JWT_SECRET=tu_jwt_secret_aqui_32_caracteres_minimo

JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ADMIN_TOKEN_EXPIRATION_HOURS=168
```

#### 📱 WhatsApp Business API

```bash
WHATSAPP_ACCESS_TOKEN=tu_token_whatsapp_aqui
WHATSAPP_APP_SECRET=tu_app_secret_whatsapp_aqui
WHATSAPP_PHONE_ID=tu_phone_id_whatsapp_aqui
WHATSAPP_VERIFY_TOKEN=tu_verify_token_aqui
```

**¿Dónde conseguir estos valores?**
1. Ir a https://developers.facebook.com
2. Tu App → WhatsApp → Getting Started
3. Copiar: Access Token, Phone Number ID, App Secret

#### 💳 Mercado Pago

```bash
MERCADOPAGO_ACCESS_TOKEN=tu_access_token_mercadopago_aqui
MERCADOPAGO_WEBHOOK_SECRET=tu_webhook_secret_mercadopago_aqui
```

**¿Dónde conseguir estos valores?**
1. Ir a https://www.mercadopago.com.ar/developers
2. Tus integraciones → Tu aplicación
3. Copiar: Production Access Token
4. Webhook Secret (configurar luego del deploy)

#### 👤 Admin Emails

```bash
# Emails separados por coma (sin espacios)
ADMIN_ALLOWED_EMAILS=tu_email@example.com,otro_admin@example.com
```

#### ⚙️ Configuración Opcional (con defaults)

```bash
# Workers Gunicorn (Railway: 2 workers OK con plan Hobby)
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=120
LOG_LEVEL=info

# Locks Redis
LOCK_TTL_SECONDS=1800
LOCK_RETRY_DELAY_MS=100
LOCK_MAX_RETRIES=5

# Pre-reservas
RESERVATION_PRE_EXPIRY_MINUTES=5

# Rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Audio (Whisper)
AUDIO_MAX_SIZE_MB=25
AUDIO_MAX_DURATION_SEC=300
STT_CONFIDENCE_THRESHOLD=0.7

# iCal sync
ICAL_SYNC_INTERVAL_MINUTES=5
ICAL_EXPORT_TTL_DAYS=365
```

### 5.3 Verificar Variables

1. Ir a **"Variables"** del servicio backend
2. Deberías ver ~30 variables configuradas
3. Las variables con 🔒 (lock) son sensibles (ocultas)

---

## Paso 6: Deploy y Validación

### 6.1 Trigger Deploy

1. En el servicio backend, ir a **"Deployments"**
2. Click en **"Deploy"** (esquina superior derecha)
3. Railway comenzará el build:
   - ⏳ Building Docker image (~5-7 minutos)
   - ⏳ Running migrations
   - ⏳ Starting Gunicorn

### 6.2 Monitorear Build Logs

1. Click en el deployment en progreso
2. Verás logs en tiempo real:

```bash
🚀 Starting SIST_CABAÑAS_MVP Backend on Railway...
📋 Validating environment variables...
✅ DATABASE_URL is set
✅ REDIS_URL is set
✅ JWT_SECRET is set
✅ WHATSAPP_ACCESS_TOKEN is set
...
✅ All required environment variables are set
⏳ Waiting for PostgreSQL...
  → Database host: containers.railway.app:5432
✅ PostgreSQL is ready
⏳ Waiting for Redis...
✅ Redis is ready
🔄 Running database migrations...
✅ Database migrations completed
🚀 Starting Gunicorn + Uvicorn workers...
```

### 6.3 Verificar Deploy Exitoso

#### Health Check Endpoint

1. Railway asignará un dominio automático: `https://sist-cabanas-mvp-production.up.railway.app`
2. Probar health check:

```bash
curl https://tu-dominio.up.railway.app/api/v1/healthz
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "checks": {
    "database": {"status": "ok", "latency_ms": 15},
    "redis": {"status": "ok", "latency_ms": 3},
    "ical_sync": {"status": "ok"}
  },
  "version": "1.0.0",
  "environment": "production"
}
```

#### Verificar Logs

En Railway → **"Logs"** del servicio backend:

```
✅ Gunicorn started with 2 workers
✅ Uvicorn running on http://0.0.0.0:8000
✅ Application started successfully
```

---

## Post-Deploy: Frontend

El frontend (Dashboard Admin React) debe desplegarse **separadamente**.

### Opciones Recomendadas

#### Opción A: Vercel (Recomendado para React)

1. Ir a https://vercel.com
2. Import repository `SIST_CABANAS_MVP`
3. Configurar:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend/admin-dashboard`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Variables de entorno:
   ```bash
   VITE_API_URL=https://tu-dominio-backend.up.railway.app
   VITE_WS_URL=wss://tu-dominio-backend.up.railway.app
   ```

#### Opción B: Railway (Servicio Separado)

1. En tu proyecto Railway, click **"+ New"**
2. Seleccionar **"GitHub Repo"** → Mismo repositorio
3. Configurar:
   - **Root Directory**: `frontend/admin-dashboard`
   - **Build Command**: `npm run build`
   - **Start Command**: `npm run preview`
4. Variables de entorno: igual que Opción A

#### Opción C: Netlify

Similar a Vercel, muy fácil de configurar.

---

## Troubleshooting

### ❌ Error: "Missing required environment variable"

**Solución:**
1. Verificar que todas las variables estén configuradas en Railway UI
2. Variables requeridas:
   - `DATABASE_URL` (auto)
   - `REDIS_URL` (auto)
   - `JWT_SECRET`
   - `WHATSAPP_ACCESS_TOKEN`
   - `WHATSAPP_APP_SECRET`
   - `WHATSAPP_PHONE_ID`
   - `WHATSAPP_VERIFY_TOKEN`
   - `MERCADOPAGO_ACCESS_TOKEN`
   - `ADMIN_ALLOWED_EMAILS`

### ❌ Error: "Database migrations failed"

**Causas posibles:**
1. PostgreSQL no disponible
2. DATABASE_URL incorrecto
3. Permisos insuficientes

**Solución:**
1. Verificar que el servicio PostgreSQL esté **UP**
2. Revisar logs del servicio PostgreSQL
3. Verificar que `DATABASE_URL` esté correctamente configurada
4. Probar conexión manualmente desde Railway CLI:
   ```bash
   railway run psql $DATABASE_URL
   ```

### ❌ Error: "Redis connection timeout"

**Solución:**
1. Verificar que el servicio Redis esté **UP**
2. Revisar `REDIS_URL` en variables
3. Verificar que backend y Redis estén en el **mismo proyecto Railway**

### ❌ Error: "nc: command not found"

El script `start-railway.sh` usa `nc` (netcat) para verificar conectividad.

**Solución:**
Agregar en `backend/Dockerfile` (antes de `USER appuser`):

```dockerfile
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*
```

### ❌ Build exitoso pero Health Check falla

**Causas posibles:**
1. Puerto incorrecto
2. Health check path incorrecto
3. App no inició correctamente

**Solución:**
1. Verificar logs de Gunicorn
2. Verificar que `PORT` env variable esté configurada (Railway la provee)
3. Probar manualmente:
   ```bash
   curl https://tu-dominio.up.railway.app/api/v1/healthz
   ```

### ❌ Whisper model download timeout

En el primer deploy, Whisper descarga el modelo (~150MB).

**Solución:**
1. Aumentar timeout de build en Railway Settings
2. O pre-descargar en Dockerfile (ver `backend/Dockerfile`)

---

## 🎉 Deploy Completado

Una vez que veas:

```
✅ Health check: PASSING
✅ Last deployment: SUCCESS
✅ Status: ACTIVE
```

¡Tu backend está en producción! 🚀

### Próximos Pasos

1. ✅ Configurar dominio custom (opcional)
2. ✅ Configurar webhooks externos:
   - WhatsApp: `https://tu-dominio.up.railway.app/api/v1/webhooks/whatsapp`
   - Mercado Pago: `https://tu-dominio.up.railway.app/api/v1/mercadopago/webhook`
3. ✅ Deploy frontend (Vercel/Netlify)
4. ✅ Monitoreo continuo (Railway provee métricas básicas)
5. ✅ Configurar alertas (opcional: Sentry, Discord webhook)

---

## 📊 Costos Estimados Railway

### Plan Hobby (Recomendado para MVP)

- **$5 USD/mes** por servicio activo
- Incluye:
  - 512MB RAM
  - 1GB Disco
  - 100GB bandwidth
  - PostgreSQL incluido
  - Redis incluido

**Costo total estimado:**
- Backend: $5/mes
- PostgreSQL: Incluido
- Redis: Incluido
- **TOTAL: ~$5-10 USD/mes**

### Plan Pro (Para escalar)

- **$20 USD/mes**
- Incluye:
  - 8GB RAM
  - 100GB Disco
  - Custom domains
  - Priority support

---

## 📚 Recursos

- Railway Docs: https://docs.railway.app
- Railway Status: https://status.railway.app
- Railway Discord: https://discord.gg/railway
- Este proyecto en GitHub: https://github.com/eevans-d/SIST_CABANAS_MVP

---

**¿Problemas?** Revisa los logs en Railway UI o contacta soporte en Discord.
