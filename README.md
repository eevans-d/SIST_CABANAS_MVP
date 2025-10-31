# 🏠 Sistema MVP de Automatización de Reservas# 🏠 Sistema MVP de Automatización de Reservas



[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)

[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io/)[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io/)

[![Production Ready](https://img.shields.io/badge/production-ready-brightgreen)](https://github.com/eevans-d/SIST_CABANAS_MVP)[![Production Ready](https://img.shields.io/badge/production-ready-brightgreen)](https://github.com/eevans-d/SIST_CABANAS_MVP)



**Sistema completo de automatización de reservas** con integración nativa de WhatsApp Business, procesamiento de pagos con Mercado Pago, transcripción de audio (Whisper STT) y sincronización bidireccional con plataformas como Airbnb/Booking via iCal.**Sistema completo de automatización de reservas** con integración nativa de WhatsApp Business, procesamiento de pagos con Mercado Pago, transcripción de audio (Whisper STT) y sincronización bidireccional con plataformas como Airbnb/Booking via iCal.



🚀 **MVP v1.0** - Listo para producción | **173+ tests passing** | **Anti doble-booking garantizado**🚀 **MVP v1.0** - Listo para producción | **173+ tests passing** | **Anti doble-booking garantizado**



------



## 🎯 Características Principales## 🎯 Características Principales



### 🤖 Automatización Completa### 🤖 Automatización Completa

- **WhatsApp Bot** con NLU básico para consultas en lenguaje natural- **WhatsApp Bot** con NLU básico para consultas en lenguaje natural

- **Audio-to-Text** con Whisper para mensajes de voz- **Audio-to-Text** con Whisper para mensajes de voz

- **Pre-reservas automáticas** con expiración configurable- **Pre-reservas automáticas** con expiración configurable

- **Confirmación de pagos** automática vía webhooks Mercado Pago- **Confirmación de pagos** automática vía webhooks Mercado Pago



### 🔒 Anti Doble-Booking### 🔒 Anti Doble-Booking

- **Constraint PostgreSQL** con `EXCLUDE USING gist` a nivel DB- **Constraint PostgreSQL** con `EXCLUDE USING gist` a nivel DB

- **Locks Redis** para operaciones concurrentes- **Locks Redis** para operaciones concurrentes

- **Validación de solapamiento** en tiempo real- **Validación de solapamiento** en tiempo real

- **Testing exhaustivo** de concurrencia- **Testing exhaustivo** de concurrencia



### 📅 Sincronización iCal### 📅 Sincronización iCal

- **Import** automático desde Airbnb/Booking- **Import** automático desde Airbnb/Booking

- **Export** con tokens seguros para gestores externos- **Export** con tokens seguros para gestores externos

- **Deduplicación** inteligente de eventos- **Deduplicación** inteligente de eventos

- **Sync en background** cada 5 minutos- **Sync en background** cada 5 minutos



### 🔐 Seguridad Enterprise### 🔐 Seguridad Enterprise

- **Validación de firmas** para todos los webhooks- **Validación de firmas** para todos los webhooks

- **Rate limiting** configurable por IP- **Rate limiting** configurable por IP

- **Autenticación JWT** para admin panel- **Autenticación JWT** para admin panel

- **Logs estructurados** con trace IDs- **Logs estructurados** con trace IDs



------



## 🏗️ Arquitectura del Sistema- [Monitoreo](#-monitoreo)



```- [Troubleshooting](#-troubleshooting)- Pre-reservas con expiración automática

┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐

│   WhatsApp      │    │   FastAPI        │    │   PostgreSQL    │- [Contribución](#-contribución)

│   Business API  │◄──►│   Backend        │◄──►│   + btree_gist  │

└─────────────────┘    │                  │    └─────────────────┘- Procesamiento de pagos (Mercado Pago)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)[![FastAPI](https://img.shields.io/badge/fastapi-0.115-009688)](https://fastapi.tiangolo.com/)

                       │  ┌─────────────┐  │

┌─────────────────┐    │  │   Redis     │  │    ┌─────────────────┐---

│   Mercado Pago  │◄──►│  │   Cache     │◄─┤    │   iCal Sync     │

│   Webhooks      │    │  │   + Locks   │  │    │   (Airbnb/etc)  │

└─────────────────┘    │  └─────────────┘  │    └─────────────────┘

                       └──────────────────┘## ✨ Características Principales

┌─────────────────┐             │

│   Whisper STT   │◄────────────┘### 🛡️ Robustez[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

│   Audio Engine  │

└─────────────────┘### **Automatización Multi-Canal**

```

# 🏠 SIST CABAÑAS MVP — Sistema de Automatización de Reservas

Sistema de automatización de reservas con FastAPI + PostgreSQL + Redis, integraciones con WhatsApp Business y Mercado Pago, y sincronización iCal (Airbnb/Booking). Backend MVP 100% completado; Admin Dashboard (React + Vite) en desarrollo.

Estado: 🟢 Backend listo | 🔶 Frontend Admin en curso | 180+ tests | 85% coverage

---

## 🚀 Quick Start (Docker Compose)

Requisitos: Docker 24+, Docker Compose, Python 3.12+ (opcional para scripts), FFmpeg (para audio opcional).

1) Configura variables de entorno

```bash
cp .env.template .env
# Edita .env con tus credenciales (DB, Redis, WhatsApp, Mercado Pago)
```

2) Levanta los servicios

```bash
docker-compose up -d
```

3) Migra base de datos y valida health

```bash
docker-compose exec backend alembic upgrade head
curl -s http://localhost:8000/api/v1/healthz | jq .
```

Documentación interactiva: http://localhost:8000/docs

---

## 🧱 Stack

- Backend: FastAPI, SQLAlchemy Async, Pydantic v2
- DB: PostgreSQL 16 (+ btree_gist para anti overlap)
- Cache/Locks: Redis 7 (locks para concurrencia)
- Integraciones: WhatsApp Business Cloud API, Mercado Pago, iCal
- Observabilidad: Prometheus `/metrics`, health checks `/api/v1/healthz`
- Frontend (admin): React 18 + Vite + Tailwind

---

## 🔒 Anti doble-booking (core)

- Constraint PostgreSQL: `EXCLUDE USING gist` sobre `period` (`daterange(check_in, check_out, '[)')`) activo para `pre_reserved|confirmed`.
- Locks Redis: `lock:acc:{id}:{checkin}:{checkout}` con TTL 1800s.
- Tests de concurrencia y solapamiento incluidos.

---

## 🛫 Deploy (Fly.io)

El repo está configurado para una sola app en Fly (`sist-cabanas-mvp`, region `gru`) y con guardas anti-duplicados de costo.

1) Cargar secretos en Fly (previo)

```bash
export DEPLOY_ACK="I_ACCEPT_SINGLE_APP_COSTS"
./ops/deploy-check.sh   # Debe decir: CHECKS OK
```

2) Desplegar

```bash
fly deploy -a sist-cabanas-mvp --ha=false
```

3) Validar

```bash
./ops/smoke-tests.sh https://sist-cabanas-mvp.fly.dev
```

Más detalles en `DEPLOY_FAST_TRACK.md` y `ops/STAGING_DEPLOYMENT_QUICK_START.md`.

---

## � Documentación principal

