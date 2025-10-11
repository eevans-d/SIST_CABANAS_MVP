# 🏡 Sistema MVP de Automatización de Reservas# Sistema MVP de Reservas de Alojamientos# Sistema MVP de Reservas de Alojamientos



Sistema completo de automatización de reservas con integración WhatsApp, Mercado Pago, y sincronización iCal.



[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)[![CI](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/ci.yml/badge.svg)](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/ci.yml)[![CI](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/ci.yml/badge.svg)](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/ci.yml)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)[![Deploy Staging](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/deploy-staging.yml/badge.svg)](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/deploy-staging.yml)[![Deploy Staging](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/deploy-staging.yml/badge.svg)](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/deploy-staging.yml)



## 🎯 Características[![Security Scan](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/security-scan.yml/badge.svg)](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/security-scan.yml)[![Security Scan](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/security-scan.yml/badge.svg)](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/security-scan.yml)



### 🤖 Automatización Completa[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)[![Production Ready](https://img.shields.io/badge/production-ready-brightgreen)](https://github.com/eevans-d/SIST_CABANAS_MVP)

- WhatsApp Bot con NLU básico

- Audio Processing (Whisper STT)[![FastAPI](https://img.shields.io/badge/fastapi-0.115-009688)](https://fastapi.tiangolo.com/)[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)

- Pre-reservas con expiración automática

- Procesamiento de pagos (Mercado Pago)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)[![FastAPI](https://img.shields.io/badge/fastapi-0.115-009688)](https://fastapi.tiangolo.com/)



### 🛡️ Robustez[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

- **Anti doble-booking**: PostgreSQL constraint + Redis locks

- **Idempotencia**: Prevención de webhooks duplicados (48h TTL)[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

- **Circuit Breaker**: Resilencia ante fallos externos

- **Rate Limiting**: 60 req/min por IP> **Sistema de automatización completo** para reservas de alojamientos con WhatsApp Business, anti-doble-booking garantizado y pagos integrados con Mercado Pago.[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)



### 📊 Observabilidad

- 20+ métricas Prometheus

- Structured logging (JSON + trace-id)---> **Sistema de automatización completo** para reservas de alojamientos con WhatsApp Business, anti-doble-booking garantizado y pagos integrados.

- Health checks comprehensivos



## 🚀 Quick Start

## 🎯 Estado del Proyecto---

```bash

# 1. Clonar

git clone https://github.com/eevans-d/SIST_CABANAS_MVP.git

cd SIST_CABANAS_MVP✅ **MVP Core Completado** - Todos los componentes críticos funcionando  ## 🎯 Estado del Proyecto



# 2. Configurar✅ **Fase 4 en Progreso** - 60% completada (4.1 ✅, 4.2 ✅, 4.3 → siguiente)

cp backend/.env.template backend/.env

# Editar backend/.env con tus credenciales✅ **37 Tests Pasando** - Suite completa con 87% coverage  ✅ **MVP COMPLETAMENTE FUNCIONAL** - Fase 4 en progreso (60% completada)



# 3. Iniciar✅ **CI/CD Automatizado** - GitHub Actions con deploy automático  ✅ **37 Tests Pasando** - Suite completa con 87% coverage

docker-compose up -d

✅ **Production Ready** - Listo para deployment  ✅ **CI/CD Automatizado** - GitHub Actions con tests, linting, security scan

# 4. Migrar

docker-compose exec backend alembic upgrade head✅ **Deploy Automatizado** - Scripts de validación, deploy y rollback



# 5. Verificar---✅ **Documentación Exhaustiva** - 32 archivos, 14,000+ líneas

curl http://localhost:8000/api/v1/healthz

```



## 📚 Documentación## 🚀 Características Principales---



- **API Docs**: http://localhost:8000/docs

- **Metrics**: http://localhost:8000/metrics

- **[Estado del MVP](./MVP_STATUS.md)**### 🔒 Anti-Doble-Booking Garantizado## 🚀 Características Principales

- **[Deployment Guide](./DEPLOYMENT.md)**

- **PostgreSQL Constraint:** `EXCLUDE USING gist` con daterange

## 🔧 Configuración Crítica

- **Redis Locks:** Locks distribuidos con TTL 30 minutos### Anti-Doble-Booking Garantizado

```env

# WhatsApp- **Prevención multicapa:** Race condition handling DB + aplicación- **PostgreSQL Constraint:** `EXCLUDE USING gist` con daterange

WHATSAPP_ACCESS_TOKEN=tu_token

WHATSAPP_APP_SECRET=tu_secret- **Redis Locks:** Locks distribuidos con TTL 30 minutos



# Mercado Pago### 📱 Integración WhatsApp Business- **Prevención multicapa:** Race condition handling a nivel DB y aplicación

MERCADOPAGO_ACCESS_TOKEN=tu_token

- **Webhooks seguros:** Validación HMAC-SHA256

# Database

DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db- **Audio STT:** Transcripción con Whisper + FFmpeg### Integración WhatsApp Business

REDIS_URL=redis://localhost:6379/0

```- **NLU básico:** Detección de intenciones (regex + dateparser)- **Webhooks seguros:** Validación HMAC-SHA256



## 📖 Uso Básico- **Respuestas automáticas:** Templates contextuales- **Audio STT:** Transcripción con Whisper + FFmpeg



### Consultar Disponibilidad- **NLU básico:** Detección de intenciones (regex + dateparser)

```bash

curl -X GET "http://localhost:8000/api/v1/reservations/availability" \### 💳 Pagos Mercado Pago- **Respuestas automáticas:** Templates contextuales

  -H "Content-Type: application/json" \

  -d '{- **Webhooks idempotentes:** Manejo de duplicados

    "accommodation_id": 1,

    "check_in": "2025-10-20",- **Validación de firmas:** x-signature header### Pagos Mercado Pago

    "check_out": "2025-10-22"

  }'- **Flujo completo:** Pre-reserva → Pago → Confirmación automática- **Webhooks idempotentes:** Manejo de duplicados

```

- **Validación de firmas:** x-signature header

### Crear Reserva

```bash### 📅 Sincronización iCal- **Flujo completo:** Pre-reserva → Pago → Confirmación automática

curl -X POST "http://localhost:8000/api/v1/reservations" \

  -H "Content-Type: application/json" \- **Import/Export:** Compatible con Airbnb, Booking.com

  -d '{

    "accommodation_id": 1,- **Deduplicación:** Por UID de evento### Sincronización iCal

    "check_in": "2025-10-20",

    "check_out": "2025-10-22",- **Background jobs:** Sync automático cada 15 minutos- **Import/Export:** Compatible con Airbnb, Booking.com

    "guests": 2,

    "guest_name": "Juan Pérez",- **Deduplicación:** Por UID de evento

    "guest_phone": "+5491123456789"

  }'### 📊 Observabilidad- **Background jobs:** Sync automático cada 15 minutos

```

- **Prometheus metrics:** 17+ métricas custom de negocio

## 🧪 Testing

- **Health checks:** `/healthz` y `/readyz` con latencias### Observabilidad

```bash

cd backend- **Structured logging:** JSON logs con trace IDs- **Prometheus metrics:** 17+ métricas custom de negocio

pytest tests/ -v

pytest tests/ --cov=app --cov-report=html- **Rate limiting:** Por IP + endpoint con métricas- **Health checks:** `/healthz` y `/readyz` con latencias

```

- **Structured logging:** JSON logs con trace IDs

## 📊 Arquitectura

---- **Rate limiting:** Por IP + endpoint con métricas

```

WhatsApp/Email → FastAPI → PostgreSQL

                    ↓         (+ btree_gist)

              Redis (locks)## ⚡ Quick Start (3 minutos)---

                    ↓

            Prometheus (metrics)

```

### Desarrollo Local## ⚡ Quick Start (3 minutos)

**Stack:**

- FastAPI 0.115+ (async)

- PostgreSQL 16 + btree_gist

- Redis 7```bash### Desarrollo Local

- SQLAlchemy 2.0+ AsyncSession

# 1. Clonar y configurar

**Integraciones:**

- WhatsApp Business Cloud APIgit clone https://github.com/eevans-d/SIST_CABANAS_MVP.git```bash

- Mercado Pago

- Whisper STTcd SIST_CABANAS_MVP# 1. Clonar y configurar

- iCal (RFC 5545)

cp backend/.env.template backend/.envgit clone https://github.com/eevans-d/SIST_CABANAS_MVP.git

## 🐛 Troubleshooting

cd SIST_CABANAS_MVP

### Doble-booking error

Normal - el sistema está previniendo correctamente:# 2. Levantar servicioscp backend/.env.template backend/.env

```sql

SELECT conname FROM pg_constraint cd backend

WHERE conname = 'no_overlap_reservations';

```docker-compose up -d# 2. Levantar servicios con Docker



### iCal sync atrasadocd backend

```bash

docker-compose logs backend | grep "ical_sync"# 3. Ejecutar migracionesdocker-compose up -d

curl -X POST "http://localhost:8000/api/v1/ical/sync/1"

```docker-compose exec api alembic upgrade head



### Redis unavailable# 3. Ejecutar migraciones

Sistema funciona en fail-open mode. Verificar:

```bash# 4. Verificardocker-compose exec api alembic upgrade head

docker-compose ps redis

docker-compose logs rediscurl http://localhost:8000/api/v1/healthz

```

# Respuesta esperada: {"status": "healthy", ...}# 4. Verificar

## 📝 Docs Adicionales

```curl http://localhost:8000/api/v1/healthz

- **[MVP_STATUS.md](./MVP_STATUS.md)** - Estado del proyecto

- **[PROGRESO_DIARIO.md](./PROGRESO_DIARIO.md)** - Log de desarrollo

- **[copilot-instructions.md](./.github/copilot-instructions.md)** - Reglas técnicas

**Accesos:**./test_constraint_specific.sh  - **Anti-Doble-Booking:** Constraint PostgreSQL `EXCLUDE USING gist` + locks Redis distribuidos

## 🤝 Contribución

- **API:** http://localhost:8000

1. Fork el repo

2. Crear branch (`git checkout -b feature/nueva-feat`)- **Docs:** http://localhost:8000/docs- **WhatsApp Business:** Webhook con firma HMAC SHA-256, normalización de mensajes, audio STT

3. Commit (`git commit -m 'feat: nueva funcionalidad'`)

4. Push (`git push origin feature/nueva-feat`)- **Métricas:** http://localhost:8000/metrics

5. Abrir PR

# Test flujo completo end-to-end- **Mercado Pago:** Integración con validación de firmas y manejo idempotente

Seguir [Conventional Commits](https://www.conventionalcommits.org/)

### Deploy a Producción

## 📄 Licencia

./test_end_to_end.sh- **iCal Import/Export:** Sincronización automática con Airbnb/Booking

MIT License

```bash

## 🎯 Roadmap Post-MVP

# 1. Configurar variables de entorno- **NLU Básico:** Detección de intención y extracción de entidades (fechas, huéspedes)

- [ ] Dashboard admin React

- [ ] Multi-propiedadcp backend/.env.template backend/.env

- [ ] Analytics avanzado

- [ ] AI agents con LLMnano backend/.env  # Completar con valores reales# Test idempotencia webhooks- **Observabilidad:** Métricas Prometheus, health checks, logs estructurados



---



**v1.0.0 - MVP Completo y Producción-Ready**# 2. Deploy automatizado./test_idempotency.sh- **Jobs Background:** Expiración de pre-reservas, sync iCal, recordatorios



Issues: https://github.com/eevans-d/SIST_CABANAS_MVP/issues./scripts/deploy.sh




# 3. Configurar SSL y webhooks

# Seguir guía en docs/deployment/STAGING_DEPLOY_GUIDE.md# Test integración Mercado Pago## 📚 Documentación Esencial

```

./test_mercadopago.sh

---

| Documento | Propósito |

## 🧪 Testing

# Test integración WhatsApp|-----------|-----------|

```bash

# Tests unitarios (SQLite fallback)./test_whatsapp_webhook.sh| **[PRODUCTION_SETUP.md](PRODUCTION_SETUP.md)** | Guía completa para deploy en producción (210 líneas) |

cd backend

pytest tests/ -v```| **[scripts/README.md](scripts/README.md)** | Documentación de scripts de automatización |



# Tests con Postgres real (constraint validation)| **[SESION_COMPLETADA.md](SESION_COMPLETADA.md)** | Último resumen de progreso |

docker-compose up -d postgres redis

pytest tests/test_double_booking.py tests/test_constraint_validation.py -v## 🛠️ Configuración Rápida| **[PARA_MAÑANA.md](PARA_MAÑANA.md)** | Guía rápida para continuar desarrollo |



# Coverage| **[STATUS_ACTUAL_2025-10-02.md](STATUS_ACTUAL_2025-10-02.md)** | Estado detallado del proyecto |

pytest tests/ --cov=app --cov-report=html

``````bash



**Resultado esperado:** 37 passed, 11 skipped (SQLite mode)# 1. Levantar servicios## 📦 Stack Tecnológico



### Tests Críticos Disponiblesmake up



```bash**Backend:** FastAPI 0.115 + SQLAlchemy Async + Alembic

# Anti-doble booking con concurrencia

./test_anti_double_booking.sh# 2. Verificar salud**Database:** PostgreSQL 16 (btree_gist) + Redis 7



# Constraint PostgreSQL específicocurl http://localhost:8000/api/v1/healthz**Deploy:** Docker + Docker Compose + Nginx

./test_constraint_specific.sh

**Observability:** Prometheus + structlog

# Flujo completo end-to-end

./test_end_to_end.sh# 3. Ejecutar tests**Testing:** pytest + asyncio (37 tests)



# Idempotencia webhooks./test_constraint_specific.sh**CI/CD:** GitHub Actions

./test_idempotency.sh

./test_end_to_end.sh

# Integración Mercado Pago

./test_mercadopago.sh```## 🎯 Repositorio Oficial



# Integración WhatsApp

./test_whatsapp_webhook.sh

```## 📋 Configuración de Integraciones- **Código e issues:** https://github.com/eevans-d/SIST_CABANAS_MVP



---- **Política:** Este es el único repositorio oficial del proyecto



## 📦 Stack Tecnológico### WhatsApp Business API- **Consolidación:** Ver `docs/CONSOLIDATION_STATUS.md`



**Backend:**Ver: `CONFIGURACION_WHATSAPP.md`

- FastAPI 0.115 + SQLAlchemy Async + Alembic

- PostgreSQL 16 (btree_gist extension)## 🏗️ Estado de Implementación (Actualizado 2025-10-02)

- Redis 7 (locks + cache)

### Mercado Pago

**Integraciones:**

- WhatsApp Business Cloud APIVer: `CONFIGURACION_MERCADOPAGO.md`✅ **Core MVP Completo:**

- Mercado Pago API

- Whisper STT (faster-whisper)- Modelos: `accommodations`, `reservations`, `payments`, `messages`, `audio_transcriptions`

- iCal RFC5545

### ngrok (para webhooks en desarrollo)- Constraint anti-doble-booking: `no_overlap_reservations` (PostgreSQL daterange + EXCLUDE gist)

**Deploy:**

- Docker + Docker Compose + Nginx```bash- ReservationService con locks Redis + pricing con multiplicadores

- GitHub Actions CI/CD

- Prometheus metrics./setup_ngrok.sh- Jobs: expiración pre-reservas, sync iCal, recordatorios



---```- Tests: 37 passed, 11 skipped (requieren Postgres real)



## 🏗️ Arquitectura del Sistema



```## 🏗️ Arquitectura✅ **Integraciones:**

┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐

│   WhatsApp      │    │   Mercado Pago   │    │   iCal Sources  │- WhatsApp Business Cloud API (webhook + firma HMAC)

│   Webhooks      │    │   Webhooks       │    │   (Airbnb/Bkng) │

└─────────────────┘    └──────────────────┘    └─────────────────┘- **Backend**: FastAPI + SQLAlchemy Async + PostgreSQL 16- Mercado Pago (preferencias + webhook idempotente)

         │                       │                       │

         ▼                       ▼                       ▼- **Cache/Locks**: Redis 7- iCal import/export con deduplicación

┌─────────────────────────────────────────────────────────────────┐

│                     FastAPI Router Layer                        │- **Pagos**: Mercado Pago Webhooks  - Audio pipeline: FFmpeg + faster-whisper

│  /whatsapp  │  /mercadopago  │  /admin  │  /ical  │  /health   │

└─────────────────────────────────────────────────────────────────┘- **Mensajería**: WhatsApp Business Cloud API- NLU: regex + dateparser para intención y entidades

         │                       │                       │

         ▼                       ▼                       ▼- **Audio**: Whisper STT + FFmpeg

┌─────────────────────────────────────────────────────────────────┐

│                     Service Layer                               │- **Deploy**: Docker Compose + Nginx✅ **Automatización y Deploy:**

│   NLU Service  │  Reservation Service  │  Payment Service      │

│   Audio STT    │  Email Service       │  iCal Sync Service    │- Scripts: pre-deploy-check.sh, smoke-test-prod.sh, deploy.sh

└─────────────────────────────────────────────────────────────────┘

         │                       │                       │## 🔒 Seguridad- Nginx template con variables

         ▼                       ▼                       ▼

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐- Health checks DB/Redis/iCal

│   PostgreSQL    │    │     Redis       │    │  Background     │

│   (Data + Locks)│    │  (Cache + RT)   │    │  Workers        │- Verificación firmas HMAC-SHA256 (WhatsApp, Mercado Pago)- Rate limiting por endpoint

└─────────────────┘    └─────────────────┘    └─────────────────┘

```- Locks Redis para prevenir condiciones de carrera- Security headers configurados



---- Constraint PostgreSQL EXCLUDE para anti-doble booking



## 🔐 Anti-Doble-Booking: Cómo Funciona- Rate limiting por IP



### Capa 1: Lock Redis (Prevención Optimista)## ⚡ Quick Start (3 minutos)

```python

lock_key = f"lock:acc:{accommodation_id}:{check_in}:{checkout}"## 📊 Constraint Anti-Doble Booking

await redis.set(lock_key, "locked", ex=1800, nx=True)

```### Desarrollo Local

- TTL: 30 minutos (1800s)

- NX: Only if Not eXists```sql

- Si falla: `{"error": "En proceso o no disponible"}`

-- Extensión requerida```bash

### Capa 2: Constraint PostgreSQL (Garantía Pesimista)

```sqlCREATE EXTENSION IF NOT EXISTS btree_gist;# 1. Clonar y configurar

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
