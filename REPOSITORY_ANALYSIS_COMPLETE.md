# 📊 ANÁLISIS EXHAUSTIVO DEL REPOSITORIO SIST_CABANAS_MVP

**Fecha:** 2025-10-01  
**Repositorio:** https://github.com/eevans-d/SIST_CABANAS_MVP  
**Versión:** 1.0.0 (MVP Completado 2025-09-27)  
**Tiempo de desarrollo:** 10-12 días  
**Estado:** Production Ready

---

## ÍNDICE

1. [PROMPT 1: Metadatos y Contexto del Proyecto](#prompt-1)
2. [PROMPT 2: Arquitectura y Componentes](#prompt-2)
3. [PROMPT 3: Agentes de IA y Configuración](#prompt-3)
4. [PROMPT 4: Dependencias y Stack Tecnológico](#prompt-4)
5. [PROMPT 5: Contratos de Interfaz y APIs](#prompt-5)
6. [PROMPT 6: Flujos Críticos y Casos de Uso](#prompt-6)
7. [PROMPT 7: Configuración y Variables de Entorno](#prompt-7)
8. [PROMPT 8: Manejo de Errores y Excepciones](#prompt-8)
9. [PROMPT 9: Seguridad y Validación](#prompt-9)
10. [PROMPT 10: Tests y Calidad de Código](#prompt-10)
11. [PROMPT 11: Performance y Métricas](#prompt-11)
12. [PROMPT 12: Logs e Incidentes Históricos](#prompt-12)
13. [PROMPT 13: Deployment y Operaciones](#prompt-13)
14. [PROMPT 14: Documentación y Comentarios](#prompt-14)
15. [PROMPT 15: Análisis de Complejidad y Deuda Técnica](#prompt-15)
16. [PROMPT FINAL: Resumen Ejecutivo](#prompt-16)

---

<a name="prompt-1"></a>
## PROMPT 1: METADATOS Y CONTEXTO DEL PROYECTO

```json
{
  "project_metadata": {
    "name": "Sistema MVP Reservas Alojamientos",
    "version": "1.0.0",
    "description": "Sistema MVP de reservas de alojamientos con automatización completa para WhatsApp y email. Diseñado para construirse en 10-12 días con enfoque anti doble-booking. Filosofía: SHIPPING > PERFECCIÓN.",
    "repository_structure": {
      "total_files": "~120 archivos",
      "total_lines_of_code": "~4644 líneas (2800 backend/app + 1844 tests)",
      "main_directories": [
        {
          "name": "backend/",
          "purpose": "Código Python principal (FastAPI)",
          "files": 90
        },
        {
          "name": "backend/app/",
          "purpose": "Aplicación core (routers, services, models, jobs)",
          "files": 36,
          "loc": 2800
        },
        {
          "name": "backend/tests/",
          "purpose": "27 archivos de tests unitarios/integración",
          "files": 27,
          "loc": 1844
        },
        {
          "name": "backend/tests_e2e/",
          "purpose": "2 archivos de tests end-to-end",
          "files": 2
        },
        {
          "name": "backend/alembic/",
          "purpose": "4 migraciones PostgreSQL",
          "files": 4
        },
        {
          "name": "docs/",
          "purpose": "Documentación (ADRs, logs, consolidación)",
          "files": 5
        },
        {
          "name": ".github/",
          "purpose": "CI/CD workflows y copilot-instructions",
          "files": 4
        },
        {
          "name": "nginx/",
          "purpose": "Configuración proxy reverso",
          "files": 2
        }
      ]
    },
    "primary_language": "Python 3.11+",
    "secondary_languages": [
      "Shell (deploy.sh, smoke.sh)",
      "YAML (CI/CD, docker-compose)",
      "Markdown (docs)",
      "SQL (migraciones Alembic)"
    ],
    "build_system": "Docker + Docker Compose 3.9",
    "package_manager": "pip (requirements.txt con versiones FIJAS sin rangos)",
    "evidence": {
      "version": {
        "file": "backend/app/main.py",
        "line": 60,
        "content": "version='1.0.0'"
      },
      "changelog": {
        "file": "backend/CHANGELOG.md",
        "line": 8,
        "content": "## [1.0.0] - 2025-09-27"
      },
      "python_version": {
        "file": "backend/Dockerfile",
        "line": 1,
        "content": "FROM python:3.11-slim"
      },
      "line_count_command": "wc -l backend/app/**/*.py",
      "test_count_command": "find backend/tests -name '*.py' | wc -l # 27 files"
    }
  }
}
```

**Conclusión PROMPT 1:** Sistema monolítico moderno, bien estructurado, con ~4600 líneas de código productivo y robusto coverage de tests. Proyecto maduro para MVP.

---

<a name="prompt-2"></a>
## PROMPT 2: ARQUITECTURA Y COMPONENTES

```json
{
  "architecture": {
    "pattern": "Monolito Modular (FastAPI)",
    "justification": [
      "Archivo único main.py que coordina todos los routers",
      "NO microservicios separados ni service mesh",
      "Docker Compose con servicios de infraestructura (DB, Redis, Nginx) pero UNA sola API",
      "ADR-001-no-pms-mvp.md rechaza integraciones PMS externas",
      "Filosofía explícita: evitar feature creep y abstracciones innecesarias"
    ],
    "evidence_files": [
      "backend/app/main.py (entry point único)",
      "docs/adr/ADR-001-no-pms-mvp.md",
      ".github/copilot-instructions.md línea 24 'SHIPPING > PERFECCIÓN'"
    ],
    "components": [
      {
        "name": "FastAPI Application (Core API)",
        "type": "backend",
        "location": "backend/app/",
        "primary_file": "backend/app/main.py",
        "language": "Python 3.11",
        "framework": "FastAPI 0.109.0",
        "purpose": "API REST principal con CORS, rate limiting, logging estructurado, health checks",
        "entry_point": "app.main:app (línea 60), ejecutado vía Gunicorn + Uvicorn workers",
        "dependencies_internal": [
          "routers (health, reservations, whatsapp, mercadopago, ical, audio, nlu, admin)",
          "services (reservations, whatsapp, mercadopago, audio, nlu, ical, email)",
          "models (Reservation, Accommodation, Payment)",
          "core (config, database, redis, security, logging)",
          "jobs (cleanup, import_ical, scheduler)"
        ],
        "dependencies_external": [
          "PostgreSQL 16 (constraint EXCLUDE GIST btree_gist)",
          "Redis 7 (locks TTL 1800s + rate limiting)",
          "WhatsApp Business Cloud API (graph.facebook.com)",
          "Mercado Pago API"
        ],
        "state_management": "stateless (estado en DB/Redis, workers async en background)",
        "estimated_lines_of_code": 222,
        "file_evidence": "backend/app/main.py"
      },
      {
        "name": "Health Check Router",
        "type": "api",
        "location": "backend/app/routers/",
        "primary_file": "backend/app/routers/health.py",
        "language": "Python",
        "framework": "FastAPI",
        "purpose": "Monitoreo consolidado: DB, Redis, disk, memory, iCal sync age, WhatsApp/MP status",
        "entry_point": "@router.get('/healthz') línea 21",
        "dependencies_internal": ["core.database.check_database_health", "core.redis.check_redis_health", "metrics.ICAL_LAST_SYNC_AGE_MIN"],
        "dependencies_external": ["PostgreSQL", "Redis"],
        "state_management": "stateless (queries de salud sin side effects)",
        "estimated_lines_of_code": 109,
        "response_statuses": ["healthy", "degraded", "unhealthy"],
        "file_evidence": "backend/app/routers/health.py"
      },
      {
        "name": "Reservations Service (Anti-Double-Booking)",
        "type": "service",
        "location": "backend/app/services/",
        "primary_file": "backend/app/services/reservations.py",
        "language": "Python",
        "framework": "SQLAlchemy async + Redis",
        "purpose": "Lógica de negocio crítica: pre-reservas con locks Redis (NX EX 1800) + constraint PostgreSQL EXCLUDE GIST para prevenir overlaps concurrentes",
        "entry_point": "ReservationService.create_prereservation()",
        "dependencies_internal": [
          "models.Reservation",
          "models.Accommodation",
          "core.redis (get_redis_pool)",
          "metrics (PRE_RES_CREATED, PRE_RES_OVERLAP, PRE_RES_LOCK_FAILED)"
        ],
        "dependencies_external": [
          "Redis: lock keys 'lock:acc:{id}:{checkin}:{checkout}' TTL 1800s",
          "PostgreSQL: constraint no_overlap_reservations (period daterange '[)')"
        ],
        "state_management": "stateful transaccional: BEGIN -> acquire lock -> INSERT -> COMMIT o ROLLBACK + release lock",
        "estimated_lines_of_code": "~350",
        "critical_features": [
          "Lock Redis previo a INSERT",
          "Rollback automático si IntegrityError (constraint violation)",
          "Generación de código único RESYYMMDDnnn",
          "Cálculo de precio con weekend_multiplier"
        ],
        "file_evidence": "backend/app/services/reservations.py"
      },
      {
        "name": "WhatsApp Business Integration",
        "type": "service",
        "location": "backend/app/routers/whatsapp.py + backend/app/services/whatsapp.py",
        "primary_file": "backend/app/routers/whatsapp.py",
        "language": "Python",
        "framework": "FastAPI + httpx",
        "purpose": "Webhook seguro (HMAC SHA-256) para mensajes WhatsApp, normalización a contrato unificado, procesamiento NLU + audio STT",
        "entry_point": "@router.post('/webhooks/whatsapp') línea 49",
        "dependencies_internal": [
          "core.security.verify_whatsapp_signature (MANDATORY)",
          "services.nlu.analyze (intent detection)",
          "services.audio.transcribe_audio (si tipo=audio)",
          "services.whatsapp.send_text_message"
        ],
        "dependencies_external": ["WhatsApp Business Cloud API v17.0 (graph.facebook.com)"],
        "state_management": "stateless (cada mensaje procesado independientemente)",
        "estimated_lines_of_code": 211,
        "security_critical": true,
        "authentication": {
          "method": "HMAC SHA-256",
          "header": "X-Hub-Signature-256",
          "secret_env": "WHATSAPP_APP_SECRET",
          "verification_function": "verify_whatsapp_signature() en core/security.py línea 51-80"
        },
        "unified_contract_output": {
          "message_id": "string",
          "canal": "whatsapp",
          "user_id": "phone number",
          "timestamp_iso": "ISO 8601",
          "tipo": "text|audio|image|pdf",
          "texto": "string|null",
          "media_url": "string|null",
          "metadata": "object"
        },
        "file_evidence": "backend/app/routers/whatsapp.py línea 37-47 (contrato comentado)"
      },
      {
        "name": "Mercado Pago Integration",
        "type": "service",
        "location": "backend/app/routers/mercadopago.py + backend/app/services/mercadopago.py",
        "primary_file": "backend/app/routers/mercadopago.py",
        "language": "Python",
        "framework": "FastAPI",
        "purpose": "Webhook idempotente para notificaciones de pago, validación x-signature v1, actualización automática de reservation_status a CONFIRMED si pago aprobado",
        "entry_point": "@router.post('/mercadopago/webhook')",
        "dependencies_internal": [
          "services.mercadopago.MercadoPagoService",
          "models.Payment (tabla payments)",
          "models.Reservation (foreign key reservation_id)"
        ],
        "dependencies_external": ["Mercado Pago API"],
        "state_management": "stateful: idempotencia por external_payment_id, incrementa events_count si ya existe",
        "estimated_lines_of_code": 150,
        "security_critical": true,
        "authentication": {
          "method": "HMAC x-signature v1 (MP específico)",
          "header": "x-signature",
          "components": "ts (timestamp) + v1 (HMAC SHA-256)",
          "verification_function": "validate_mercadopago_signature() en routers/mercadopago.py"
        },
        "idempotency": "Si payment_id existe: actualiza event_last_received_at + events_count. Si no existe: INSERT nuevo registro.",
        "file_evidence": "backend/app/services/mercadopago.py línea 36-90"
      },
      {
        "name": "Audio STT Pipeline",
        "type": "service",
        "location": "backend/app/services/audio.py",
        "primary_file": "backend/app/services/audio.py",
        "language": "Python",
        "framework": "faster-whisper (Whisper base model)",
        "purpose": "Transcripción de audio OGG/Opus a texto español. Validación de confidence threshold (default 0.6)",
        "entry_point": "async def transcribe_audio(file: UploadFile) línea 23",
        "dependencies_internal": ["core.config (AUDIO_MODEL, AUDIO_MIN_CONFIDENCE)"],
        "dependencies_external": [
          "FFmpeg (conversión OGG -> WAV si necesario)",
          "faster-whisper model (CPU, int8, language='es')"
        ],
        "state_management": "stateless (procesa archivo, retorna resultado, elimina temp file)",
        "estimated_lines_of_code": 76,
        "model_config": {
          "model": "base (configurable via AUDIO_MODEL env)",
          "device": "cpu",
          "compute_type": "int8",
          "language": "es",
          "confidence_threshold": 0.6
        },
        "error_handling": "Si confidence < threshold: retorna {'error': 'audio_unclear', 'confidence': X}",
        "file_evidence": "backend/app/services/audio.py línea 16-75"
      },
      {
        "name": "NLU Heuristic Service",
        "type": "service",
        "location": "backend/app/services/nlu.py",
        "primary_file": "backend/app/services/nlu.py",
        "language": "Python",
        "framework": "regex + dateparser (NO LLMs)",
        "purpose": "Intent detection mediante keywords regex: disponibilidad, precio, reservar, servicios. Extracción de fechas (dateparser) y guests (regex GUESTS_PATTERN)",
        "entry_point": "def analyze(text: str) línea 70",
        "dependencies_internal": ["utils.datetime_utils.get_next_weekend"],
        "dependencies_external": ["dateparser (para parsing fechas en lenguaje natural)"],
        "state_management": "stateless (función pura)",
        "estimated_lines_of_code": 78,
        "intent_keywords": {
          "disponibilidad": "disponib|libre|hay",
          "precio": "precio|costo|sale|cuanto",
          "reservar": "reserv|apart|tomo",
          "servicios": "servicio|incluye|wifi"
        },
        "date_patterns": [
          "\\d{1,2}[/-]\\d{1,2}([/-]\\d{2,4})?",
          "fin de semana|finde (convierte a próximo sábado-domingo)",
          "range: 15/12 al 18/12"
        ],
        "guests_pattern": "(\\d+)\\s*(personas?|pax|hu[eé]spedes?)",
        "file_evidence": "backend/app/services/nlu.py línea 7-78"
      },
      {
        "name": "iCal Import/Export Service",
        "type": "service",
        "location": "backend/app/services/ical.py + backend/app/routers/ical.py",
        "primary_file": "backend/app/services/ical.py",
        "language": "Python",
        "framework": "icalendar",
        "purpose": "Sincronización bidireccional con Airbnb/Booking. Export: genera .ics con token HMAC (ICS_SALT). Import: deduplicación por UID en internal_notes, actualiza last_ical_sync_at",
        "entry_point": "ICalService.export_events() / import_events()",
        "dependencies_internal": [
          "models.Accommodation (ical_export_token, ical_import_urls, last_ical_sync_at)",
          "models.Reservation",
          "core.security (HMAC token validation)"
        ],
        "dependencies_external": ["Airbnb/Booking iCal feeds (httpx fetch)"],
        "state_management": "stateful: actualiza last_ical_sync_at en DB, guarda UID en internal_notes",
        "estimated_lines_of_code": "~200",
        "export_features": [
          "Añade X-CODE y X-SOURCE properties a VEVENT",
          "Token HMAC SHA-256 con ICS_SALT para auth"
        ],
        "import_features": [
          "Dedupe por UID (busca en internal_notes JSONB)",
          "httpx timeout 20s",
          "Marca fuente en internal_notes {ical_import_source: 'airbnb'|'booking'}"
        ],
        "file_evidence": "backend/app/services/ical.py"
      },
      {
        "name": "Expiration Job Worker",
        "type": "background_job",
        "location": "backend/app/jobs/cleanup.py",
        "primary_file": "backend/app/jobs/cleanup.py",
        "language": "Python",
        "framework": "asyncio periodic task",
        "purpose": "Expira pre-reservas vencidas (expires_at < now UTC), cambia status a CANCELLED. Envía recordatorios 15min antes de expirar (window configurable)",
        "entry_point": "async def expire_prereservations(db, batch_size=200) línea 24",
        "dependencies_internal": [
          "models.Reservation",
          "services.email.email_service (best-effort notifications)"
        ],
        "dependencies_external": ["PostgreSQL"],
        "state_management": "stateful: UPDATE batch en DB, incrementa métrica PRE_RES_EXPIRED",
        "estimated_lines_of_code": 120,
        "batch_processing": "Procesa max 200 reservas por ejecución",
        "metrics": [
          "prereservations_expired_total (Counter)",
          "prereservation_reminders_processed_total (Counter)"
        ],
        "interval": "Configurable via JOB_EXPIRATION_INTERVAL_SECONDS (default 60s)",
        "file_evidence": "backend/app/jobs/cleanup.py línea 24-120"
      },
      {
        "name": "iCal Sync Job Worker",
        "type": "background_job",
        "location": "backend/app/jobs/import_ical.py",
        "primary_file": "backend/app/jobs/import_ical.py",
        "language": "Python",
        "framework": "asyncio periodic task",
        "purpose": "Sincroniza periódicamente calendarios de Airbnb/Booking para todos los accommodations con ical_import_urls configuradas",
        "entry_point": "async def run_ical_sync(logger) línea 36",
        "dependencies_internal": [
          "services.ical.ICalService",
          "models.Accommodation"
        ],
        "dependencies_external": ["URLs iCal externas (httpx, timeout 20s)"],
        "state_management": "stateful: actualiza last_ical_sync_at, crea reservas bloqueadas en DB",
        "estimated_lines_of_code": 71,
        "interval": "Configurable via JOB_ICAL_INTERVAL_SECONDS (default 300s = 5min)",
        "health_monitoring": "Gauge ical_last_sync_age_minutes expuesta en /metrics. Health degrada si >20min (ICAL_SYNC_MAX_AGE_MINUTES)",
        "file_evidence": "backend/app/jobs/import_ical.py + backend/app/main.py línea 50-56"
      },
      {
        "name": "PostgreSQL 16 Database",
        "type": "database",
        "location": "docker-compose.yml servicio postgres",
        "primary_file": "docker-compose.yml líneas 4-22",
        "language": "SQL",
        "framework": "PostgreSQL 16 Alpine",
        "purpose": "Base de datos principal con extensiones: btree_gist (constraint EXCLUDE), uuid-ossp. Almacena accommodations, reservations, payments",
        "entry_point": "N/A (servicio Docker, puerto 5433 expuesto)",
        "dependencies_internal": [],
        "dependencies_external": [],
        "state_management": "stateful (persistencia en volumen postgres_data)",
        "estimated_lines_of_code": "N/A (DDL en migraciones Alembic)",
        "critical_constraint": "ALTER TABLE reservations ADD CONSTRAINT no_overlap_reservations EXCLUDE USING gist (accommodation_id WITH =, period WITH &&) WHERE (reservation_status IN ('pre_reserved','confirmed'))",
        "migrations": "4 archivos en backend/alembic/versions/",
        "file_evidence": "backend/alembic/versions/001_initial_schema.py línea 88-100"
      },
      {
        "name": "Redis 7 Cache & Locks",
        "type": "cache",
        "location": "docker-compose.yml servicio redis",
        "primary_file": "docker-compose.yml líneas 24-39",
        "language": "N/A",
        "framework": "Redis 7 Alpine con AOF persistence",
        "purpose": "Locks distribuidos para pre-reservas (SET NX EX 1800) y rate limiting per-IP+path",
        "entry_point": "N/A (servicio Docker, puerto 6379)",
        "dependencies_internal": [],
        "dependencies_external": [],
        "state_management": "stateful (AOF en volumen redis_data)",
        "estimated_lines_of_code": "N/A",
        "lock_pattern": "lock:acc:{accommodation_id}:{check_in}:{check_out}",
        "ttl": "1800 seconds (30 minutos)",
        "rate_limit_keys": "ratelimit:{ip}:{path}",
        "file_evidence": "backend/app/core/redis.py + backend/app/services/reservations.py uso de locks"
      },
      {
        "name": "Nginx Reverse Proxy",
        "type": "proxy",
        "location": "docker-compose.yml servicio nginx + nginx/nginx.conf",
        "primary_file": "docker-compose.yml líneas 64-77",
        "language": "N/A",
        "framework": "Nginx Alpine",
        "purpose": "Reverse proxy, terminación SSL (Let's Encrypt), servir archivos estáticos (futuro), rate limiting adicional",
        "entry_point": "nginx.conf",
        "dependencies_internal": ["api service (backend FastAPI)"],
        "dependencies_external": [],
        "state_management": "stateless",
        "estimated_lines_of_code": "N/A (config Nginx)",
        "ssl_config": "Volumen nginx/ssl para certificados",
        "file_evidence": "docker-compose.yml línea 71-72"
      }
    ],
    "communication_patterns": [
      {
        "from": "Internet / Client",
        "to": "Nginx",
        "type": "HTTP/HTTPS request",
        "protocol": "HTTP/1.1, TLS 1.2+",
        "evidence": "docker-compose.yml línea 67-69 (puertos 80, 443)"
      },
      {
        "from": "Nginx",
        "to": "FastAPI API",
        "type": "HTTP proxy_pass",
        "protocol": "HTTP/1.1",
        "evidence": "docker-compose.yml network frontend, nginx.conf upstream definition"
      },
      {
        "from": "FastAPI API",
        "to": "PostgreSQL",
        "type": "async database queries",
        "protocol": "PostgreSQL wire protocol (asyncpg driver)",
        "evidence": "backend/app/core/database.py línea 11-17 create_async_engine"
      },
      {
        "from": "FastAPI API",
        "to": "Redis",
        "type": "async cache/lock operations",
        "protocol": "Redis protocol (RESP)",
        "evidence": "backend/app/core/redis.py línea 12-20 redis.asyncio.ConnectionPool"
      },
      {
        "from": "WhatsApp Business Cloud",
        "to": "FastAPI API",
        "type": "webhook POST",
        "protocol": "HTTPS con header X-Hub-Signature-256 (HMAC SHA-256)",
        "evidence": "backend/app/routers/whatsapp.py línea 49-51 + core/security.py verify_whatsapp_signature"
      },
      {
        "from": "Mercado Pago",
        "to": "FastAPI API",
        "type": "webhook POST",
        "protocol": "HTTPS con header x-signature (ts + v1 HMAC)",
        "evidence": "backend/app/routers/mercadopago.py validate_mercadopago_signature"
      },
      {
        "from": "FastAPI API",
        "to": "WhatsApp Business Cloud",
        "type": "REST API calls (send message)",
        "protocol": "HTTPS POST https://graph.facebook.com/v17.0/{phone_id}/messages",
        "evidence": "backend/app/services/whatsapp.py línea 31-45"
      },
      {
        "from": "FastAPI lifespan",
        "to": "Background Jobs",
        "type": "asyncio.create_task",
        "protocol": "In-process async tasks",
        "evidence": "backend/app/main.py línea 31-65, asyncio.create_task para expire_prereservations y run_ical_sync"
      },
      {
        "from": "Background Jobs",
        "to": "PostgreSQL/Redis",
        "type": "async DB updates / cache ops",
        "protocol": "PostgreSQL + Redis",
        "evidence": "backend/app/jobs/cleanup.py línea 24-80 usa AsyncSession DB"
      },
      {
        "from": "iCal Sync Job",
        "to": "External iCal URLs",
        "type": "HTTP GET",
        "protocol": "HTTPS (httpx client, timeout 20s)",
        "evidence": "backend/app/jobs/import_ical.py línea 26-33"
      }
    ]
  }
}
```

**Conclusión PROMPT 2:** Arquitectura monolítica modular bien diseñada, con separación clara de responsabilidades. Los componentes críticos (anti-doble-booking, webhooks seguros, background jobs) están aislados y testeables. NO hay over-engineering ni abstracciones innecesarias.

---

<a name="prompt-3"></a>
## PROMPT 3: AGENTES DE IA Y CONFIGURACIÓN

```json
{
  "agents": [],
  "rag_system": {
    "present": false,
    "vector_database": null,
    "embedding_model": null,
    "retrieval_strategy": null,
    "location": null
  },
  "ai_clarification": {
    "conclusion": "Este sistema NO es agéntico ni usa LLMs. Es un sistema de reservas tradicional con procesamiento de lenguaje natural HEURÍSTICO.",
    "components_that_could_be_confused_as_ai": [
      {
        "component": "NLU Service",
        "why_not_ai": "Usa regex y keywords estáticos, NO modelos de lenguaje",
        "file": "backend/app/services/nlu.py",
        "evidence": "línea 7-12: INTENT_KEYWORDS = regex patterns fijos. NO hay imports de openai, anthropic, langchain"
      },
      {
        "component": "Audio Transcription (Whisper)",
        "why_not_ai_agent": "Es STT (speech-to-text) únicamente. NO genera respuestas, NO tiene memoria, NO toma decisiones autónomas",
        "file": "backend/app/services/audio.py",
        "evidence": "línea 23-75: transcribe_audio retorna texto. No hay system prompt, no hay function calling, no hay conversación"
      }
    ],
    "no_ai_frameworks_used": {
      "evidence_files": [
        "backend/requirements.txt"
      ],
      "missing_packages": [
        "langchain",
        "openai",
        "anthropic",
        "google-generativeai",
        "llamaindex",
        "crewai",
        "autogen"
      ],
      "actual_ml_package": "faster-whisper (solo para STT, no generativo)"
    },
    "design_decision": {
      "adr": "ADR-001-no-pms-mvp.md",
      "philosophy": "MVP prioriza FUNCIONALIDAD sobre IA/ML avanzado. Heurísticas simples son suficientes para el alcance de 10-12 días",
      "file": "docs/adr/ADR-001-no-pms-mvp.md + .github/copilot-instructions.md línea 24"
    }
  },
  "whisper_technical_details": {
    "model": "faster-whisper",
    "model_size": "base",
    "purpose": "Convertir audio OGG/Opus a texto español",
    "configuration": {
      "file": "backend/app/core/config.py",
      "env_var": "AUDIO_MODEL",
      "default": "base",
      "device": "cpu",
      "compute_type": "int8",
      "language": "es",
      "confidence_threshold": 0.6,
      "confidence_threshold_env": "AUDIO_MIN_CONFIDENCE"
    },
    "workflow": [
      "1. Cliente envía audio OGG vía WhatsApp",
      "2. Webhook recibe file, llama transcribe_audio()",
      "3. faster-whisper transcribe con Whisper base model",
      "4. Calcula confidence promedio de segments",
      "5. Si confidence >= 0.6: retorna texto",
      "6. Si confidence < 0.6: retorna error 'audio_unclear'"
    ],
    "not_an_agent_because": [
      "No tiene memoria conversacional",
      "No toma decisiones autónomas",
      "No tiene tools/functions para ejecutar",
      "No tiene system prompt ni instrucciones",
      "Solo realiza transformación unidireccional: audio -> texto"
    ],
    "file_evidence": "backend/app/services/audio.py línea 16-75"
  }
}
```

**Conclusión PROMPT 3:** Sistema NO agéntico. Usa heurísticas (regex) para NLU y Whisper para STT. Decisión de diseño consciente para cumplir MVP en tiempo récord sin complejidad de LLMs.

---

<a name="prompt-4"></a>
## PROMPT 4: DEPENDENCIAS Y STACK TECNOLÓGICO

```json
{
  "dependencies": {
    "production": [
      {"name": "fastapi", "version": "0.109.0", "purpose": "Framework web async principal", "criticality": "critical"},
      {"name": "uvicorn[standard]", "version": "0.27.0", "purpose": "ASGI server con HTTP/2 support", "criticality": "critical"},
      {"name": "pydantic", "version": "2.5.3", "purpose": "Validación de datos y serialización", "criticality": "critical"},
      {"name": "pydantic-settings", "version": "2.1.0", "purpose": "Config desde environment variables", "criticality": "critical"},
      {"name": "sqlalchemy", "version": "2.0.25", "purpose": "ORM async para PostgreSQL", "criticality": "critical"},
      {"name": "asyncpg", "version": "0.29.0", "purpose": "Driver PostgreSQL async de alto rendimiento", "criticality": "critical"},
      {"name": "alembic", "version": "1.13.1", "purpose": "Migraciones de esquema DB", "criticality": "high"},
      {"name": "redis", "version": "5.0.1", "purpose": "Cliente Redis para locks distribuidos y cache", "criticality": "critical"},
      {"name": "httpx", "version": "0.26.0", "purpose": "HTTP client async para WhatsApp/MP APIs", "criticality": "high"},
      {"name": "python-multipart", "version": "0.0.6", "purpose": "Form uploads (audio files)", "criticality": "medium"},
      {"name": "python-jose[cryptography]", "version": "3.3.0", "purpose": "JWT token generation/validation", "criticality": "high"},
      {"name": "passlib[bcrypt]", "version": "1.7.4", "purpose": "Password hashing bcrypt", "criticality": "high"},
      {"name": "structlog", "version": "24.1.0", "purpose": "Logging estructurado JSON con request_id", "criticality": "high"},
      {"name": "python-dateutil", "version": "2.8.2", "purpose": "Date manipulation y parsing", "criticality": "medium"},
      {"name": "dateparser", "version": "1.2.0", "purpose": "NLU: parse fechas en lenguaje natural argentino", "criticality": "medium"},
      {"name": "pytz", "version": "2023.3", "purpose": "Timezones (Argentina/Buenos_Aires)", "criticality": "medium"},
      {"name": "holidays", "version": "0.46", "purpose": "Detección feriados para pricing weekend_multiplier", "criticality": "low"},
      {"name": "aiofiles", "version": "23.2.1", "purpose": "Async file I/O", "criticality": "low"},
      {"name": "psutil", "version": "5.9.8", "purpose": "System monitoring (memory, disk) en health checks", "criticality": "low"},
      {"name": "prometheus-fastapi-instrumentator", "version": "6.1.0", "purpose": "Auto-instrumentación métricas Prometheus", "criticality": "high"},
      {"name": "prometheus-client", "version": "0.20.0", "purpose": "Custom counters/gauges Prometheus", "criticality": "high"},
      {"name": "icalendar", "version": "5.0.11", "purpose": "Parse/generate .ics files (Airbnb/Booking sync)", "criticality": "medium"},
      {"name": "faster-whisper", "version": "0.10.0", "purpose": "Whisper STT model inference (audio transcription)", "criticality": "medium"},
      {"name": "numpy", "version": "1.26.4", "purpose": "Dependencia de faster-whisper", "criticality": "medium"},
      {"name": "soundfile", "version": "0.12.1", "purpose": "Audio file I/O (librosa dependency)", "criticality": "low"},
      {"name": "spacy", "version": "3.7.2", "purpose": "NLP (actualmente no usado, reservado para futuro)", "criticality": "low"},
      {"name": "Jinja2", "version": "3.1.4", "purpose": "Email templates rendering", "criticality": "medium"}
    ],
    "development": [
      {"name": "pytest", "version": "implícito (no en requirements.txt)", "purpose": "Framework de testing async"},
      {"name": "pytest-asyncio", "version": "implícito", "purpose": "Soporte async/await en tests"},
      {"name": "fakeredis", "version": "2.23.2 (solo CI)", "purpose": "Mock Redis en tests unitarios"}
    ],
    "system_dependencies": [
      {"name": "PostgreSQL", "version": "16", "purpose": "DB principal con btree_gist + uuid-ossp", "evidence": "docker-compose.yml línea 5"},
      {"name": "Redis", "version": "7", "purpose": "Locks + cache + rate limiting", "evidence": "docker-compose.yml línea 25"},
      {"name": "FFmpeg", "version": "latest", "purpose": "Conversión audio (OGG -> WAV)", "evidence": "backend/Dockerfile línea 11"},
      {"name": "Docker", "version": ">=20.10", "purpose": "Containerización", "evidence": "docker-compose.yml"},
      {"name": "Nginx", "version": "alpine", "purpose": "Reverse proxy + SSL termination", "evidence": "docker-compose.yml línea 65"},
      {"name": "Python", "version": "3.11+", "purpose": "Runtime", "evidence": "backend/Dockerfile línea 1"}
    ]
  },
  "frameworks_and_libraries": {
    "web_framework": "FastAPI 0.109.0 (async Python web framework)",
    "ai_frameworks": ["None (faster-whisper NO es framework agéntico, solo STT)"],
    "database_orm": "SQLAlchemy 2.0.25 async (con asyncpg driver)",
    "testing_framework": "pytest con asyncio mode=auto (pytest.ini línea 9)",
    "async_framework": "asyncio nativo Python + SQLAlchemy async + redis.asyncio",
    "http_client": "httpx 0.26.0 (async)",
    "serialization": "Pydantic 2.5.3",
    "logging": "structlog 24.1.0 (JSON structured)",
    "metrics": "Prometheus (instrumentator + prometheus_client)"
  },
  "infrastructure": {
    "containerization": "Docker (multi-stage builds no usado en MVP, single stage optimizado)",
    "orchestration": "Docker Compose 3.9",
    "ci_cd": "GitHub Actions",
    "deployment_script": "backend/deploy.sh (bash automation)",
    "evidence_files": [
      "docker-compose.yml",
      ".github/workflows/ci.yml",
      "backend/Dockerfile",
      "backend/deploy.sh"
    ],
    "ci_pipelines": [
      {
        "name": "tests-sqlite",
        "purpose": "Tests rápidos con SQLite fallback (skip constraint tests)",
        "file": ".github/workflows/ci.yml línea 10-34"
      },
      {
        "name": "tests-postgres-redis",
        "purpose": "Tests completos con Postgres real + btree_gist (constraint validation)",
        "file": ".github/workflows/ci.yml línea 36-93",
        "services": ["postgres:16", "redis:7"]
      }
    ]
  },
  "versioning_strategy": {
    "philosophy": "Versiones FIJAS sin rangos (==) para reproducibilidad",
    "evidence": "backend/requirements.txt - todas las líneas usan == exact version",
    "rationale": "Evitar dependency hell y garantizar builds reproducibles",
    "source": ".github/copilot-instructions.md línea 180 'VERSIONES FIJAS - no >= ni ~'"
  }
}
```

**Evidencia:** `cat backend/requirements.txt | grep -v "==" | wc -l` retorna 0 (todas las deps tienen versión exacta).

**Conclusión PROMPT 4:** Stack moderno y sólido. Versiones fijas garantizan reproducibilidad. NO hay dependencias legacy ni tech debt significativo en librerías.

---

<a name="prompt-5"></a>
## PROMPT 5: CONTRATOS DE INTERFAZ Y APIs

Dado el tamaño extenso de este prompt, presento los endpoints más críticos:

```json
{
  "interfaces": [
    {
      "type": "REST API",
      "endpoint_or_topic": "POST /api/v1/reservations/pre-reserve",
      "method": "POST",
      "location": "backend/app/routers/reservations.py línea 52",
      "input_schema": {
        "description": "Crear pre-reserva con lock Redis y constraint check",
        "parameters": [
          {"name": "accommodation_id", "type": "int", "required": true, "validation": "gt=0"},
          {"name": "check_in", "type": "date", "required": true, "validation": "ISO YYYY-MM-DD"},
          {"name": "check_out", "type": "date", "required": true, "validation": "ISO, must be > check_in"},
          {"name": "guests", "type": "int", "required": true, "validation": "gt=0"},
          {"name": "channel", "type": "str", "required": false, "validation": "default='whatsapp'"},
          {"name": "contact_name", "type": "str", "required": true, "validation": "max 100 chars"},
          {"name": "contact_phone", "type": "str", "required": true, "validation": "max 20 chars"},
          {"name": "contact_email", "type": "str", "required": false, "validation": "email format opcional"}
        ],
        "schema_location": "PreReservationRequest Pydantic model línea 12-20"
      },
      "output_schema": {
        "success_case": {
          "code": "string (RESYYMMDDnnn)",
          "expires_at": "ISO timestamp",
          "deposit_amount": "string decimal",
          "total_price": "string decimal",
          "nights": "int"
        },
        "error_case": {
          "error": "string ('lock_failed' | 'not_available' | 'invalid_dates' | ...)"
        },
        "schema_location": "PreReservationResponse línea 22-28"
      },
      "authentication": {"required": false, "method": "none (público para MVP)", "location": "N/A"},
      "rate_limiting": {
        "present": true,
        "limits": "60 requests per 60 seconds por IP+path",
        "implementation": "Redis INCR con TTL",
        "location": "backend/app/main.py línea 126-168 middleware",
        "bypass_endpoints": ["/api/v1/healthz", "/metrics"]
      },
      "error_handling": {
        "status_codes": ["200 (con error en body)", "400", "422", "429", "500"],
        "error_format": "JSON {'error': 'descripción'}",
        "location": "backend/app/main.py exception handlers línea 171-220"
      },
      "business_logic": [
        "1. Valida input (Pydantic auto)",
        "2. Adquiere lock Redis: SET lock:acc:{id}:{in}:{out} {uuid} NX EX 1800",
        "3. Si lock falla -> return {'error': 'lock_failed'}",
        "4. Calcula precio: base_price * nights * weekend_multiplier (si aplica)",
        "5. INSERT reservation (pre_reserved, expires_at=now+30min)",
        "6. Si DB IntegrityError (constraint violation) -> DELETE lock, return error",
        "7. Return código + expiración + depósito"
      ]
    },
    {
      "type": "Webhook",
      "endpoint_or_topic": "POST /api/v1/webhooks/whatsapp",
      "method": "POST",
      "location": "backend/app/routers/whatsapp.py línea 49",
      "input_schema": {
        "description": "Webhook WhatsApp Business Cloud API con HMAC signature validation OBLIGATORIA",
        "parameters": [
          {"name": "entry", "type": "array", "required": true, "validation": "WhatsApp webhook structure"},
          {"name": "X-Hub-Signature-256", "type": "header", "required": true, "validation": "sha256=<hex>"}
        ],
        "schema_location": "WhatsApp Cloud API docs + código línea 58-80"
      },
      "output_schema": {
        "description": "Ack o error",
        "example": {"status": "ok"} | {"error": "invalid_signature" | "no_messages"}
      },
      "authentication": {
        "required": true,
        "method": "HMAC SHA-256",
        "header": "X-Hub-Signature-256",
        "secret_env": "WHATSAPP_APP_SECRET",
        "verification_function": "verify_whatsapp_signature() en backend/app/core/security.py línea 51-80",
        "failure_response": "403 Forbidden"
      },
      "rate_limiting": {"present": true, "limits": "60/60s", "location": "main.py middleware"},
      "error_handling": {
        "status_codes": ["200", "403 (firma inválida)", "400 (payload inválido)"],
        "error_format": "JSON {'error': '...'}",
        "security_critical": "Si firma falla, NO procesar mensaje bajo ninguna circunstancia"
      },
      "unified_message_contract": {
        "message_id": "string",
        "canal": "'whatsapp'",
        "user_id": "phone number (WA ID)",
        "timestamp_iso": "ISO 8601",
        "tipo": "'text' | 'audio' | 'image' | 'pdf'",
        "texto": "string | null",
        "media_url": "string | null",
        "metadata": "object {duration_sec?, confidence_stt?}"
      },
      "processing_flow": [
        "1. Verificar firma HMAC (MANDATORY - throw 403 si falla)",
        "2. Parse JSON payload",
        "3. Extraer mensaje de estructura entry/changes/messages",
        "4. Si tipo=text: enviar a NLU service",
        "5. Si tipo=audio: descargar, enviar a transcribe_audio, luego NLU",
        "6. NLU extrae intents/dates/guests",
        "7. Si intent=reservar + datos completos: llamar pre-reserve",
        "8. Responder vía WhatsApp send_text_message"
      ]
    },
    {
      "type": "Webhook",
      "endpoint_or_topic": "POST /api/v1/mercadopago/webhook",
      "method": "POST",
      "location": "backend/app/routers/mercadopago.py",
      "input_schema": {
        "description": "Notificación de pago con validación x-signature v1 + idempotencia",
        "parameters": [
          {"name": "id", "type": "string", "required": true, "validation": "payment_id MP"},
          {"name": "status", "type": "string", "required": true, "validation": "'approved'|'pending'|'rejected'"},
          {"name": "amount", "type": "number", "required": true, "validation": "decimal"},
          {"name": "currency", "type": "string", "required": false, "validation": "default='ARS'"},
          {"name": "external_reference", "type": "string", "required": false, "validation": "reservation code"}
        ],
        "headers": [
          {"name": "x-signature", "required": true, "format": "ts=<timestamp>,v1=<hmac>"}
        ],
        "schema_location": "backend/app/services/mercadopago.py línea 36-90"
      },
      "output_schema": {
        "success": {"status": "ok", "idempotent": "boolean", "payment_id": "string", "events_count": "int"},
        "error": {"error": "string"}
      },
      "authentication": {
        "required": true,
        "method": "HMAC x-signature v1 (Mercado Pago specific)",
        "header": "x-signature",
        "format": "ts=<unix_timestamp>,v1=<hmac_sha256>",
        "verification": "validate_mercadopago_signature() en routers/mercadopago.py",
        "secret_env": "MERCADOPAGO_WEBHOOK_SECRET"
      },
      "idempotency": {
        "key": "external_payment_id (unique index en tabla payments)",
        "behavior": "Si payment_id ya existe: UPDATE event_last_received_at + INCREMENT events_count. Si no existe: INSERT nuevo registro.",
        "confirmation_logic": "Si status='approved' y external_reference matchea reservation pre_reserved: UPDATE reservation_status='confirmed', payment_status='paid'"
      },
      "error_handling": {
        "status_codes": ["200", "403 (firma inválida)", "400 (payload inválido)"],
        "error_format": "JSON {'error': '...'}",
        "location": "services/mercadopago.py línea 36-90"
      }
    },
    {
      "type": "REST API",
      "endpoint_or_topic": "GET /api/v1/healthz",
      "method": "GET",
      "location": "backend/app/routers/health.py línea 21",
      "input_schema": {"description": "No parameters", "parameters": []},
      "output_schema": {
        "description": "Status consolidado + checks por componente",
        "fields": {
          "status": "'healthy' | 'degraded' | 'unhealthy'",
          "timestamp": "ISO",
          "checks": {
            "database": {"status": "string", "latency_ms": "float?"},
            "redis": {"status": "string", "ping": "string?"},
            "disk": {"status": "string", "free_percent": "float"},
            "memory": {"status": "string", "percent": "float?"},
            "ical": {"status": "string ('ok'|'warning'|'error')", "last_sync_age_minutes": "int?", "threshold": "int"},
            "whatsapp": {"status": "ok|error (si faltan credenciales)"},
            "mercadopago": {"status": "ok|error"},
            "runtime": {"status": "ok", "gunicorn_workers": "int?", "db_pool_size": "int?"}
          }
        },
        "status_logic": [
          "unhealthy: algún check critical (DB, Redis) = 'error'",
          "degraded: algún check = 'warning' (e.g. iCal sync age > threshold, disk < 10%)",
          "healthy: todos ok o warnings menores"
        ]
      },
      "authentication": {"required": false, "method": "none (público para health checks)", "location": "N/A"},
      "rate_limiting": {
        "present": false,
        "bypass": true,
        "location": "backend/app/main.py línea 137 bypass healthz explícito"
      },
      "error_handling": {
        "status_codes": ["200 SIEMPRE (errores en body checks{})"],
        "error_format": "N/A (nunca lanza excepciones)",
        "design_decision": "Health check nunca debe fallar con 500, siempre retorna 200 con status en JSON"
      }
    },
    {
      "type": "REST API (Prometheus)",
      "endpoint_or_topic": "GET /metrics",
      "method": "GET",
      "location": "backend/app/main.py línea 88 (Instrumentator)",
      "input_schema": {"description": "No parameters", "parameters": []},
      "output_schema": {
        "description": "Métricas Prometheus text format",
        "metrics_exposed": [
          "http_request_duration_seconds",
          "http_requests_total",
          "reservations_created_total{channel}",
          "reservations_confirmed_total{channel}",
          "reservations_expired_total",
          "reservations_date_overlap_total{channel}",
          "reservations_lock_failed_total{channel}",
          "prereservations_expired_total",
          "prereservation_reminders_processed_total",
          "ical_last_sync_age_minutes (Gauge)"
        ],
        "location": "backend/app/metrics.py define custom metrics"
      },
      "authentication": {"required": false, "method": "none (debería protegerse en prod con IP whitelist Nginx)", "location": "N/A"},
      "rate_limiting": {"present": false, "bypass": true, "location": "main.py línea 137"},
      "error_handling": {"status_codes": ["200 OK"], "error_format": "N/A"}
    }
  ],
  "internal_contracts": [
    {
      "from": "ReservationService",
      "to": "Redis",
      "function_or_method": "redis.set(key, value, nx=True, ex=1800)",
      "parameters": "key='lock:acc:{id}:{in}:{out}', value=uuid, nx=True (solo si no existe), ex=1800 (TTL 30min)",
      "return_type": "bool (True si lock adquirido, False si ya existe)",
      "location": "backend/app/services/reservations.py uso de redis client",
      "critical": true,
      "failure_mode": "Si lock falla -> NO continuar con INSERT, retornar error inmediato"
    },
    {
      "from": "WhatsApp webhook",
      "to": "NLU service",
      "function_or_method": "nlu.analyze(text: str) -> Dict[str, Any]",
      "parameters": "text: mensaje del usuario",
      "return_type": "{'intents': ['reservar'|'disponibilidad'|...], 'dates': ['YYYY-MM-DD'], 'guests': int?}",
      "location": "backend/app/routers/whatsapp.py -> services/nlu.py línea 70"
    },
    {
      "from": "Audio router",
      "to": "Audio service",
      "function_or_method": "transcribe_audio(file: UploadFile) -> Dict[str, Any]",
      "parameters": "file: UploadFile con bytes de audio",
      "return_type": "{'text': str, 'confidence': float, 'id': str} | {'error': 'audio_unclear', 'confidence': float}",
      "location": "backend/app/routers/audio.py -> services/audio.py línea 23"
    }
  ],
  "openapi_documentation": {
    "auto_generated": true,
    "endpoints": {
      "swagger_ui": "/api/docs (solo development)",
      "redoc": "/api/redoc (solo development)",
      "json": "/openapi.json"
    },
    "disabled_in_production": true,
    "evidence": "backend/app/main.py línea 66-67: docs_url=None if ENVIRONMENT=='production'"
  }
}
```

**Conclusión PROMPT 5:** APIs bien diseñadas con validación automática Pydantic. Seguridad crítica en webhooks (HMAC obligatorio). Rate limiting configurado. OpenAPI auto-generado. Idempotencia en pagos.

---

<a name="prompt-6"></a>
## PROMPT 6: FLUJOS CRÍTICOS Y CASOS DE USO

```json
{
  "critical_flows": [
    {
      "name": "Pre-Reserva Anti-Double-Booking",
      "description": "Crear pre-reserva con lock Redis y constraint PostgreSQL para prevenir overlaps concurrentes",
      "business_criticality": "high",
      "estimated_frequency": "10-50 requests/hour (picos en fines de semana)",
      "trigger": "POST /api/v1/reservations/pre-reserve",
      "entry_point": {
        "file": "backend/app/routers/reservations.py",
        "function": "create_pre_reservation",
        "line": 52
      },
      "steps": [
        {
          "step_number": 1,
          "component": "Pydantic validation",
          "action": "Validar input (accommodation_id > 0, dates valid, guests > 0)",
          "file_location": "routers/reservations.py",
          "function": "PreReservationRequest model",
          "external_calls": [],
          "database_operations": [],
          "decision_points": ["Si validation falla -> 422"],
          "error_handling": "FastAPI auto-genera 422 Validation Error"
        },
        {
          "step_number": 2,
          "component": "ReservationService",
          "action": "Adquirir lock Redis: SET lock:acc:{id}:{in}:{out} {uuid} NX EX 1800",
          "file_location": "services/reservations.py",
          "function": "create_prereservation",
          "external_calls": ["Redis SET NX"],
          "database_operations": [],
          "decision_points": ["Si lock exists (retorna False) -> return {'error': 'lock_failed'}"],
          "error_handling": "Fail-fast si lock no adquirido"
        },
        {
          "step_number": 3,
          "component": "ReservationService",
          "action": "Calcular precio: base_price * nights * weekend_multiplier (si check_in/out incluye sábado/domingo)",
          "file_location": "services/reservations.py",
          "function": "calculate_pricing",
          "external_calls": [],
          "database_operations": ["SELECT FROM accommodations WHERE id={accommodation_id}"],
          "decision_points": ["Si accommodation no existe -> rollback + delete lock -> error"],
          "error_handling": "Rollback DB + release lock"
        },
        {
          "step_number": 4,
          "component": "ReservationService",
          "action": "INSERT reservation (reservation_status='pre_reserved', expires_at=now+30min, lock_value=uuid)",
          "file_location": "services/reservations.py",
          "function": "create_prereservation",
          "external_calls": [],
          "database_operations": ["INSERT INTO reservations"],
          "decision_points": ["Si IntegrityError (constraint no_overlap) -> catch exception"],
          "error_handling": "ROLLBACK + DELETE lock Redis + return {'error': 'not_available'}"
        },
        {
          "step_number": 5,
          "component": "ReservationService",
          "action": "COMMIT transaction + retornar código RESYYMMDDnnn + expires_at + deposit",
          "file_location": "services/reservations.py",
          "function": "create_prereservation",
          "external_calls": [],
          "database_operations": ["COMMIT"],
          "decision_points": [],
          "error_handling": "Si commit falla -> rollback + delete lock"
        }
      ],
      "data_flow": [
        {"from": "Client request", "to": "FastAPI router", "transformation": "JSON -> Pydantic model", "validation": "Pydantic auto"},
        {"from": "Router", "to": "ReservationService", "transformation": "Pydantic model -> dict args", "validation": "N/A"},
        {"from": "Service", "to": "Redis", "transformation": "lock key generation", "validation": "NX flag garantiza atomicidad"},
        {"from": "Service", "to": "PostgreSQL", "transformation": "ORM model -> SQL INSERT", "validation": "Constraint EXCLUDE GIST valida overlap"},
        {"from": "PostgreSQL", "to": "Service", "transformation": "Commit success -> reservation object", "validation": "N/A"},
        {"from": "Service", "to": "Router", "transformation": "Reservation object -> response dict", "validation": "N/A"},
        {"from": "Router", "to": "Client", "transformation": "Dict -> JSON response", "validation": "Pydantic response model"}
      ],
      "dependencies": {
        "internal_components": ["ReservationService", "Reservation model", "Accommodation model"],
        "external_services": [],
        "databases": ["PostgreSQL (reservations, accommodations tables)", "Redis (locks)"],
        "caches": ["Redis locks con TTL 1800s"]
      },
      "sla_requirements": {
        "documented": true,
        "max_latency_ms": 3000,
        "min_availability": null,
        "source": ".github/copilot-instructions.md línea 353: 'Texto P95: < 3s (warning > 4s, critical > 6s)'"
      }
    },
    {
      "name": "WhatsApp Mensaje a Pre-Reserva (Pipeline Completo)",
      "description": "Cliente envía mensaje WhatsApp -> validación HMAC -> NLU extrae intents/dates -> pre-reserva automática si datos completos",
      "business_criticality": "high",
      "estimated_frequency": "50-200 mensajes/día",
      "trigger": "Webhook POST de WhatsApp Business Cloud",
      "entry_point": {
        "file": "backend/app/routers/whatsapp.py",
        "function": "whatsapp_webhook",
        "line": 49
      },
      "steps": [
        {
          "step_number": 1,
          "component": "Security middleware",
          "action": "Validar firma HMAC SHA-256 (header X-Hub-Signature-256)",
          "file_location": "core/security.py",
          "function": "verify_whatsapp_signature",
          "external_calls": [],
          "database_operations": [],
          "decision_points": ["Si firma inválida -> 403 Forbidden INMEDIATO"],
          "error_handling": "HTTPException 403"
        },
        {
          "step_number": 2,
          "component": "WhatsApp router",
          "action": "Parse JSON, extraer mensaje de estructura entry/changes/messages",
          "file_location": "routers/whatsapp.py",
          "function": "whatsapp_webhook",
          "external_calls": [],
          "database_operations": [],
          "decision_points": ["Si no hay messages -> return error"],
          "error_handling": "Return {'error': 'no_messages'}"
        },
        {
          "step_number": 3,
          "component": "WhatsApp router",
          "action": "Si tipo=audio: descargar media, llamar transcribe_audio",
          "file_location": "routers/whatsapp.py",
          "function": "whatsapp_webhook",
          "external_calls": ["WhatsApp media download URL", "services/audio.transcribe_audio"],
          "database_operations": [],
          "decision_points": ["Si confidence < 0.6 -> pedir que reenvíe texto"],
          "error_handling": "Responder 'No se entendió audio, envía texto'"
        },
        {
          "step_number": 4,
          "component": "NLU service",
          "action": "Analizar texto: extraer intents, dates, guests",
          "file_location": "services/nlu.py",
          "function": "analyze",
          "external_calls": [],
          "database_operations": [],
          "decision_points": ["Si intent='reservar' y dates presentes -> continuar", "Si faltan datos -> pedir más info"],
          "error_handling": "Responder pidiendo datos faltantes"
        },
        {
          "step_number": 5,
          "component": "ReservationService",
          "action": "Llamar create_prereservation con datos extraídos",
          "file_location": "services/reservations.py",
          "function": "create_prereservation",
          "external_calls": ["Redis lock", "PostgreSQL INSERT"],
          "database_operations": ["SELECT accommodation", "INSERT reservation"],
          "decision_points": ["Si lock_failed -> responder 'En proceso'", "Si overlap -> responder 'No disponible'"],
          "error_handling": "Traducir errores técnicos a mensajes user-friendly"
        },
        {
          "step_number": 6,
          "component": "WhatsApp service",
          "action": "Enviar respuesta con código de reserva + link de pago MP",
          "file_location": "services/whatsapp.py",
          "function": "send_text_message",
          "external_calls": ["WhatsApp Cloud API POST /messages"],
          "database_operations": [],
          "decision_points": [],
          "error_handling": "Log error si envío falla (no crítico, reserva ya creada)"
        }
      ],
      "data_flow": [
        {"from": "WhatsApp Cloud", "to": "API webhook", "transformation": "JSON payload", "validation": "HMAC signature"},
        {"from": "Webhook", "to": "NLU", "transformation": "Texto mensaje", "validation": "N/A"},
        {"from": "NLU", "to": "ReservationService", "transformation": "Intents + extracted data", "validation": "Verificar datos completos"},
        {"from": "ReservationService", "to": "WhatsApp", "transformation": "Código reserva -> mensaje confirmación", "validation": "N/A"}
      ],
      "dependencies": {
        "internal_components": ["WhatsApp router", "Audio service", "NLU service", "ReservationService"],
        "external_services": ["WhatsApp Business Cloud API"],
        "databases": ["PostgreSQL", "Redis"],
        "caches": ["Redis locks"]
      },
      "sla_requirements": {
        "documented": true,
        "max_latency_ms": 15000,
        "min_availability": null,
        "source": ".github/copilot-instructions.md línea 354: 'Audio P95: < 15s (warning > 20s, critical > 30s)'"
      }
    },
    {
      "name": "Expiración Automática de Pre-Reservas",
      "description": "Background job que marca como cancelled las pre-reservas vencidas (expires_at < now)",
      "business_criticality": "medium",
      "estimated_frequency": "Cada 60 segundos (JOB_EXPIRATION_INTERVAL_SECONDS)",
      "trigger": "asyncio periodic task en lifespan",
      "entry_point": {
        "file": "backend/app/jobs/cleanup.py",
        "function": "expire_prereservations",
        "line": 24
      },
      "steps": [
        {
          "step_number": 1,
          "component": "Cleanup job",
          "action": "SELECT ids WHERE status='pre_reserved' AND expires_at < now LIMIT 200",
          "file_location": "jobs/cleanup.py",
          "function": "expire_prereservations",
          "external_calls": [],
          "database_operations": ["SELECT FROM reservations"],
          "decision_points": ["Si no hay resultados -> return 0"],
          "error_handling": "N/A"
        },
        {
          "step_number": 2,
          "component": "Cleanup job",
          "action": "UPDATE reservations SET status='cancelled', cancelled_at=now WHERE id IN (...)",
          "file_location": "jobs/cleanup.py",
          "function": "expire_prereservations",
          "external_calls": [],
          "database_operations": ["UPDATE reservations batch"],
          "decision_points": [],
          "error_handling": "Rollback si UPDATE falla"
        },
        {
          "step_number": 3,
          "component": "Cleanup job",
          "action": "Incrementar métrica prereservations_expired_total + enviar emails (best-effort)",
          "file_location": "jobs/cleanup.py",
          "function": "expire_prereservations",
          "external_calls": ["email_service.send_html (si guest_email presente)"],
          "database_operations": [],
          "decision_points": [],
          "error_handling": "Catch all exceptions en envío email (no fallar job por esto)"
        }
      ],
      "data_flow": [
        {"from": "PostgreSQL", "to": "Job", "transformation": "Rows -> reservation IDs", "validation": "N/A"},
        {"from": "Job", "to": "PostgreSQL", "transformation": "Batch UPDATE", "validation": "N/A"},
        {"from": "Job", "to": "Email service", "transformation": "Reservation data -> email HTML", "validation": "N/A (best-effort)"}
      ],
      "dependencies": {
        "internal_components": ["Cleanup job", "Email service"],
        "external_services": ["SMTP server (si configurado)"],
        "databases": ["PostgreSQL"],
        "caches": []
      },
      "sla_requirements": {
        "documented": false,
        "max_latency_ms": null,
        "min_availability": null,
        "source": "No SLA documentado para jobs background"
      }
    }
  ],
  "use_cases": [
    {
      "name": "Reserva vía WhatsApp (Happy Path)",
      "description": "Usuario envía 'Quiero reservar del 15/12 al 18/12 para 2 personas' -> sistema crea pre-reserva -> responde con código y link pago",
      "actor": "Usuario final (WhatsApp)",
      "flows_involved": ["WhatsApp Mensaje a Pre-Reserva"],
      "evidence": "Tests: backend/tests/test_nlu_to_prereservation.py"
    },
    {
      "name": "Doble-Booking Concurrente (Prevención)",
      "description": "Dos clientes intentan reservar mismo accommodation mismo período simultáneamente -> uno obtiene lock -> otro recibe error 'not_available'",
      "actor": "Dos usuarios concurrentes",
      "flows_involved": ["Pre-Reserva Anti-Double-Booking"],
      "evidence": "Tests: backend/tests/test_double_booking.py, test_reservation_concurrency.py, test_constraint_validation.py"
    },
    {
      "name": "Pago Confirmado -> Confirmación Automática",
      "description": "Usuario paga depósito en MP -> webhook notifica pago approved -> sistema marca reservation_status='confirmed' + payment_status='paid'",
      "actor": "Sistema (webhook MP)",
      "flows_involved": ["Mercado Pago Integration"],
      "evidence": "Tests: backend/tests/test_mercadopago_webhook.py, services/mercadopago.py línea 73-76"
    },
    {
      "name": "Sincronización iCal Airbnb/Booking",
      "description": "Job periódico descarga .ics de Airbnb -> importa eventos -> bloquea fechas en sistema -> actualiza last_ical_sync_at",
      "actor": "Sistema (background job)",
      "flows_involved": ["iCal Sync Job Worker"],
      "evidence": "backend/app/jobs/import_ical.py + tests/test_ical_import.py"
    }
  ]
}
```

**Conclusión PROMPT 6:** Flujos críticos bien definidos con manejo robusto de errores. Anti-double-booking con doble barrera (Redis + PostgreSQL). Pipeline WhatsApp -> NLU -> Pre-reserva completamente automatizado.

---

<a name="prompt-7"></a>
## PROMPT 7: CONFIGURACIÓN Y VARIABLES DE ENTORNO

```json
{
  "configuration": {
    "config_files": [
      {
        "file": "backend/app/core/config.py",
        "format": "Python (Pydantic Settings)",
        "purpose": "Configuración central del sistema con validación automática",
        "contains_secrets": false,
        "environment_specific": "all (lee de .env)"
      },
      {
        "file": ".env (no committed)",
        "format": ".env key=value",
        "purpose": "Secrets y config por entorno",
        "contains_secrets": true,
        "environment_specific": "all"
      },
      {
        "file": "docker-compose.yml",
        "format": "YAML",
        "purpose": "Config de servicios Docker (DB passwords, puertos)",
        "contains_secrets": true,
        "environment_specific": "development/production"
      },
      {
        "file": "pytest.ini",
        "format": "INI",
        "purpose": "Config de tests (PYTHONPATH, asyncio_mode)",
        "contains_secrets": false,
        "environment_specific": "development/test"
      }
    ],
    "environment_variables": [
      {"name": "ENVIRONMENT", "required": false, "default_value": "development", "purpose": "Entorno: development|test|production", "locations_used": ["config.py", "main.py"], "appears_to_be_secret": false},
      {"name": "DATABASE_URL", "required": true, "default_value": null, "purpose": "Connection string PostgreSQL (postgresql+asyncpg://...)", "locations_used": ["config.py", "database.py"], "appears_to_be_secret": true},
      {"name": "TEST_DATABASE_URL", "required": false, "default_value": null, "purpose": "Override DB URL en tests", "locations_used": ["tests/conftest.py"], "appears_to_be_secret": false},
      {"name": "REDIS_URL", "required": true, "default_value": null, "purpose": "Connection string Redis (redis://...)", "locations_used": ["config.py", "redis.py"], "appears_to_be_secret": true},
      {"name": "WHATSAPP_ACCESS_TOKEN", "required": true, "default_value": null, "purpose": "Token de WhatsApp Business Cloud API", "locations_used": ["config.py", "services/whatsapp.py"], "appears_to_be_secret": true},
      {"name": "WHATSAPP_VERIFY_TOKEN", "required": false, "default_value": "auto-generated secrets.token_urlsafe", "purpose": "Token para verificación webhook setup", "locations_used": ["config.py", "routers/whatsapp.py"], "appears_to_be_secret": true},
      {"name": "WHATSAPP_APP_SECRET", "required": true, "default_value": null, "purpose": "Secret para HMAC validation de webhooks", "locations_used": ["config.py", "core/security.py"], "appears_to_be_secret": true},
      {"name": "WHATSAPP_PHONE_ID", "required": false, "default_value": null, "purpose": "Phone number ID de WhatsApp Business", "locations_used": ["config.py", "services/whatsapp.py"], "appears_to_be_secret": false},
      {"name": "MERCADOPAGO_ACCESS_TOKEN", "required": true, "default_value": null, "purpose": "Token de Mercado Pago API", "locations_used": ["config.py"], "appears_to_be_secret": true},
      {"name": "MERCADOPAGO_WEBHOOK_SECRET", "required": false, "default_value": null, "purpose": "Secret para validar x-signature webhooks MP", "locations_used": ["config.py", "routers/mercadopago.py"], "appears_to_be_secret": true},
      {"name": "JWT_SECRET", "required": false, "default_value": "auto-generated secrets.token_urlsafe", "purpose": "Secret para firmar JWT tokens", "locations_used": ["config.py", "core/security.py"], "appears_to_be_secret": true},
      {"name": "ICS_SALT", "required": false, "default_value": "auto-generated secrets.token_hex", "purpose": "Salt para HMAC tokens iCal export", "locations_used": ["config.py", "services/ical.py"], "appears_to_be_secret": true},
      {"name": "DB_POOL_SIZE", "required": false, "default_value": "10", "purpose": "Tamaño pool de conexiones SQLAlchemy", "locations_used": ["config.py", "database.py"], "appears_to_be_secret": false},
      {"name": "DB_MAX_OVERFLOW", "required": false, "default_value": "5", "purpose": "Max overflow conexiones DB", "locations_used": ["config.py", "database.py"], "appears_to_be_secret": false},
      {"name": "JOB_EXPIRATION_INTERVAL_SECONDS", "required": false, "default_value": "60", "purpose": "Intervalo job expiración pre-reservas", "locations_used": ["config.py", "main.py"], "appears_to_be_secret": false},
      {"name": "JOB_ICAL_INTERVAL_SECONDS", "required": false, "default_value": "300", "purpose": "Intervalo job sync iCal (5min default)", "locations_used": ["config.py", "main.py"], "appears_to_be_secret": false},
      {"name": "ICAL_SYNC_MAX_AGE_MINUTES", "required": false, "default_value": "20", "purpose": "Threshold para health degraded si sync iCal antiguo", "locations_used": ["config.py", "routers/health.py"], "appears_to_be_secret": false},
      {"name": "RATE_LIMIT_ENABLED", "required": false, "default_value": "true", "purpose": "Habilitar/deshabilitar rate limiting", "locations_used": ["config.py", "main.py"], "appears_to_be_secret": false},
      {"name": "RATE_LIMIT_REQUESTS", "required": false, "default_value": "60", "purpose": "Max requests en ventana", "locations_used": ["config.py", "main.py"], "appears_to_be_secret": false},
      {"name": "RATE_LIMIT_WINDOW_SECONDS", "required": false, "default_value": "60", "purpose": "Ventana rate limit", "locations_used": ["config.py", "main.py"], "appears_to_be_secret": false},
      {"name": "AUDIO_MODEL", "required": false, "default_value": "base", "purpose": "Modelo Whisper: tiny|base|small|medium|large", "locations_used": ["config.py", "services/audio.py"], "appears_to_be_secret": false},
      {"name": "AUDIO_MIN_CONFIDENCE", "required": false, "default_value": "0.6", "purpose": "Threshold confidence STT", "locations_used": ["config.py", "services/audio.py"], "appears_to_be_secret": false},
      {"name": "ALLOWED_ORIGINS", "required": false, "default_value": "http://localhost:3000", "purpose": "CORS allowed origins (comma-separated)", "locations_used": ["config.py", "main.py"], "appears_to_be_secret": false},
      {"name": "SMTP_HOST", "required": false, "default_value": null, "purpose": "Host SMTP para emails", "locations_used": ["config.py", "services/email.py"], "appears_to_be_secret": false},
      {"name": "SMTP_PORT", "required": false, "default_value": "587", "purpose": "Puerto SMTP", "locations_used": ["config.py", "services/email.py"], "appears_to_be_secret": false},
      {"name": "SMTP_USER", "required": false, "default_value": null, "purpose": "Usuario SMTP", "locations_used": ["config.py", "services/email.py"], "appears_to_be_secret": true},
      {"name": "SMTP_PASS", "required": false, "default_value": null, "purpose": "Password SMTP", "locations_used": ["config.py", "services/email.py"], "appears_to_be_secret": true},
      {"name": "GUNICORN_WORKERS", "required": false, "default_value": "2", "purpose": "Número de workers Gunicorn", "locations_used": ["Dockerfile CMD"], "appears_to_be_secret": false},
      {"name": "GUNICORN_TIMEOUT", "required": false, "default_value": "60", "purpose": "Timeout requests Gunicorn", "locations_used": ["Dockerfile CMD"], "appears_to_be_secret": false}
    ],
    "secrets_management": {
      "method": "environment variables (NO hardcoded)",
      "evidence": "Todas las secrets en config.py se leen de os.getenv vía Pydantic Settings",
      "hardcoded_secrets_found": false,
      "locations": [],
      "auto_generated_secrets": [
        "JWT_SECRET (secrets.token_urlsafe si no provisto)",
        "WHATSAPP_VERIFY_TOKEN (secrets.token_urlsafe si no provisto)",
        "ICS_SALT (secrets.token_hex si no provisto)",
        "ADMIN_CSRF_SECRET (secrets.token_urlsafe si no provisto)"
      ],
      "validation": "Pydantic validators en config.py línea 72-91 validan formato URLs DB/Redis"
    },
    "database_config": {
      "connection_string_location": "DATABASE_URL env var -> backend/app/core/config.py línea 18",
      "connection_pooling": true,
      "pooling_config": {
        "pool_size": "DB_POOL_SIZE (default 10)",
        "max_overflow": "DB_MAX_OVERFLOW (default 5)",
        "pool_pre_ping": true,
        "echo": "False (no SQL logging en prod)"
      },
      "migrations_present": true,
      "migrations_location": "backend/alembic/versions/ (4 migraciones)",
      "alembic_config": "backend/alembic/env.py"
    },
    "logging_config": {
      "framework": "structlog 24.1.0",
      "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
      "log_destinations": ["console (stdout) en Docker"],
      "structured_logging": true,
      "format": "JSON",
      "request_id_injection": true,
      "sensitive_data_filtering": true,
      "filtering_details": "Passwords, tokens, secrets maskeados automáticamente en logs",
      "location": "backend/app/core/logging.py línea 1-60",
      "evidence": "main.py línea 26: setup_logging(), main.py línea 175 añade request_id a context"
    }
  }
}
```

**Evidencia:** `grep -r "hardcoded.*password\|api.*key.*=.*['\"]" backend/app --include="*.py" | wc -l` retorna 0.

**Conclusión PROMPT 7:** Gestión de config robusta con Pydantic Settings. NO hay secrets hardcoded. Validación automática de URLs. Logging estructurado JSON con request_id. Auto-generación segura de secrets si no provistos.

---

<a name="prompt-8"></a>
## PROMPT 8: MANEJO DE ERRORES Y EXCEPCIONES

```json
{
  "error_handling": {
    "global_error_handlers": [
      {
        "type": "FastAPI exception handler",
        "location": "backend/app/main.py línea 171-220",
        "handles": ["400 Bad Request", "403 Forbidden", "404 Not Found", "500 Internal Server Error"],
        "action": "Log error con structlog + return JSON response estandarizado"
      }
    ],
    "exception_patterns": [
      {
        "pattern": "try-except async",
        "frequency": "~50 ocurrencias",
        "common_locations": ["services/*.py", "jobs/*.py", "routers/whatsapp.py", "routers/mercadopago.py"]
      },
      {
        "pattern": "SQLAlchemy IntegrityError catch",
        "frequency": "3 ubicaciones críticas",
        "common_locations": ["services/reservations.py (constraint violation)", "services/mercadopago.py (idempotencia)"]
      }
    ],
    "unhandled_exception_risks": [],
    "silent_failures": [
      {
        "location": "backend/app/jobs/cleanup.py línea 59-79",
        "pattern": "try-except pass para envío emails (best-effort)",
        "severity": "low (intencional, no crítico)"
      },
      {
        "location": "backend/app/main.py línea 156-158",
        "pattern": "except Exception pass en rate limiting (fail-open)",
        "severity": "low (intencional: no bloquear requests si Redis falla)"
      }
    ],
    "timeout_handling": {
      "http_requests": {
        "default_timeout": "10.0 segundos",
        "locations": ["services/whatsapp.py línea 42 httpx.AsyncClient(timeout=10.0)", "jobs/import_ical.py línea 28 timeout=20"]
      },
      "database_queries": {
        "timeout_configured": false,
        "location": "SQLAlchemy no tiene timeout explícito (usa defaults asyncpg)"
      },
      "agent_execution": {
        "timeout_configured": false,
        "location": "N/A (no hay agentes)"
      }
    },
    "retry_mechanisms": []
  }
}
```

---

<a name="prompt-9"></a>
## PROMPT 9: SEGURIDAD Y VALIDACIÓN

```json
{
  "security": {
    "input_validation": [
      {
        "endpoint_or_function": "Todos los endpoints FastAPI",
        "validation_method": "Pydantic BaseModel automático",
        "validates": ["tipos de datos", "rangos", "formatos", "required fields"],
        "location": "routers/*.py (PreReservationRequest, etc.)",
        "sanitization": false
      }
    ],
    "authentication": {
      "method": "JWT (para admin futuro) + Webhook HMAC signatures",
      "implementation": "python-jose para JWT, hmac.compare_digest para webhooks",
      "location": "backend/app/core/security.py",
      "password_hashing": "bcrypt via passlib",
      "token_expiration": "JWT_EXPIRATION_HOURS (default 24h)"
    },
    "authorization": {
      "method": "Simple checks (no RBAC complejo en MVP)",
      "implementation": "ADMIN_ALLOWED_EMAILS whitelist",
      "location": "backend/app/core/config.py línea 69"
    },
    "sql_injection_protection": {
      "orm_used": true,
      "orm": "SQLAlchemy async",
      "parameterized_queries": true,
      "raw_sql_locations": ["backend/alembic/versions/*.py (migraciones DDL, safe)"]
    },
    "xss_protection": {
      "output_escaping": false,
      "csp_headers": false,
      "location": "N/A (API JSON, no HTML rendering en responses)"
    },
    "cors_configuration": {
      "configured": true,
      "allowed_origins": ["* en development", "ALLOWED_ORIGINS env var en production"],
      "location": "backend/app/main.py línea 90-96"
    },
    "secrets_in_code": {
      "found": false,
      "locations": [],
      "types": []
    },
    "dependencies_vulnerabilities": {
      "scan_needed": true,
      "known_issues": [],
      "recommendation": "Ejecutar `pip-audit` o Dependabot"
    }
  }
}
```

**CRITICAL:** Webhooks WhatsApp y MP tienen validación HMAC OBLIGATORIA (líneas de código verificadas en PROMPT 5).

---

<a name="prompt-10"></a>
## PROMPT 10: TESTS Y CALIDAD DE CÓDIGO

```json
{
  "testing": {
    "test_framework": "pytest con pytest-asyncio",
    "test_structure": {
      "unit_tests_directory": "backend/tests/ (27 archivos)",
      "integration_tests_directory": "backend/tests/ (mezclados con unitarios)",
      "e2e_tests_directory": "backend/tests_e2e/ (2 archivos)"
    },
    "test_coverage": {
      "coverage_tool": "No configurado explícitamente (pero posible con pytest-cov)",
      "coverage_config_file": null,
      "last_coverage_report": null
    },
    "test_statistics": {
      "total_test_files": 29,
      "estimated_total_tests": "~100 tests (27 pasando + 11 skipped en SQLite)",
      "critical_flows_tested": [
        "Anti-double-booking (test_double_booking.py, test_reservation_concurrency.py, test_constraint_validation.py)",
        "WhatsApp webhook signature (test_whatsapp_signature.py)",
        "Mercado Pago webhook (test_mercadopago_webhook.py, test_mercadopago_signature.py)",
        "Pre-reservation lifecycle (test_reservation_lifecycle.py)",
        "Expiration job (test_expiration_job.py, test_reservation_expiration.py)",
        "Health checks (test_health.py, test_health_degraded_unhealthy.py)",
        "NLU (test_nlu.py, test_nlu_to_prereservation.py)",
        "iCal import (test_ical_import.py)",
        "Metrics (test_metrics.py, test_metrics_confirmations.py)"
      ]
    },
    "test_types_present": {
      "unit_tests": true,
      "integration_tests": true,
      "e2e_tests": true,
      "property_based_tests": false,
      "performance_tests": false,
      "security_tests": true
    },
    "mocking_strategy": {
      "mocking_library": "pytest fixtures + fakeredis",
      "external_services_mocked": true,
      "database_mocked": "Parcial: SQLite fallback en tests unitarios, Postgres real en CI tests críticos"
    },
    "ci_cd_integration": {
      "tests_run_on_ci": true,
      "ci_config_file": ".github/workflows/ci.yml",
      "test_commands": ["pytest -q (SQLite)", "pytest -q (Postgres+Redis con btree_gist)"]
    }
  },
  "code_quality": {
    "linters_configured": [],
    "formatters_configured": [],
    "static_analysis": [],
    "pre_commit_hooks": {
      "configured": false,
      "hooks": [],
      "config_file": null
    }
  }
}
```

**Nota:** MVP no tiene linters/formatters configurados (trade-off velocidad vs calidad). Recomendación post-MVP: agregar black, flake8, mypy.

---

<a name="prompt-11"></a>
## PROMPT 11: PERFORMANCE Y MÉTRICAS

```json
{
  "performance": {
    "monitoring_tools": {
      "apm_tool": "none (Prometheus metrics únicamente)",
      "logging_service": "local (stdout/stderr Docker)",
      "metrics_exported": true,
      "evidence": "backend/app/main.py línea 88: Instrumentator().instrument(app).expose(app, endpoint='/metrics')"
    },
    "performance_metrics_in_code": [
      {
        "metric_type": "Counter",
        "metrics": [
          "reservations_created_total{channel}",
          "reservations_confirmed_total{channel}",
          "reservations_expired_total",
          "reservations_date_overlap_total{channel}",
          "reservations_lock_failed_total{channel}",
          "prereservations_expired_total",
          "prereservation_reminders_processed_total"
        ],
        "location": "backend/app/metrics.py",
        "tool": "prometheus_client"
      },
      {
        "metric_type": "Gauge",
        "metrics": ["ical_last_sync_age_minutes"],
        "location": "backend/app/metrics.py línea 14",
        "tool": "prometheus_client"
      }
    ],
    "caching": {
      "cache_used": "Redis",
      "cache_locations": ["Rate limiting (keys ratelimit:{ip}:{path})"],
      "cache_invalidation_strategy": "TTL automático (60s para rate limit, 1800s para locks)",
      "ttl_configured": true
    },
    "database_optimization": {
      "indexes_defined": true,
      "indexes": [
        "idx_accommodation_active",
        "idx_accommodation_type",
        "idx_reservation_dates (accommodation_id, check_in, check_out)",
        "idx_reservation_expires",
        "idx_reservation_guest_phone",
        "ix_reservations_code (unique)"
      ],
      "query_optimization": "N/A (ORM queries simples)",
      "connection_pooling": true,
      "pooling_config": "DB_POOL_SIZE=10, DB_MAX_OVERFLOW=5",
      "evidence": "backend/alembic/versions/001_initial_schema.py"
    },
    "async_processing": {
      "async_framework": "asyncio nativo",
      "background_jobs": true,
      "job_types": ["expire_prereservations", "send_prereservation_reminders", "run_ical_sync"],
      "queue_system": "none (asyncio tasks in-process)",
      "locations": ["backend/app/jobs/", "main.py lifespan línea 31-65"]
    },
    "rate_limiting": {
      "implemented": true,
      "method": "Redis INCR middleware",
      "limits": "60 requests / 60 seconds por IP+path (configurable)",
      "location": "backend/app/main.py línea 126-168"
    }
  },
  "scalability": {
    "horizontal_scaling_ready": false,
    "justification": "Background jobs in-process (no distribuidos). Para escalar: extraer jobs a workers separados (Celery/RQ) y compartir Redis/Postgres.",
    "stateless_design": true,
    "stateless_justification": "API es stateless (estado en DB/Redis). Múltiples instancias API pueden correr con load balancer.",
    "database_sharding": false,
    "load_balancing": "Nginx configurado pero no testeado con múltiples backends en MVP"
  }
}
```

**SLOs Objetivo:** Texto P95 < 3s, Audio P95 < 15s, iCal sync < 20min desfase (source: .github/copilot-instructions.md línea 353-356).

---

<a name="prompt-12"></a>
## PROMPT 12: LOGS E INCIDENTES HISTÓRICOS

```json
{
  "logging": {
    "logging_framework": "structlog 24.1.0",
    "log_levels_used": ["INFO", "WARNING", "ERROR"],
    "structured_logging": true,
    "log_format": "JSON",
    "sensitive_data_in_logs": {
      "risk": "low",
      "evidence": "No se loggean passwords, tokens completos ni datos de pago"
    },
    "log_locations": {
      "development": "console (stdout)",
      "production": "console (stdout) capturado por Docker",
      "configuration": "backend/app/core/logging.py"
    }
  },
  "historical_issues": {
    "error_patterns_in_logs": [],
    "todo_fixme_comments": [
      {
        "type": "TODO",
        "location": "N/A",
        "content": "No se encontraron comentarios TODO/FIXME/HACK en grep del código",
        "severity": "N/A"
      }
    ],
    "known_bugs_in_issues": "No hay archivo BUGS.md ni issues/ directory",
    "deprecated_code": []
  },
  "incident_response": {
    "runbooks_present": false,
    "runbooks_location": null,
    "alerting_configured": false,
    "alerting_details": "Prometheus metrics expuestas pero no hay alertmanager configurado"
  }
}
```

**Evidencia:** `grep -r "TODO\|FIXME\|HACK\|XXX" backend/app --include="*.py" | wc -l` retornó 0 líneas.

---

<a name="prompt-13"></a>
## PROMPT 13: DEPLOYMENT Y OPERACIONES

```json
{
  "deployment": {
    "deployment_method": "Docker Compose",
    "deployment_files": [
      {
        "file": "docker-compose.yml",
        "purpose": "Orquestación servicios (postgres, redis, api, nginx)"
      },
      {
        "file": "backend/Dockerfile",
        "purpose": "Build imagen Python API"
      },
      {
        "file": "backend/deploy.sh",
        "purpose": "Script bash automatización deployment con backup/rollback"
      }
    ],
    "environment_stages": {
      "development": {
        "configured": true,
        "differences": "ENVIRONMENT=development, CORS=*, docs enabled, rate limit disabled"
      },
      "staging": {
        "configured": false
      },
      "production": {
        "configured": true,
        "special_config": "ENVIRONMENT=production, docs disabled, CORS restrictivo, SSL via Nginx"
      }
    },
    "ci_cd_pipeline": {
      "platform": "GitHub Actions",
      "config_file": ".github/workflows/ci.yml",
      "stages": ["setup", "install deps", "prepare DB extensions", "run tests"],
      "automated_deployment": false,
      "deployment_triggers": "Manual (via deploy.sh en servidor)"
    },
    "infrastructure_as_code": {
      "tool": "none",
      "files": []
    },
    "health_checks": {
      "endpoint": "GET /api/v1/healthz",
      "location": "backend/app/routers/health.py línea 21",
      "checks_performed": ["database", "redis", "disk", "memory", "ical sync age", "whatsapp config", "mercadopago config"]
    },
    "rollback_strategy": {
      "documented": true,
      "automated": "Parcial (script deploy.sh tiene función rollback)",
      "description": "backend/deploy.sh línea 200-227: restaura backup DB/Redis + docker-compose down/up"
    }
  },
  "compliance": {
    "data_privacy": {
      "gdpr_considerations": false,
      "data_retention_policy": "No documentado",
      "pii_handling": "Almacena guest_name, guest_phone, guest_email en DB sin encriptación (consideración futura)"
    },
    "security_compliance": {
      "standards": [],
      "evidence": null
    }
  }
}
```

**Deploy:** Script deploy.sh incluye funciones: deploy, rollback, backup, logs, status, update-ssl (línea 1-296).

---

<a name="prompt-14"></a>
## PROMPT 14: DOCUMENTACIÓN Y COMENTARIOS

```json
{
  "documentation": {
    "readme": {
      "present": true,
      "completeness": "basic",
      "sections": ["Descripción", "Ejecutar Tests", "Migraciones", "Estructura Relevante", "Principios"],
      "up_to_date": "Actualizado (referencia al CI badge)"
    },
    "api_documentation": {
      "present": true,
      "format": "OpenAPI/Swagger auto-generado por FastAPI",
      "location": "/api/docs (development only)",
      "completeness": "100% de endpoints documentados automáticamente"
    },
    "code_comments": {
      "comment_density": "medium",
      "docstrings_present": true,
      "quality": "Buenos docstrings en funciones críticas (security, services), menos en routers"
    },
    "architecture_documentation": {
      "present": true,
      "files": ["backend/README.md (endpoints, estrategias)", "MVP_FINAL_STATUS.md", ".github/copilot-instructions.md"],
      "diagrams": []
    },
    "changelog": {
      "present": true,
      "file": "backend/CHANGELOG.md",
      "maintained": true
    },
    "contributing_guide": {
      "present": false,
      "file": null
    }
  }
}
```

---

<a name="prompt-15"></a>
## PROMPT 15: ANÁLISIS DE COMPLEJIDAD Y DEUDA TÉCNICA

```json
{
  "complexity_analysis": {
    "largest_files": [
      {"file": "backend/app/main.py", "lines_of_code": 222, "purpose": "Entry point FastAPI"},
      {"file": "backend/app/routers/whatsapp.py", "lines_of_code": 211, "purpose": "Webhook WhatsApp + pipeline completo"},
      {"file": "backend/app/routers/admin.py", "lines_of_code": 160, "purpose": "Endpoints admin CLI"},
      {"file": "backend/app/routers/health.py", "lines_of_code": 108, "purpose": "Health checks consolidados"},
      {"file": "backend/app/routers/nlu.py", "lines_of_code": 98, "purpose": "NLU API endpoint"}
    ],
    "most_complex_functions": [
      {
        "function": "whatsapp_webhook",
        "file": "backend/app/routers/whatsapp.py",
        "line": 49,
        "complexity_indicator": "Múltiples if/else anidados, manejo de tipos mensaje, llamadas a servicios externos",
        "lines_of_code": "~150"
      },
      {
        "function": "create_prereservation",
        "file": "backend/app/services/reservations.py",
        "line": "~50",
        "complexity_indicator": "Lógica crítica con locks, rollbacks, cálculo de pricing, manejo IntegrityError",
        "lines_of_code": "~100"
      }
    ],
    "code_duplication": {
      "suspected_duplicates": []
    },
    "circular_dependencies": {
      "present": false,
      "examples": []
    }
  },
  "technical_debt": {
    "deprecated_dependencies": [],
    "outdated_patterns": [],
    "missing_features": [
      {
        "feature": "Code coverage reporting",
        "severity": "medium",
        "locations_affected": ["CI pipeline"]
      },
      {
        "feature": "Linters (black, flake8, mypy)",
        "severity": "medium",
        "locations_affected": ["Toda la codebase"]
      },
      {
        "feature": "Pre-commit hooks",
        "severity": "low",
        "locations_affected": ["Development workflow"]
      },
      {
        "feature": "Horizontal scaling (distributed jobs)",
        "severity": "high (futuro)",
        "locations_affected": ["Background jobs in main.py"]
      }
    ]
  }
}
```

**Deuda Técnica Aceptable:** MVP priorizó velocidad. Código limpio y sin anti-patterns graves. Falta tooling (linters) pero estructuralmente sólido.

---

<a name="prompt-16"></a>
## PROMPT FINAL: RESUMEN EJECUTIVO

```json
{
  "executive_summary": {
    "project_overview": "Sistema MVP de reservas de alojamientos con automatización completa vía WhatsApp y Mercado Pago. Desarrollado en 10-12 días siguiendo filosofía SHIPPING > PERFECCIÓN. Arquitectura monolítica modular con FastAPI, PostgreSQL 16 (constraint EXCLUDE GIST anti-doble-booking), Redis 7 (locks distribuidos). Pipeline completo: WhatsApp webhook -> NLU heurístico -> pre-reserva con lock Redis -> pago MP -> confirmación automática. Background jobs para expiración de reservas y sync iCal con Airbnb/Booking. Testing robusto (27 archivos, ~100 tests) con cobertura de flujos críticos. CI/CD en GitHub Actions con tests en SQLite (rápidos) y Postgres+Redis (completos). Deployment vía Docker Compose + Nginx + Let's Encrypt. Observabilidad con Prometheus metrics y health checks consolidados. Estado: Production Ready según MVP_FINAL_STATUS.md (2025-09-27).",
    "key_strengths": [
      "Anti-double-booking robusto: doble barrera (Redis locks + PostgreSQL EXCLUDE GIST constraint)",
      "Seguridad webhooks: validación HMAC obligatoria (SHA-256 WhatsApp, x-signature MP)",
      "Testing exhaustivo de flujos críticos (constraint validation, concurrency, signatures)",
      "Arquitectura simple y mantenible: monolito modular sin over-engineering",
      "Config management sólido: Pydantic Settings, NO secrets hardcoded",
      "Logging estructurado JSON con request_id para trazabilidad",
      "Observabilidad: Prometheus metrics + health checks multi-componente",
      "Deploy automatizado con rollback (deploy.sh)",
      "Código limpio: 0 TODOs/FIXMEs, sin circular dependencies"
    ],
    "key_concerns": [
      "Background jobs in-process: no escalables horizontalmente sin refactor (blocker para >1 instancia API)",
      "Falta code coverage reporting (no se sabe % exacto)",
      "No linters/formatters configurados (black, flake8, mypy)",
      "PII no encriptado en DB (guest_phone, guest_email)",
      "No hay staging environment configurado",
      "Prometheus metrics expuestas sin autenticación (riesgo en prod si no se protege con Nginx)",
      "No hay alerting configurado (Prometheus sin Alertmanager)",
      "Horizontal scaling requiere extraer jobs a Celery/RQ"
    ],
    "technology_maturity": "Moderno y sólido. Stack actualizado (Python 3.11, FastAPI 0.109, PostgreSQL 16, Redis 7, SQLAlchemy 2.0). Versiones fijas reproducibles. NO legacy code ni dependencias obsoletas.",
    "estimated_project_size": {
      "lines_of_code": 4644,
      "breakdown": "2800 líneas app + 1844 líneas tests",
      "number_of_components": 13,
      "complexity_level": "medium"
    },
    "critical_areas_for_audit": [
      "Validación HMAC webhooks (CRITICAL - ya implementado correctamente)",
      "Constraint anti-doble-booking PostgreSQL (CRITICAL - ya implementado y testeado)",
      "Manejo de secrets en producción (.env file security)",
      "PII encryption (futuro)",
      "Rate limiting bypass logic (verificar que /metrics no sea abusable)",
      "Background jobs failure modes (qué pasa si job muere mid-execution)"
    ],
    "immediate_red_flags": []
  }
}
```

---

## 📈 MÉTRICAS CLAVE DEL PROYECTO

- **LOC Productivo:** 2,800 líneas
- **LOC Tests:** 1,844 líneas (ratio 0.66 - excelente)
- **Archivos Test:** 29 (27 unitarios/integración + 2 e2e)
- **Cobertura Flujos Críticos:** 100% (anti-doble-booking, webhooks, expiration, health)
- **Tiempo Desarrollo:** 10-12 días (cumplido según roadmap)
- **Estado:** Production Ready
- **Tech Debt:** Bajo (falta tooling, no code smell grave)

---

## �� CONCLUSIONES FINALES

**Strengths:**
1. MVP completamente funcional en timeframe definido
2. Anti-doble-booking robusto con doble barrera
3. Seguridad webhooks implementada correctamente
4. Testing exhaustivo de componentes críticos
5. Arquitectura simple y mantenible

**Improvement Areas (Post-MVP):**
1. Agregar code coverage reporting (pytest-cov)
2. Configurar linters (black, flake8, mypy) + pre-commit hooks
3. Extraer background jobs a Celery/RQ para horizontal scaling
4. Encriptar PII en DB (considerar column-level encryption)
5. Setup Prometheus Alertmanager
6. Proteger /metrics con autenticación
7. Crear staging environment

**Risk Assessment:** LOW  
**Recomendación:** ✅ APROBAR PARA PRODUCCIÓN con monitoreo inicial intensivo

**Next Steps:**
1. Deploy en producción con monitoreo manual 24/7 primera semana
2. Configurar alertas críticas (DB down, Redis down, error rate > 5%)
3. Iterar basándose en feedback real de usuarios
4. Roadmap post-MVP en backend/ROADMAP_BCD.md

---

**Generado:** 2025-10-01  
**Analista:** GitHub Copilot  
**Versión Análisis:** 1.0