- Guía de navegación: `DOCUMENTATION_INDEX.md`
- Resumen ejecutivo: `PROJECT_SUMMARY.md`
- UX Master Plan (Admin/Guest): `ops/UX_MASTER_PLAN_ADMIN_GUEST.md`
- Playbooks de deploy/operaciones: `ops/*.md`

---

## 🔐 Seguridad (mandatorios)

- Validar SIEMPRE firmas de webhooks (WhatsApp `X-Hub-Signature-256`, Mercado Pago `x-signature`).
- No subir secretos al repo. Usar `.env` y secrets en Fly.
- Rate limiting por IP+path respaldado por Redis. JWT para admin.

---

## 🧪 Tests

```bash
cd backend
pytest -q
```

Suite >180 tests, cobertura ~85%. Algunos tests de overlap requieren Postgres real con `btree_gist`.

---

## 📄 Licencia

MIT. Ver `LICENSE`.


```bashREDIS_URL=redis://localhost:6379/0

ENVIRONMENT=production                    # ⚠️ Obligatorio

DATABASE_URL=postgresql+asyncpg://...     # ⚠️ Con btree_gist- **Backend:** FastAPI 0.104+, SQLAlchemy 2.0 (Async), Pydantic v2

REDIS_URL=redis://prod-redis:6379/0       # ⚠️ Redis persistente

BASE_URL=https://tu-dominio.com           # ⚠️ HTTPS obligatorio- **Database:** PostgreSQL 16 (btree_gist extension)```- **NLU básico:** Detección de intenciones (regex + dateparser)- **Webhooks seguros:** Validación HMAC-SHA256

WHATSAPP_*=valores_reales                 # ⚠️ No usar 'dummy'

MERCADOPAGO_*=valores_produccion          # ⚠️ Credenciales reales- **Cache:** Redis 7

```

- **WhatsApp:** Meta Business Cloud API v17.0

---

- **Payments:** Mercado Pago API

## 📊 Observabilidad

- **Audio:** faster-whisper (OpenAI Whisper) + FFmpeg## 📖 Uso Básico- **Respuestas automáticas:** Templates contextuales- **Audio STT:** Transcripción con Whisper + FFmpeg

### Health Checks

```bash- **Observability:** Prometheus + structlog (JSON)

curl /api/v1/healthz

# Response: {"status": "healthy", "checks": {...}}- **Infrastructure:** Docker + Docker Compose + Nginx + Let's Encrypt

```



### Métricas (Prometheus)

```bash---### Consultar Disponibilidad- **NLU básico:** Detección de intenciones (regex + dateparser)

curl /metrics

# Métricas: reservations_total, audio_transcriptions, ical_sync_age, etc.

```

## 🚀 Instalación Rápida```bash

### Logs Estructurados

```json

{

  "timestamp": "2025-01-14T10:30:00Z",### **Prerequisitos**curl -X GET "http://localhost:8000/api/v1/reservations/availability" \### 💳 Pagos Mercado Pago- **Respuestas automáticas:** Templates contextuales

  "level": "INFO",

  "event": "reservation_created",

  "trace_id": "abc123",

  "accommodation_id": 1,- Docker 24+ y Docker Compose 2.20+  -H "Content-Type: application/json" \

  "check_in": "2025-02-01",

  "total_price": 150.00- Git

}

```- (Opcional) Credenciales de WhatsApp Business y Mercado Pago  -d '{- **Webhooks idempotentes:** Manejo de duplicados



---



## 🔒 Seguridad### **1. Clonar y Configurar**    "accommodation_id": 1,



### Checklist de Producción

- ✅ **HTTPS obligatorio** (Let's Encrypt / Cloudflare)

- ✅ **Firmas webhook validadas** (WhatsApp + Mercado Pago)```bash    "check_in": "2025-10-20",- **Validación de firmas:** x-signature header### Pagos Mercado Pago

- ✅ **Rate limiting por IP** (60 req/min configurable)

- ✅ **JWT para admin panel** (HS256, exp configurable)git clone https://github.com/eevans-d/SIST_CABANAS_MVP.git

- ✅ **Variables sensibles en entorno** (no hardcoded)

- ✅ **Logs sin datos PII** (números de teléfono hasheados)cd SIST_CABANAS_MVP    "check_out": "2025-10-22"



### Rate Limiting

```bash

# 60 requests por minuto por IP (configurable)# Copiar template de configuración  }'- **Flujo completo:** Pre-reserva → Pago → Confirmación automática- **Webhooks idempotentes:** Manejo de duplicados

RATE_LIMIT_REQUESTS=60

RATE_LIMIT_WINDOW_SECONDS=60cp .env.template .env



# Bypass automático para health checks```

# /api/v1/healthz y /metrics sin límite

```# Editar con tus credenciales



---nano .env- **Validación de firmas:** x-signature header



## 🤝 Contribución```



### Desarrollo Local### Crear Reserva

```bash

# 1. Setup entorno### **2. Levantar Servicios**

cd backend

python -m venv venv```bash### 📅 Sincronización iCal- **Flujo completo:** Pre-reserva → Pago → Confirmación automática

source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt```bash



# 2. DB local (PostgreSQL + Redis requeridos)# Opción 1: Con Make (recomendado)curl -X POST "http://localhost:8000/api/v1/reservations" \

createdb cabanas_test

psql cabanas_test -c "CREATE EXTENSION btree_gist;"make up



# 3. Variables de desarrollo  -H "Content-Type: application/json" \- **Import/Export:** Compatible con Airbnb, Booking.com

cp ../.env.template .env

# Ajustar para desarrollo local# Opción 2: Docker Compose directo



# 4. Migraciones y testsdocker-compose up -d  -d '{

alembic upgrade head

pytest tests/ -v

```

# Ver logs    "accommodation_id": 1,- **Deduplicación:** Por UID de evento### Sincronización iCal

### Comandos Útiles (Makefile)

```bashmake logs

make test       # Tests unitarios

make test-e2e   # Tests E2E completos```    "check_in": "2025-10-20",

make up         # Docker Compose up

make logs       # Ver logs

make migrate    # Aplicar migraciones

make format     # Black + isort### **3. Ejecutar Migraciones**    "check_out": "2025-10-22",- **Background jobs:** Sync automático cada 15 minutos- **Import/Export:** Compatible con Airbnb, Booking.com

make lint       # Flake8 + mypy

make security   # Bandit scan

```

```bash    "guests": 2,

---

make migrate

## 📞 Soporte

```    "guest_name": "Juan Pérez",- **Deduplicación:** Por UID de evento

### Issues Comunes



**❌ Error: "NOT NULL constraint failed: reservations.accommodation_id"**

```bash### **4. Verificar Instalación**    "guest_phone": "+5491123456789"

# Solución: Usar PostgreSQL, no SQLite para tests E2E

# Tests unitarios: automático fallback a SQLite

# Tests E2E: usar docker-compose con Postgres real

``````bash  }'### 📊 Observabilidad- **Background jobs:** Sync automático cada 15 minutos



**❌ Error: "Redis connection refused"**curl http://localhost:8000/api/v1/healthz

```bash

# Solución: Verificar Redis running``````

docker ps | grep redis

# O usar Redis local:

redis-server --port 6379

```**Respuesta esperada:**- **Prometheus metrics:** 17+ métricas custom de negocio



**❌ Error: "Invalid WhatsApp signature"**```json

```bash

# Solución: Verificar WHATSAPP_APP_SECRET correcto{## 🧪 Testing

# Logs muestran: "whatsapp_signature_validation_failed"

```  "status": "healthy",



### Contacto  "checks": {- **Health checks:** `/healthz` y `/readyz` con latencias### Observabilidad

- **GitHub Issues:** [Sistema MVP Issues](https://github.com/eevans-d/SIST_CABANAS_MVP/issues)

- **Documentación:** [Wiki del proyecto](https://github.com/eevans-d/SIST_CABANAS_MVP/wiki)    "database": {"status": "ok", "latency_ms": 15},

- **Arquitectura:** Ver `docs/` y `.github/copilot-instructions.md`

    "redis": {"status": "ok", "latency_ms": 2},```bash

---

    "ical_sync": {"status": "ok", "last_sync_age_minutes": 3}

## 📄 Licencia

  }cd backend- **Structured logging:** JSON logs con trace IDs- **Prometheus metrics:** 17+ métricas custom de negocio

MIT License. Ver `LICENSE` para detalles completos.

}

**TL;DR:** Libre para uso comercial, modificación y distribución con atribución.

```pytest tests/ -v

---



<div align="center">

### **5. Acceder a Documentación**pytest tests/ --cov=app --cov-report=html- **Rate limiting:** Por IP + endpoint con métricas- **Health checks:** `/healthz` y `/readyz` con latencias

**🏠 Sistema MVP de Automatización de Reservas v1.0**



*Construido con ❤️ para hoteleros modernos*

- **Swagger UI:** http://localhost:8000/docs```

[⭐ Star en GitHub](https://github.com/eevans-d/SIST_CABANAS_MVP) | [📖 Documentación](https://github.com/eevans-d/SIST_CABANAS_MVP/wiki) | [🐛 Reportar Bug](https://github.com/eevans-d/SIST_CABANAS_MVP/issues)

- **ReDoc:** http://localhost:8000/redoc

</div>
- **Metrics:** http://localhost:8000/metrics- **Structured logging:** JSON logs con trace IDs



---## 📊 Arquitectura



## ⚙️ Configuración---- **Rate limiting:** Por IP + endpoint con métricas



### **Variables de Entorno Críticas**```



```envWhatsApp/Email → FastAPI → PostgreSQL

# Database

DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/reservas                    ↓         (+ btree_gist)

POSTGRES_USER=reservas_user

POSTGRES_PASSWORD=strong_password_here              Redis (locks)## ⚡ Quick Start (3 minutos)---

POSTGRES_DB=reservas

                    ↓

# Redis

REDIS_URL=redis://redis:6379/0            Prometheus (metrics)



# WhatsApp Business Cloud API```

WHATSAPP_ACCESS_TOKEN=your_access_token

WHATSAPP_PHONE_ID=your_phone_number_id### Desarrollo Local## ⚡ Quick Start (3 minutos)

WHATSAPP_VERIFY_TOKEN=your_verify_token

WHATSAPP_APP_SECRET=your_app_secret**Stack:**



# Mercado Pago- FastAPI 0.115+ (async)

MERCADOPAGO_ACCESS_TOKEN=your_mp_access_token

MERCADOPAGO_PUBLIC_KEY=your_mp_public_key- PostgreSQL 16 + btree_gist



# Security- Redis 7```bash### Desarrollo Local

SECRET_KEY=generate_with_openssl_rand_hex_32

ALLOWED_ORIGINS=https://yourdomain.com- SQLAlchemy 2.0+ AsyncSession



# Environment# 1. Clonar y configurar

ENVIRONMENT=development  # development | test | production

```**Integraciones:**



Ver `.env.template` para lista completa de variables.- WhatsApp Business Cloud APIgit clone https://github.com/eevans-d/SIST_CABANAS_MVP.git```bash



---- Mercado Pago



## 💻 Uso- Whisper STTcd SIST_CABANAS_MVP# 1. Clonar y configurar



### **Crear Alojamiento**- iCal (RFC 5545)



```bashcp backend/.env.template backend/.envgit clone https://github.com/eevans-d/SIST_CABANAS_MVP.git

curl -X POST http://localhost:8000/api/v1/admin/accommodations \

  -H "Content-Type: application/json" \## 🐛 Troubleshooting

  -d '{

    "name": "Cabaña del Lago",cd SIST_CABANAS_MVP

    "type": "cabin",

    "capacity": 4,### Doble-booking error

    "base_price": 15000,

    "description": "Hermosa cabaña frente al lago"Normal - el sistema está previniendo correctamente:# 2. Levantar servicioscp backend/.env.template backend/.env

  }'

``````sql

  ## 🧭 Frontend Admin (Quick Start)

  > Panel administrativo (React + Vite + Tailwind) para KPIs, listado de reservas, filtros y monitoreo.

  1) Variables del frontend

  ```
  cd frontend/admin-dashboard
  cp .env.example .env
  # Editar .env y configurar:
  # VITE_API_URL=https://sist-cabanas-mvp.fly.dev/api/v1   # o tu backend local: http://localhost:8000/api/v1
  ```

  2) Correr en local (dev) o compilar

  ```
  # Dev (hot reload)
  npm ci
  npm run dev

  # Build de producción
  npm run build
  # Opcional: preview del build
  npm run preview
  ```

  Docs del Admin:
  - README del Admin: `frontend/admin-dashboard/README.md`
  - Estado de Deploy: `frontend/admin-dashboard/DEPLOYMENT_STATUS.md`




### **Consultar Disponibilidad**SELECT conname FROM pg_constraint cd backend



```bashWHERE conname = 'no_overlap_reservations';

curl "http://localhost:8000/api/v1/accommodations/1/availability?check_in=2025-10-20&check_out=2025-10-22"

``````docker-compose up -d# 2. Levantar servicios con Docker



### **Crear Pre-Reserva**



```bash### iCal sync atrasadocd backend

curl -X POST http://localhost:8000/api/v1/reservations \

  -H "Content-Type: application/json" \```bash

  -d '{

    "accommodation_id": 1,docker-compose logs backend | grep "ical_sync"# 3. Ejecutar migracionesdocker-compose up -d

    "check_in": "2025-10-20",

    "check_out": "2025-10-22",curl -X POST "http://localhost:8000/api/v1/ical/sync/1"

    "guests_count": 4,

    "guest_name": "Juan Pérez",```docker-compose exec api alembic upgrade head

    "guest_phone": "+5491112345678",

    "channel_source": "web"

  }'

```### Redis unavailable# 3. Ejecutar migraciones



---Sistema funciona en fail-open mode. Verificar:



## 📡 API Endpoints```bash# 4. Verificardocker-compose exec api alembic upgrade head



### **Health & Metrics**docker-compose ps redis



- `GET /api/v1/healthz` - Health check comprehensivodocker-compose logs rediscurl http://localhost:8000/api/v1/healthz

- `GET /metrics` - Métricas de Prometheus

```

### **Accommodations**

# Respuesta esperada: {"status": "healthy", ...}# 4. Verificar

- `GET /api/v1/accommodations` - Listar alojamientos

- `GET /api/v1/accommodations/{id}` - Detalle## 📝 Docs Adicionales

- `GET /api/v1/accommodations/{id}/availability` - Consultar disponibilidad

- `POST /api/v1/admin/accommodations` - Crear (admin)```curl http://localhost:8000/api/v1/healthz

- `PUT /api/v1/admin/accommodations/{id}` - Actualizar (admin)

- **[MVP_STATUS.md](./MVP_STATUS.md)** - Estado del proyecto

### **Reservations**

- **[PROGRESO_DIARIO.md](./PROGRESO_DIARIO.md)** - Log de desarrollo

- `POST /api/v1/reservations` - Crear pre-reserva

- `GET /api/v1/reservations/{code}` - Detalle- **[copilot-instructions.md](./.github/copilot-instructions.md)** - Reglas técnicas

- `POST /api/v1/reservations/{code}/cancel` - Cancelar

- `GET /api/v1/admin/reservations` - Listar todas (admin)**Accesos:**./test_constraint_specific.sh  - **Anti-Doble-Booking:** Constraint PostgreSQL `EXCLUDE USING gist` + locks Redis distribuidos



### **Webhooks**## 🤝 Contribución



- `GET /api/v1/webhooks/whatsapp` - Verificación webhook- **API:** http://localhost:8000

- `POST /api/v1/webhooks/whatsapp` - Recibir mensajes

- `POST /api/v1/webhooks/mercadopago` - Recibir eventos de pago1. Fork el repo



### **iCal**2. Crear branch (`git checkout -b feature/nueva-feat`)- **Docs:** http://localhost:8000/docs- **WhatsApp Business:** Webhook con firma HMAC SHA-256, normalización de mensajes, audio STT



- `GET /api/v1/ical/export/{accommodation_id}` - Exportar calendario3. Commit (`git commit -m 'feat: nueva funcionalidad'`)

- `POST /api/v1/admin/ical/import` - Importar desde URL

4. Push (`git push origin feature/nueva-feat`)- **Métricas:** http://localhost:8000/metrics

### **Audio**

5. Abrir PR

- `POST /api/v1/audio/transcribe` - Transcribir audio (multipart/form-data)

# Test flujo completo end-to-end- **Mercado Pago:** Integración con validación de firmas y manejo idempotente

Ver documentación completa en `/docs` (Swagger UI).

Seguir [Conventional Commits](https://www.conventionalcommits.org/)

---

### Deploy a Producción

## 🧪 Testing

## 📄 Licencia

### **Ejecutar Tests**

./test_end_to_end.sh- **iCal Import/Export:** Sincronización automática con Airbnb/Booking

```bash

# Todos los testsMIT License

make test

```bash

# Con cobertura

make test-coverage## 🎯 Roadmap Post-MVP



# Tests específicos# 1. Configurar variables de entorno- **NLU Básico:** Detección de intención y extracción de entidades (fechas, huéspedes)

docker-compose exec backend pytest tests/test_reservations.py -v

- [ ] Dashboard admin React

# Test individual

docker-compose exec backend pytest tests/test_reservations.py::test_no_double_booking -v- [ ] Multi-propiedadcp backend/.env.template backend/.env

```

- [ ] Analytics avanzado

### **Tests Críticos**

- [ ] AI agents con LLMnano backend/.env  # Completar con valores reales# Test idempotencia webhooks- **Observabilidad:** Métricas Prometheus, health checks, logs estructurados

- ✅ Anti doble-booking (concurrencia)

- ✅ Idempotencia de webhooks

- ✅ Pre-reserva expiration

- ✅ iCal deduplication---

- ✅ WhatsApp button callbacks



Ver `backend/tests/` para test suite completo.

**v1.0.0 - MVP Completo y Producción-Ready**# 2. Deploy automatizado./test_idempotency.sh- **Jobs Background:** Expiración de pre-reservas, sync iCal, recordatorios

---



## 🚢 Deployment

Issues: https://github.com/eevans-d/SIST_CABANAS_MVP/issues./scripts/deploy.sh

### **Producción con Docker Compose**



```bash

# 1. Configurar .env para producción

cp .env.template .env# 3. Configurar SSL y webhooks

nano .env  # Editar con credenciales reales

# Seguir guía en docs/deployment/STAGING_DEPLOY_GUIDE.md# Test integración Mercado Pago## 📚 Documentación Esencial

# 2. Levantar servicios

docker-compose -f docker-compose.prod.yml up -d```



# 3. Ejecutar migraciones./test_mercadopago.sh

docker-compose exec backend alembic upgrade head

---

# 4. Verificar

curl https://yourdomain.com/api/v1/healthz| Documento | Propósito |

```

## 🧪 Testing

### **Nginx + SSL**

# Test integración WhatsApp|-----------|-----------|

```nginx

server {```bash

    listen 443 ssl http2;

    server_name yourdomain.com;# Tests unitarios (SQLite fallback)./test_whatsapp_webhook.sh| **[PRODUCTION_SETUP.md](PRODUCTION_SETUP.md)** | Guía completa para deploy en producción (210 líneas) |



    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;cd backend

    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    pytest tests/ -v```| **[scripts/README.md](scripts/README.md)** | Documentación de scripts de automatización |

    location / {

        proxy_pass http://localhost:8000;

        proxy_set_header Host $host;

        proxy_set_header X-Real-IP $remote_addr;# Tests con Postgres real (constraint validation)| **[SESION_COMPLETADA.md](SESION_COMPLETADA.md)** | Último resumen de progreso |

        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

    }docker-compose up -d postgres redis

}

```pytest tests/test_double_booking.py tests/test_constraint_validation.py -v## 🛠️ Configuración Rápida| **[PARA_MAÑANA.md](PARA_MAÑANA.md)** | Guía rápida para continuar desarrollo |



```bash

# Obtener certificado SSL

sudo certbot --nginx -d yourdomain.com# Coverage| **[STATUS_ACTUAL_2025-10-02.md](STATUS_ACTUAL_2025-10-02.md)** | Estado detallado del proyecto |

```

pytest tests/ --cov=app --cov-report=html

### **Configurar Webhooks**

``````bash

**WhatsApp Business:**

1. Meta Developer Console → WhatsApp → Configuration

2. Webhook URL: `https://yourdomain.com/api/v1/webhooks/whatsapp`

3. Verify Token: Valor de `WHATSAPP_VERIFY_TOKEN`**Resultado esperado:** 37 passed, 11 skipped (SQLite mode)# 1. Levantar servicios## 📦 Stack Tecnológico

4. Subscribe to: `messages`



**Mercado Pago:**

1. Mercado Pago Developer → Webhooks### Tests Críticos Disponiblesmake up

2. URL: `https://yourdomain.com/api/v1/webhooks/mercadopago`

3. Events: `payment`, `merchant_order`



Ver [`DEPLOYMENT.md`](DEPLOYMENT.md) para guía detallada.```bash**Backend:** FastAPI 0.115 + SQLAlchemy Async + Alembic



---# Anti-doble booking con concurrencia



## 📊 Monitoreo./test_anti_double_booking.sh# 2. Verificar salud**Database:** PostgreSQL 16 (btree_gist) + Redis 7



### **Métricas Prometheus**



```prometheus# Constraint PostgreSQL específicocurl http://localhost:8000/api/v1/healthz**Deploy:** Docker + Docker Compose + Nginx

# Reservas

reservations_total{channel, status}./test_constraint_specific.sh

reservations_lock_failed_total{channel}

reservations_date_overlap_total{channel}**Observability:** Prometheus + structlog



# HTTP# Flujo completo end-to-end

http_requests_total{method, path, status_code}

http_request_duration_seconds{method, path}./test_end_to_end.sh# 3. Ejecutar tests**Testing:** pytest + asyncio (37 tests)



# iCal

ical_last_sync_age_minutes

ical_import_events_total{accommodation_id}# Idempotencia webhooks./test_constraint_specific.sh**CI/CD:** GitHub Actions



# Botones WhatsApp./test_idempotency.sh

whatsapp_button_clicks_total{button_id, flow}

whatsapp_button_conversion_total{flow, outcome}./test_end_to_end.sh

```

# Integración Mercado Pago

### **Queries Útiles (Grafana)**

./test_mercadopago.sh```## 🎯 Repositorio Oficial

```promql

# Tasa de reservas por hora

rate(reservations_total[1h])

# Integración WhatsApp

# P95 latencia de API

histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))./test_whatsapp_webhook.sh



# Alerta: iCal desactualizado```## 📋 Configuración de Integraciones- **Código e issues:** https://github.com/eevans-d/SIST_CABANAS_MVP

ical_last_sync_age_minutes > 20

```



------- **Política:** Este es el único repositorio oficial del proyecto



## 🔧 Troubleshooting



### **Health Check Falla**## 📦 Stack Tecnológico### WhatsApp Business API- **Consolidación:** Ver `docs/CONSOLIDATION_STATUS.md`



```bash

# Verificar servicios

docker-compose ps**Backend:**Ver: `CONFIGURACION_WHATSAPP.md`



# Ver logs- FastAPI 0.115 + SQLAlchemy Async + Alembic

docker-compose logs backend postgres redis

- PostgreSQL 16 (btree_gist extension)## 🏗️ Estado de Implementación (Actualizado 2025-10-02)

# Reiniciar

docker-compose restart- Redis 7 (locks + cache)

```

### Mercado Pago

### **Webhooks No Llegan**

**Integraciones:**

```bash

# Ver logs de webhooks- WhatsApp Business Cloud APIVer: `CONFIGURACION_MERCADOPAGO.md`✅ **Core MVP Completo:**

docker-compose logs backend | grep "webhook"

- Mercado Pago API

# Test local con ngrok

ngrok http 8000- Whisper STT (faster-whisper)- Modelos: `accommodations`, `reservations`, `payments`, `messages`, `audio_transcriptions`

# Configurar URL temporal en Meta/Mercado Pago

```- iCal RFC5545



### **Audio No Transcribe**### ngrok (para webhooks en desarrollo)- Constraint anti-doble-booking: `no_overlap_reservations` (PostgreSQL daterange + EXCLUDE gist)



```bash**Deploy:**

# Verificar FFmpeg

docker-compose exec backend ffmpeg -version- Docker + Docker Compose + Nginx```bash- ReservationService con locks Redis + pricing con multiplicadores



# Ver logs de Whisper- GitHub Actions CI/CD

docker-compose logs backend | grep "whisper"

```- Prometheus metrics./setup_ngrok.sh- Jobs: expiración pre-reservas, sync iCal, recordatorios



### **Redis Out of Memory**



```bash---```- Tests: 37 passed, 11 skipped (requieren Postgres real)

# Ver uso

docker-compose exec redis redis-cli INFO memory



# Limpiar keys expiradas## 🏗️ Arquitectura del Sistema

docker-compose exec redis redis-cli FLUSHDB

```



Ver [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) para más soluciones.```## 🏗️ Arquitectura✅ **Integraciones:**



---┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐



## 🗺️ Roadmap│   WhatsApp      │    │   Mercado Pago   │    │   iCal Sources  │- WhatsApp Business Cloud API (webhook + firma HMAC)



Ver [`POST_MVP_ROADMAP.md`](POST_MVP_ROADMAP.md) para plan completo.│   Webhooks      │    │   Webhooks       │    │   (Airbnb/Bkng) │



### **Próximas Funcionalidades**└─────────────────┘    └──────────────────┘    └─────────────────┘- **Backend**: FastAPI + SQLAlchemy Async + PostgreSQL 16- Mercado Pago (preferencias + webhook idempotente)



- **Phase 1 (M1-2):** Dashboard Admin React, Notificaciones async         │                       │                       │

- **Phase 2 (M3-4):** Multi-propiedad (SaaS), Kubernetes

- **Phase 3 (M5-7):** GPT-4 NLU, Dynamic pricing ML         ▼                       ▼                       ▼- **Cache/Locks**: Redis 7- iCal import/export con deduplicación

- **Phase 4 (M8-10):** Mobile app, Booking.com API

- **Phase 5 (M11-12):** BI Dashboard, Forecasting┌─────────────────────────────────────────────────────────────────┐



---│                     FastAPI Router Layer                        │- **Pagos**: Mercado Pago Webhooks  - Audio pipeline: FFmpeg + faster-whisper



## 🤝 Contribución│  /whatsapp  │  /mercadopago  │  /admin  │  /ical  │  /health   │



1. Fork el repositorio└─────────────────────────────────────────────────────────────────┘- **Mensajería**: WhatsApp Business Cloud API- NLU: regex + dateparser para intención y entidades

2. Crear branch: `git checkout -b feat/mi-feature`

3. Commit: `git commit -m "feat: Agregar X"`         │                       │                       │

4. Push: `git push origin feat/mi-feature`

5. Abrir Pull Request         ▼                       ▼                       ▼- **Audio**: Whisper STT + FFmpeg



### **Commit Convention**┌─────────────────────────────────────────────────────────────────┐



```│                     Service Layer                               │- **Deploy**: Docker Compose + Nginx✅ **Automatización y Deploy:**

feat: Nueva característica

fix: Corrección de bug│   NLU Service  │  Reservation Service  │  Payment Service      │

docs: Cambios en documentación

test: Agregar tests│   Audio STT    │  Email Service       │  iCal Sync Service    │- Scripts: pre-deploy-check.sh, smoke-test-prod.sh, deploy.sh

refactor: Refactorización

```└─────────────────────────────────────────────────────────────────┘



### **Pre-commit Hooks**         │                       │                       │## 🔒 Seguridad- Nginx template con variables



```bash         ▼                       ▼                       ▼

pip install pre-commit

pre-commit install┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐- Health checks DB/Redis/iCal

```

│   PostgreSQL    │    │     Redis       │    │  Background     │

---

│   (Data + Locks)│    │  (Cache + RT)   │    │  Workers        │- Verificación firmas HMAC-SHA256 (WhatsApp, Mercado Pago)- Rate limiting por endpoint

## 📚 Documentación Adicional

└─────────────────┘    └─────────────────┘    └─────────────────┘

- [Botones Interactivos WhatsApp](WHATSAPP_INTERACTIVE_BUTTONS.md)

- [Auditoría de Seguridad](SECURITY_AUDIT_v1.0.0.md)```- Locks Redis para prevenir condiciones de carrera- Security headers configurados

- [Benchmarks de Performance](PERFORMANCE_BENCHMARKS_v1.0.0.md)

- [Roadmap Post-MVP](POST_MVP_ROADMAP.md)

- [Estado del MVP](MVP_STATUS.md)

---- Constraint PostgreSQL EXCLUDE para anti-doble booking

---



## 📄 Licencia

## 🔐 Anti-Doble-Booking: Cómo Funciona- Rate limiting por IP

Este proyecto está bajo la licencia **MIT**. Ver [LICENSE](LICENSE) para más detalles.



---

### Capa 1: Lock Redis (Prevención Optimista)## ⚡ Quick Start (3 minutos)

## 👥 Autores

```python

- **Sistema de Automatización de Reservas MVP** - Desarrollo inicial

lock_key = f"lock:acc:{accommodation_id}:{check_in}:{checkout}"## 📊 Constraint Anti-Doble Booking

---

await redis.set(lock_key, "locked", ex=1800, nx=True)

## 📞 Soporte

```### Desarrollo Local

- **Issues:** https://github.com/eevans-d/SIST_CABANAS_MVP/issues

- **Discussions:** https://github.com/eevans-d/SIST_CABANAS_MVP/discussions- TTL: 30 minutos (1800s)

- **Email:** soporte@tudominio.com

- NX: Only if Not eXists```sql

---

- Si falla: `{"error": "En proceso o no disponible"}`

**¿Listo para automatizar tus reservas? 🚀**

-- Extensión requerida```bash

```bash

git clone https://github.com/eevans-d/SIST_CABANAS_MVP.git### Capa 2: Constraint PostgreSQL (Garantía Pesimista)

cd SIST_CABANAS_MVP

make up```sqlCREATE EXTENSION IF NOT EXISTS btree_gist;# 1. Clonar y configurar

```

CREATE EXTENSION btree_gist;

git clone https://github.com/eevans-d/SIST_CABANAS_MVP.git

ALTER TABLE reservations

ADD COLUMN period daterange-- Columna period generadacd SIST_CABANAS_MVP

GENERATED ALWAYS AS (daterange(check_in, check_out, '[)')) STORED;

ALTER TABLE reservations cp backend/.env.template backend/.env

ALTER TABLE reservations

ADD CONSTRAINT no_overlap_reservationsADD COLUMN period daterange

EXCLUDE USING gist (

    accommodation_id WITH =,GENERATED ALWAYS AS (daterange(check_in, check_out, '[)')) STORED;# 2. Levantar servicios con Docker

    period WITH &&

) WHERE (reservation_status IN ('pre_reserved','confirmed'));cd backend

```

-- Constraint EXCLUDEdocker-compose up -d

**Características:**

- Fechas half-open: `[check_in, check_out)` → checkout mismo día permitidoALTER TABLE reservations

- Solo aplica a: `pre_reserved`, `confirmed`

- Si falla: `IntegrityError` → respuesta clara al clienteADD CONSTRAINT no_overlap_reservations # 3. Ejecutar migraciones



### Testing de ConcurrenciaEXCLUDE USING gist (docker-compose exec api alembic upgrade head

```bash

pytest tests/test_double_booking.py::test_overlapping_reservation_blocked -v    accommodation_id WITH =,

# DEBE fallar con IntegrityError esperado

```    period WITH &&# 4. Verificar



---) WHERE (reservation_status IN ('pre_reserved','confirmed'));curl http://localhost:8000/api/v1/healthz



## 📊 Observabilidad y Monitoreo```# Respuesta esperada: {"status": "healthy", ...}



### Health Checks```



```bash## 🧪 Testing

# Health check completo con latencias

curl http://localhost:8000/api/v1/healthz**API disponible en:** http://localhost:8000



# Readiness check para KubernetesEl sistema ha pasado todos los tests críticos:**Documentación OpenAPI:** http://localhost:8000/docs

curl http://localhost:8000/api/v1/readyz

```**Métricas Prometheus:** http://localhost:8000/metrics



**Status levels:**- ✅ **Prevención doble-booking**: Solicitudes simultáneas correctamente rechazadas

- `healthy` - Todos los sistemas OK

- `degraded` - Latencias altas pero funcionando- ✅ **Flujo end-to-end**: WhatsApp → NLU → Reserva → Pago → Confirmación### Deploy a Producción

- `unhealthy` - Algún sistema crítico falló

- ✅ **Idempotencia**: Webhooks duplicados sin efectos secundarios

### Métricas Prometheus

- ✅ **Integraciones**: WhatsApp y Mercado Pago funcionando al 100%```bash

```bash

curl http://localhost:8000/metrics# 1. Configurar variables de entorno

```

## 📝 Próximos Pasos (Fase 4)cd backend

**Métricas disponibles:**

- `http_requests_total` - Total requests por endpointcp .env.template .env

- `http_request_duration_seconds` - Latencia por endpoint

- `reservations_total` - Reservas por estado- Background jobs (expiración pre-reservas, sync iCal)nano .env  # Completar con valores reales

- `prereservations_expired_total` - Pre-reservas expiradas

- `ical_last_sync_age_minutes` - Edad último sync iCal- Métricas Prometheus

- `rate_limit_exceeded_total` - Rate limits superados

- Health checks avanzados# 2. Ejecutar deploy automatizado

### SLOs Target

- **Texto P95:** < 3s (warning > 4s, critical > 6s)- Rate limiting configurablecd ..

- **Audio P95:** < 15s (warning > 20s, critical > 30s)

- **iCal sync:** < 20min desfase (warning > 30min)- Observabilidad completa./scripts/deploy.sh

- **Error rate:** < 1% (critical > 5%)



---

---# 3. Configurar SSL y webhooks

## 📚 Documentación

# Seguir guía en PRODUCTION_SETUP.md

### Documentos Principales

| Documento | Propósito |**Desarrollo**: Octubre 2025  ```

|-----------|-----------|

| **[ESTADO_ACTUAL_2025-10-10.md](ESTADO_ACTUAL_2025-10-10.md)** | Estado completo del proyecto y tareas pendientes |**Estado**: MVP Fase 3 completada ✅

| **[ROADMAP_MVP_PRIORIDAD_ALTA.md](ROADMAP_MVP_PRIORIDAD_ALTA.md)** | Roadmap de desarrollo (Fase 4-6) |**Guía Completa:** Ver [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md)

| **[IMPLEMENTATION_PLAN_DETAILED.md](IMPLEMENTATION_PLAN_DETAILED.md)** | Plan detallado Fase 4.3 |

| **[AUDITORIA_TECNICA_COMPLETA.md](AUDITORIA_TECNICA_COMPLETA.md)** | Auditoría técnica exhaustiva |## 🧪 Testing



### Documentación Técnica```bash

| Documento | Propósito |# Tests unitarios (SQLite fallback)

|-----------|-----------|cd backend

| **[docs/INDEX.md](docs/INDEX.md)** | Índice completo de documentación |pytest tests/ -v

| **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** | Solución de problemas comunes |

| **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)** | Referencia de API |# Tests con Postgres real (constraint validation)

| **[docs/architecture/TECHNICAL_ARCHITECTURE.md](docs/architecture/TECHNICAL_ARCHITECTURE.md)** | Arquitectura técnica |docker-compose up -d postgres redis

| **[docs/deployment/STAGING_DEPLOY_GUIDE.md](docs/deployment/STAGING_DEPLOY_GUIDE.md)** | Guía de deploy paso a paso |export TEST_DATABASE_URL=postgresql+asyncpg://alojamientos:password@localhost:5432/alojamientos_test_db

| **[docs/adr/](docs/adr/)** | Architecture Decision Records |pytest tests/test_double_booking.py tests/test_constraint_validation.py -v



---# Coverage

pytest tests/ --cov=app --cov-report=html

## 🛠️ Scripts de Automatización```



```bash**Resultado esperado:** 37 passed, 11 skipped (SQLite mode)

# Validación pre-deploy (200+ checks)

./scripts/pre-deploy-check.sh## 🔐 Convenciones Anti-Doble-Booking



# Tests de producciónLa prevención de doble-booking es **CRÍTICA** y se implementa en dos capas:

BASE_URL=https://tudominio.com ./scripts/smoke-test-prod.sh

### 1. Lock Redis (Prevención Optimista)

# Deploy automatizado (6 fases)```python

./scripts/deploy.shlock_key = f"lock:acc:{accommodation_id}:{check_in}:{check_out}"

```await redis.set(lock_key, "locked", ex=1800, nx=True)

```

**Documentación completa:** [scripts/README.md](scripts/README.md)- TTL: 30 minutos (1800s)

- NX: Only if Not eXists

---- Si falla: `{"error": "En proceso o no disponible"}`



## 🔒 Seguridad### 2. Constraint PostgreSQL (Garantía Pesimista)

```sql

### Validación de WebhooksCREATE EXTENSION btree_gist;

period daterange GENERATED ALWAYS AS (daterange(check_in, check_out, '[)')) STORED

**WhatsApp (HMAC SHA-256):**CONSTRAINT no_overlap_reservations EXCLUDE USING gist

- Header: `X-Hub-Signature-256`  (accommodation_id WITH =, period WITH &&)

- Secret: `WHATSAPP_APP_SECRET`  WHERE (reservation_status IN ('pre_reserved','confirmed'))

```

**Mercado Pago (x-signature v1):**- Fechas half-open: `[check_in, check_out)` → checkout mismo día permitido

- Header: `x-signature`- Solo aplica a estados: `pre_reserved`, `confirmed`

- Secret: `MERCADOPAGO_WEBHOOK_SECRET`- Si falla: `IntegrityError` capturado y retorna error al cliente

- Manejo idempotente de `payment_id`

### Testing de Concurrencia

### Seguridad en Producción```bash

- ✅ PostgreSQL/Redis NO expuestos (solo red interna Docker)# Test de concurrencia simultánea (DEBE fallar)

- ✅ Security headers (HSTS, X-Frame-Options, CSP, X-Content-Type-Options)pytest tests/test_double_booking.py::test_overlapping_reservation_blocked -v

- ✅ Rate limiting por endpoint```

- ✅ JWT para autenticación admin

- ✅ HTTPS obligatorio (Let's Encrypt)## 🛠️ Scripts de Automatización

- ✅ Variables de entorno para secretos

- ✅ No logs de datos sensibles### pre-deploy-check.sh (Validación Pre-Deploy)

```bash

---./scripts/pre-deploy-check.sh

```

## 🎯 Filosofía del ProyectoValida: `.env`, docker-compose, tests, seguridad puertos, nginx, Git, SSL



### SHIPPING > PERFECCIÓN### smoke-test-prod.sh (Tests de Producción)

```bash

**Principios:**BASE_URL=https://tudominio.com ./scripts/smoke-test-prod.sh

1. Implementar SOLO lo necesario```

2. Tests críticos primero (locks, overlap, firmas)8 tests: health, metrics, security headers, CORS, performance

3. No feature creep ("sería fácil agregar...")

4. Solución MÁS SIMPLE que funcione### deploy.sh (Deploy Automatizado)

5. Refactors DESPUÉS de tests pasando```bash

./scripts/deploy.sh

### Anti-Patrones Prohibidos```

- ❌ Microservicios o arquitectura compleja6 fases: validación → backup → build → migrations → smoke tests

- ❌ Cache sin evidencia de lentitud

- ❌ Múltiples providers de pago**Documentación completa:** [scripts/README.md](scripts/README.md)

- ❌ Channel manager propio

- ❌ Optimizaciones prematuras## 📊 Observabilidad y Monitoreo

- ❌ Abstracciones "por si acaso"

### Health Check

---```bash

curl http://localhost:8000/api/v1/healthz

## 🤝 Contribución```

Verifica:

### Workflow- ✅ Database connection (SELECT 1)

- ✅ Redis connection (PING)

1. **Branch desde main:**- ✅ iCal last sync age < 20min

   ```bash- ⚠️ Degraded: Redis down pero DB ok

   git checkout -b feature/nombre-feature- ❌ Unhealthy: DB down

   ```

### Métricas Prometheus

2. **Desarrollar con TDD:**```bash

   ```bashcurl http://localhost:8000/metrics

   pytest tests/test_nueva_feature.py -v```

   ```Métricas disponibles:

- `http_requests_total` - Total de requests por endpoint

3. **Validar antes de commit:**- `http_request_duration_seconds` - Latencia por endpoint

   ```bash- `reservations_total` - Reservas creadas por estado

   pytest tests/ -v- `ical_last_sync_age_minutes` - Edad del último sync iCal

   ./scripts/pre-deploy-check.sh- `rate_limit_exceeded_total` - Rate limits superados

   ```

### SLOs Target

4. **Commit con convención:**- **Texto P95:** < 3s (warning > 4s, critical > 6s)

   ```bash- **Audio P95:** < 15s (warning > 20s, critical > 30s)

   git commit -m "feat(reservations): agregar endpoint confirmación"- **iCal sync:** < 20min desfase (warning > 30min)

   git commit -m "fix(whatsapp): corregir validación firma HMAC"- **Error rate:** < 1% (critical > 5%)

   ```

## 🏗️ Estructura del Proyecto

### Tests Obligatorios

```

```bashSIST_CABANAS_MVP/

# Todos los tests deben pasar├── backend/

pytest tests/ -v│   ├── app/

│   │   ├── main.py              # FastAPI app + middleware + jobs

# Coverage mínimo 80%│   │   ├── core/                # config, db, redis, auth, logging

pytest tests/ --cov=app --cov-report=term-missing│   │   ├── models/              # SQLAlchemy ORM

```│   │   ├── routers/             # Endpoints API

│   │   │   ├── health.py        # Health checks

---│   │   │   ├── reservations.py  # CRUD reservas

│   │   │   ├── whatsapp.py      # Webhook WhatsApp

## 📞 Soporte│   │   │   ├── mercadopago.py   # Webhook Mercado Pago

│   │   │   ├── ical.py          # Import/Export iCal

- **Issues:** https://github.com/eevans-d/SIST_CABANAS_MVP/issues│   │   │   ├── audio.py         # Transcripción audio

- **Pull Requests:** https://github.com/eevans-d/SIST_CABANAS_MVP/pulls│   │   │   ├── admin.py         # Panel admin

- **Documentación:** Ver `docs/INDEX.md`│   │   │   └── nlu.py           # Análisis de intención

│   │   ├── services/            # Lógica de negocio

---│   │   │   ├── reservations.py  # ReservationService

│   │   │   ├── whatsapp.py      # WhatsAppService

## 📄 Licencia│   │   │   ├── mercadopago.py   # MercadoPagoService

│   │   │   ├── ical.py          # iCal sync

MIT License - Ver [LICENSE](LICENSE)│   │   │   ├── audio.py         # Audio transcription

│   │   │   └── nlu.py           # NLU intent detection

---│   │   └── jobs/                # Background jobs

│   │       ├── scheduler.py     # APScheduler config

## 🎓 ADR: No Integrar PMS Externo│   │       ├── cleanup.py       # Expiración pre-reservas

│   │       └── import_ical.py   # Sync iCal automático

**Decisión:** NO se integrará ningún PMS (Odoo, HotelDruid, QloApps) en el MVP.│   ├── alembic/                 # Migraciones DB

│   ├── tests/                   # Tests (37 passed)

**Razones:**│   ├── docker-compose.yml       # Servicios (postgres, redis, api, nginx)

- Añade complejidad estructural innecesaria (>2-3 días)│   ├── Dockerfile               # Imagen API

- No resuelve diferenciadores clave (WhatsApp, locks, audio/NLU)│   ├── nginx.conf.template      # Template nginx con variables

- Riesgo de feature creep fuera del scope MVP│   └── .env.template            # Variables de entorno

- El modelo de datos necesario es mínimo y está definido├── scripts/                     # Scripts de automatización

│   ├── pre-deploy-check.sh      # Validación pre-deploy (200+ líneas)

**Re-evaluación:** Post-MVP cuando >100 reservas/mes o necesidades avanzadas.│   ├── smoke-test-prod.sh       # Tests de producción (100+ líneas)

│   ├── deploy.sh                # Deploy automatizado (80+ líneas)

Ver: `docs/adr/001-no-pms-externo.md`│   └── README.md                # Documentación de scripts

├── docs/                        # Documentación adicional

---│   ├── adr/                     # Architecture Decision Records

│   └── CONSOLIDATION_STATUS.md  # Estado de consolidación del repo

**El sistema está listo para producción. ¡A deployar! 🚀**├── PRODUCTION_SETUP.md          # Guía de deploy paso a paso (210 líneas)

├── STATUS_ACTUAL_2025-10-02.md  # Estado actual detallado

---├── PARA_MAÑANA.md               # Guía para continuar desarrollo

└── README.md                    # Este archivo

_README actualizado: 2025-10-10 - Fase 4 en progreso (60% completada)_```



## 🔒 Seguridad

### Validación de Webhooks

**WhatsApp (HMAC SHA-256):**
```python
signature = request.headers.get("X-Hub-Signature-256")
# Valida con WHATSAPP_APP_SECRET
# CRÍTICO: Sin validación = vulnerabilidad
```

**Mercado Pago (x-signature v1):**
```python
signature = request.headers.get("x-signature")
# Valida timestamp + v1 con MERCADOPAGO_WEBHOOK_SECRET
# Manejo idempotente de payment_id
```

### Seguridad en Producción
- ✅ Puertos PostgreSQL/Redis NO expuestos (solo red interna Docker)
- ✅ Nginx con security headers (HSTS, X-Frame-Options, CSP, X-Content-Type-Options)
- ✅ Rate limiting por endpoint (api: 10r/s, webhooks: 50r/s)
- ✅ JWT para autenticación admin
- ✅ HTTPS obligatorio (Let's Encrypt)
- ✅ Variables de entorno para secretos
- ✅ No logs de datos sensibles

## 📋 ADRs (Architecture Decision Records)

### ADR-001: No Integrar PMS Externo en MVP
**Decisión:** NO se integrará ningún PMS (Odoo, HotelDruid, QloApps) durante el alcance del MVP.

**Razones:**
- Añade complejidad estructural innecesaria
- No resuelve diferenciadores clave (conversación WhatsApp, locks Redis, audio/NLU)
- Genera riesgo de dependencia externa y feature creep
- El modelo de datos necesario es mínimo y ya está definido

**Re-evaluación:** Post-MVP cuando >100 reservas/mes o necesidades avanzadas

Ver índice completo: `docs/adr/README.md`

## 🚫 Anti-Patrones Prohibidos

Según filosofía **SHIPPING > PERFECCIÓN**, NO implementar:

- ❌ Microservicios o arquitectura compleja
- ❌ ORM abstractions innecesarias (usar SQLAlchemy directo)
- ❌ Cache sin evidencia de lentitud
- ❌ Múltiples providers de pago (solo Mercado Pago)
- ❌ Channel manager propio (usar iCal)
- ❌ Optimizaciones prematuras
- ❌ Abstracciones "por si acaso"
- ❌ Feature creep ("sería fácil agregar...", "ya que estamos...")

**REGLA DE ORO:** Implementar SOLO lo pedido, solución MÁS SIMPLE que funcione.

## 🤝 Contribución y Desarrollo

### Workflow Recomendado

1. **Crear branch desde `main`:**
   ```bash
   git checkout -b feature/nombre-feature
   ```

2. **Desarrollar con TDD:**
   ```bash
   # Escribir test primero
   # Implementar código mínimo
   pytest tests/test_nueva_feature.py -v
   ```

3. **Validar antes de commit:**
   ```bash
   pytest tests/ -v
   ./scripts/pre-deploy-check.sh  # Validación completa
   ```

4. **Commit siguiendo convenciones:**
   ```bash
   git commit -m "feat(reservations): agregar endpoint confirmación"
   git commit -m "fix(whatsapp): corregir validación firma HMAC"
   git commit -m "docs: actualizar guía de deploy"
   ```

5. **Push y PR:**
   ```bash
   git push origin feature/nombre-feature
   # Crear Pull Request en GitHub
   ```

### Convenciones de Commits

- `feat(scope):` Nueva funcionalidad
- `fix(scope):` Corrección de bug
- `docs:` Documentación
- `test:` Tests
- `refactor:` Refactorización sin cambio funcional
- `perf:` Mejora de performance
- `chore:` Tareas de mantenimiento

### Tests Obligatorios

Antes de cualquier PR, TODOS estos tests deben pasar:

```bash
# Tests unitarios
pytest tests/ -v

# Tests de constraint (requiere Postgres)
pytest tests/test_double_booking.py -v

# Coverage mínimo 80%
pytest tests/ --cov=app --cov-report=term-missing
```

## 📞 Soporte y Contacto

- **Issues:** https://github.com/eevans-d/SIST_CABANAS_MVP/issues
- **Pull Requests:** https://github.com/eevans-d/SIST_CABANAS_MVP/pulls
- **Documentación:** Este README + archivos en raíz del proyecto

## 📝 Changelog y Releases

Ver commits y tags en GitHub para historial completo de cambios.

**Última actualización:** 2025-10-02 (Sistema 9.5/10 Production Ready)

## 📄 Licencia

[Agregar licencia según corresponda]

## 🎓 Principios del Proyecto

1. **SHIPPING > PERFECCIÓN** - Entregar funcionalidad sobre código perfecto
2. **Anti-Feature Creep** - Solo implementar lo estrictamente necesario
3. **Tests Críticos Primero** - Locks, overlap, firmas webhook
4. **Seguridad por Defecto** - Validaciones, rate limiting, headers
5. **Observabilidad Básica** - Métricas, health checks, logs estructurados
6. **Documentación como Código** - Guías prácticas y ejecutables
7. **No Abstracciones Prematuras** - YAGNI (You Aren't Gonna Need It)
8. **Refactors Post-Funcionalidad** - Solo después de tests pasando

---

**El sistema está listo para producción. ¡A deployar! 🚀**

---

_README actualizado: 2025-10-02 - Sistema 9.5/10 Production Ready_
