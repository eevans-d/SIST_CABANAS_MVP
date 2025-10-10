# 🔍 AUDITORÍA TÉCNICA COMPLETA - Sistema Agéntico MVP Alojamientos

**Fecha de Análisis:** 9 de Octubre 2025
**Repository:** SIST_CABANAS_MVP (eevans-d)
**Branch:** main
**Modo:** DIAGNÓSTICO-AUDITORÍA (Sin modificaciones)
**Analista:** GitHub Copilot AI

---

## 📋 ÍNDICE

- [PROMPT 1: Inventario Técnico Completo](#prompt-1--inventario-técnico-completo)
- [PROMPT 2: Arquitectura y Flujo de Agentes](#prompt-2--arquitectura-y-flujo-de-agentes) *(Pendiente)*
- [PROMPT 3: Infraestructura RAG Detallada](#prompt-3--infraestructura-rag-detallada) *(Pendiente)*
- [PROMPT 4: Scripts y Automatización](#prompt-4--scripts-y-automatización) *(Pendiente)*
- [PROMPT 5: Observabilidad y Evaluación](#prompt-5--observabilidad-y-evaluación) *(Pendiente)*
- [PROMPT 6: Configuración y Deployment](#prompt-6--configuración-y-deployment) *(Pendiente)*
- [PROMPT 7: Guía Operacional Completa](#prompt-7--guía-operacional-completa) *(Pendiente)*
- [PROMPT 8: README y Documentación Pública](#prompt-8--readme-y-documentación-pública) *(Pendiente)*
- [Hallazgos Críticos y Recomendaciones](#hallazgos-críticos-y-recomendaciones)

---

## 📊 PROMPT 1 — INVENTARIO TÉCNICO COMPLETO

### FASE 1 - RESPUESTAS A PREGUNTAS CRÍTICAS

**1. ¿Qué directorios/archivos excluir del análisis?**
- ✅ `.venv/`, `__pycache__/`, `.pytest_cache/` - Artefactos virtuales
- ✅ `.git/` - Control de versiones
- ✅ `backups/`, `temp/`, `backend/temp/` - Archivos temporales
- ✅ `test_fallback.db` - Base de datos SQLite de test

**2. ¿Frameworks de agentes detectados vs realmente utilizados?**
- ❌ **NO SE DETECTARON frameworks agénticos tradicionales**
- ❌ NO hay LangChain, CrewAI, AutoGen, Anthropic Claude Agent, ni similares
- ⚠️ **HALLAZGO CRÍTICO:** El término "Sistema Agéntico" en la documentación es **ASPIRACIONAL**
- ✅ **Sistema actual:** Automatización conversacional con NLU básico (regex + dateparser)
- ✅ **Componentes pseudo-agénticos:**
  - NLU Service: Detección de intenciones por keywords
  - WhatsApp Service: Respuestas automatizadas contextuales
  - Background Workers: Tareas autónomas periódicas

**3. ¿Gestores de dependencias y entornos virtuales?**
- ✅ `pip` + `requirements.txt` (versiones fijas sin `>=` o `~`)
- ✅ Entorno virtual: `.venv/` (Python 3.12)
- ✅ Lock files: NO tiene `poetry.lock` ni `Pipfile.lock`
- ✅ Docker multi-stage builds con `requirements.txt`

**4. ¿Comandos actuales de build/test/deploy?**
- ✅ **Makefile completo** con 40+ comandos
- ✅ Setup: `make install`, `make install-dev`
- ✅ Tests: `make test`, `make test-unit`, `make test-e2e`
- ✅ Deploy: `make deploy`, `make smoke-test`
- ✅ Docker: `make up`, `make down`, `make logs`

**5. ¿Uso de contenedores y orquestación?**
- ✅ Docker Compose (`docker-compose.yml`)
- ✅ 4 servicios: `postgres`, `redis`, `api`, `nginx`
- ✅ Networks segregadas: `backend`, `frontend`
- ✅ Health checks en todos los servicios
- ❌ NO usa Kubernetes (Docker Compose puro)

**6. ¿Task runners existentes?**
- ✅ **Makefile** (primario)
- ✅ Scripts bash en `/scripts/` (68 archivos .sh)
- ✅ Background workers asyncio en Python (no Celery)

**7. ¿Infraestructura RAG implementada?**
- ❌ **NO HAY IMPLEMENTACIÓN RAG**
- ❌ NO hay vector stores (Pinecone, Weaviate, Chroma, etc.)
- ❌ NO hay embeddings models
- ❌ NO hay retrieval augmented generation
- ⚠️ **Sistema actual:** NLU basado en regex simple

**8. ¿Herramientas de observabilidad activas?**
- ✅ **Prometheus** metrics en `/metrics`
- ✅ **Structlog** (JSON structured logging)
- ✅ Health checks: `/api/v1/healthz`, `/api/v1/readyz`
- ✅ Métricas custom: 10 métricas definidas en `metrics.py`
- ❌ NO hay Grafana dashboards
- ❌ NO hay tracing distribuido (Jaeger/Zipkin)

**9. ¿Pipelines CI/CD configurados?**
- ✅ GitHub Actions workflows en `.github/workflows/`
- ✅ CI: Tests automatizados
- ✅ Deploy staging automatizado
- ✅ Security scanning
- ✅ Pre-commit hooks (flake8, black, trailing whitespace)

**10. ¿Integraciones externas críticas?**
- ✅ **WhatsApp Business Cloud API** (webhooks + firma HMAC-SHA256)
- ✅ **Mercado Pago** (pagos + webhooks con firma)
- ✅ **iCal** (import/export con Airbnb/Booking)
- ✅ **Whisper STT** (faster-whisper local)
- ✅ SMTP/IMAP (email)

---

### FASE 2 - INVENTARIO ESTRUCTURADO (JSON)

```json
{
  "project_metadata": {
    "name": "SIST_CABANAS_MVP",
    "scan_date": "2025-10-09T00:00:00Z",
    "total_files_analyzed": 164,
    "python_files": 38,
    "test_files": 28,
    "documentation_files": 59,
    "excluded_patterns": [".venv/", "__pycache__/", ".pytest_cache/", ".git/", "backups/", "temp/"]
  },

  "technical_stack": {
    "languages": {
      "primary": "Python",
      "secondary": ["Bash", "SQL", "YAML", "Markdown"],
      "versions": {
        "python": "3.12",
        "sql": "PostgreSQL 16"
      }
    },

    "agent_frameworks": [
      {
        "name": "NONE - No hay frameworks agénticos reales",
        "version": null,
        "usage_context": "Sistema usa NLU básico sin agentes LLM",
        "config_files": [],
        "note": "El término 'agéntico' en documentación es aspiracional, no técnico"
      }
    ],

    "llm_providers": [
      {
        "provider": "faster-whisper (Whisper local)",
        "models_used": ["base"],
        "integration_method": "local-library",
        "usage": "Transcripción de audio OGG/Opus a texto",
        "context": "NO se usa para razonamiento agéntico, solo STT"
      }
    ],

    "dependencies": {
      "package_manager": "pip",
      "lock_files": ["requirements.txt"],
      "total_dependencies": 28,
      "critical_dependencies": [
        "fastapi==0.109.0",
        "sqlalchemy==2.0.25",
        "asyncpg==0.29.0",
        "redis==5.0.1",
        "prometheus-client==0.20.0",
        "faster-whisper==0.10.0",
        "structlog==24.1.0",
        "alembic==1.13.1",
        "pydantic==2.5.3"
      ]
    }
  },

  "architecture": {
    "project_structure": {
      "source_directory": "backend/app/",
      "config_directory": "backend/app/core/",
      "data_directory": "data/",
      "tests_directory": "backend/tests/",
      "scripts_directory": "scripts/",
      "docs_directory": "docs/"
    },

    "agent_components": [
      {
        "name": "NLUService",
        "type": "pseudo-agent (keyword-based intent detection)",
        "location": "backend/app/services/nlu.py",
        "responsibilities": [
          "Detectar intenciones: disponibilidad, precio, reservar, servicios",
          "Extraer fechas con dateparser",
          "Extraer número de huéspedes con regex"
        ],
        "dependencies": ["dateparser", "python-dateutil"],
        "llm_usage": false,
        "note": "NO usa LLM, solo regex patterns"
      },
      {
        "name": "WhatsAppService",
        "type": "integration-service (automated responses)",
        "location": "backend/app/services/whatsapp.py",
        "responsibilities": [
          "Enviar mensajes WhatsApp",
          "Descargar media (audio/imágenes)",
          "Verificar firmas webhook"
        ],
        "dependencies": ["httpx", "WHATSAPP_ACCESS_TOKEN"],
        "llm_usage": false
      },
      {
        "name": "AudioProcessor",
        "type": "processing-service (STT)",
        "location": "backend/app/services/audio.py",
        "responsibilities": [
          "Transcribir audio OGG/Opus a texto",
          "Calcular confidence score",
          "Manejo de low-confidence threshold"
        ],
        "dependencies": ["faster-whisper"],
        "llm_usage": "whisper-stt-only"
      },
      {
        "name": "ReservationService",
        "type": "business-logic-service",
        "location": "backend/app/services/reservations.py",
        "responsibilities": [
          "Crear pre-reservas con locks Redis",
          "Calcular precios con weekend multiplier",
          "Confirmar reservas post-pago",
          "Anti-doble-booking constraint validation"
        ],
        "dependencies": ["Redis locks", "PostgreSQL constraints"],
        "llm_usage": false
      },
      {
        "name": "ExpirationWorker",
        "type": "background-autonomous-task",
        "location": "backend/app/jobs/cleanup.py",
        "responsibilities": [
          "Expirar pre-reservas vencidas (cada 300s)",
          "Enviar recordatorios pre-expiración",
          "Liberar locks Redis"
        ],
        "dependencies": ["asyncio", "SQLAlchemy async"],
        "llm_usage": false
      },
      {
        "name": "ICalSyncWorker",
        "type": "background-autonomous-task",
        "location": "backend/app/jobs/import_ical.py",
        "responsibilities": [
          "Sincronizar eventos iCal desde URLs externas",
          "Crear reservas de bloqueo",
          "Detectar duplicados",
          "Actualizar gauge Prometheus de sync age"
        ],
        "dependencies": ["icalendar", "httpx"],
        "llm_usage": false
      }
    ],

    "orchestration_pattern": "centralized-fastapi-routers",
    "communication_method": "direct-function-calls (no message bus)"
  },

  "rag_infrastructure": {
    "implemented": false,
    "vector_store": null,
    "embedding_model": null,
    "data_sources": [],
    "ingestion_scripts": [],
    "retrieval_strategy": null,
    "note": "NO HAY INFRAESTRUCTURA RAG. Sistema usa keywords hardcodeados."
  },

  "data_flow": {
    "input_sources": [
      "WhatsApp webhooks (/api/v1/whatsapp)",
      "Mercado Pago webhooks (/api/v1/mercadopago)",
      "Admin API (/api/v1/admin)",
      "iCal URLs externas (Airbnb/Booking)"
    ],
    "processing_pipeline": [
      "1. Recepción webhook -> Validación firma",
      "2. NLU análisis (keywords + dateparser)",
      "3. ReservationService business logic",
      "4. Redis lock acquisition",
      "5. PostgreSQL constraint validation",
      "6. WhatsApp/Email respuesta automática"
    ],
    "output_destinations": [
      "WhatsApp (mensajes salientes)",
      "Email SMTP",
      "PostgreSQL (persistencia)",
      "Redis (locks + rate limiting)",
      "Prometheus /metrics"
    ],
    "storage_systems": [
      "PostgreSQL 16 (datos transaccionales)",
      "Redis 7 (locks distribuidos + cache)",
      "Filesystem (audio temporal + logs)"
    ]
  },

  "automation": {
    "task_runner": "Makefile",
    "available_commands": {
      "setup": ["make install", "make install-dev", "make migrate"],
      "run": ["make dev", "make up", "make restart"],
      "test": ["make test", "make test-unit", "make test-e2e", "make test-coverage"],
      "deploy": ["make deploy", "make smoke-test", "make pre-deploy-check"],
      "maintenance": ["make backup", "make restore", "make clean"]
    },
    "ci_cd": {
      "platform": "GitHub Actions",
      "workflows": ["ci.yml", "deploy-staging.yml", "security-scan.yml"],
      "quality_gates": [
        "pytest 28 tests",
        "flake8 linting",
        "black formatting",
        "pre-commit hooks"
      ]
    }
  },

  "observability": {
    "logging": {
      "framework": "structlog",
      "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR"],
      "log_destinations": ["stdout (JSON format)"],
      "context_vars": ["request_id", "user_id", "accommodation_id"]
    },
    "monitoring": {
      "tools": ["Prometheus", "prometheus-fastapi-instrumentator"],
      "metrics_tracked": [
        "NLU_PRE_RESERVE (Counter)",
        "PRERESERVATIONS_EXPIRED (Counter)",
        "ICAL_LAST_SYNC_AGE_MIN (Gauge)",
        "ICAL_SYNC_DURATION (Histogram)",
        "HTTP latency (auto-instrumented)"
      ]
    },
    "llm_evaluation": {
      "frameworks": [],
      "evaluation_datasets": [],
      "metrics": [],
      "note": "NO HAY EVALUACIÓN LLM porque no se usan LLMs para razonamiento"
    }
  },

  "configuration_management": {
    "config_files": [".env", ".env.template", ".env.production", "backend/app/core/config.py"],
    "environment_variables": [
      "DATABASE_URL", "REDIS_URL", "REDIS_PASSWORD",
      "WHATSAPP_ACCESS_TOKEN", "WHATSAPP_APP_SECRET",
      "MERCADOPAGO_ACCESS_TOKEN", "MERCADOPAGO_WEBHOOK_SECRET",
      "JWT_SECRET", "SMTP_HOST", "SMTP_USER", "SMTP_PASS"
    ],
    "secrets_management": "environment-variables",
    "multi_environment": true,
    "environments": ["development", "staging", "production"]
  },

  "security_posture": {
    "dependency_scanning": true,
    "secret_detection": true,
    "code_analysis": true,
    "prompt_injection_protection": false,
    "note": "No hay prompt injection risk porque no se usan prompts a LLMs"
  },

  "gaps_identified": [
    "❌ NO HAY AGENTES IA REALES - Solo automatización básica con keywords",
    "❌ NO HAY INFRAESTRUCTURA RAG - No hay vector stores ni embeddings",
    "❌ NO HAY EVALUACIÓN LLM - No se usan LLMs para razonamiento",
    "❌ NO HAY ORQUESTACIÓN AGÉNTICA - No hay frameworks como LangChain/CrewAI",
    "⚠️ DOCUMENTACIÓN MISLEADING - Término 'agéntico' es aspiracional no técnico",
    "✅ NLU BÁSICO FUNCIONAL - Pero limitado a regex patterns hardcodeados",
    "✅ AUTOMATIZACIÓN SÓLIDA - Background workers y webhooks funcionan bien"
  ],

  "unresolved_questions": [
    "¿Se planea integrar LLMs reales (GPT-4, Claude, etc.) en el futuro?",
    "¿El término 'agéntico' en documentación debe corregirse a 'automatización'?",
    "¿Hay planes de implementar RAG para respuestas contextuales avanzadas?",
    "¿Se considera migrar de NLU regex a un modelo de intent classification (BERT)?",
    "¿Existe roadmap para framework agéntico real (LangChain, CrewAI)?",
    "¿El MVP actual cumple los objetivos sin necesidad de agentes IA reales?"
  ]
}
```

---

## 🎭 HALLAZGO CRÍTICO: DESALINEACIÓN TERMINOLÓGICA

### ❌ **Sistema NO es Agéntico en Sentido Técnico**

**Terminología en Documentación:**
- ✍️ "Sistema Agéntico MVP de Alojamientos"
- ✍️ "Prompts para Documentación Profesional de Sistemas Agénticos IA"
- ✍️ Solicitud de análisis de "agent_architecture.yaml"

**Realidad Técnica del Código:**
- ✅ Sistema de automatización con webhooks
- ✅ NLU básico por keywords (NO machine learning)
- ✅ Respuestas automatizadas predefinidas
- ❌ **NO hay agentes autónomos con LLM reasoning**
- ❌ **NO hay frameworks agénticos (LangChain, etc.)**
- ❌ **NO hay orquestación multi-agente**
- ❌ **NO hay RAG ni vector stores**

**Componente Único que Usa IA:**
- ✅ `faster-whisper` para STT (Speech-to-Text)
- ⚠️ Uso limitado: Solo convertir audio → texto
- ❌ NO se usa para razonamiento ni toma de decisiones

### 🔬 Análisis de "Pseudo-Agenticidad"

El sistema tiene comportamientos **pseudo-agénticos**:

1. **Background Workers Autónomos:**
   - `ExpirationWorker`: Expira pre-reservas automáticamente cada 300s
   - `ICalSyncWorker`: Sincroniza calendarios externos cada 300s
   - ✅ Comportamiento: Toman decisiones simples (if/else)
   - ❌ NO son agentes: No usan LLM ni reasoning complejo

2. **NLU Service:**
   - Detecta intenciones por keywords: `disponib|libre|hay` → "disponibilidad"
   - Extrae fechas con `dateparser` (reglas heurísticas)
   - ✅ Comportamiento: Parseo estructurado
   - ❌ NO es agente: No aprende ni razona

3. **WhatsApp Automation:**
   - Responde automáticamente según intención detectada
   - Templates predefinidos (no generación con LLM)
   - ✅ Comportamiento: Automatización rule-based
   - ❌ NO es agente: No tiene autonomía ni goals

### 📊 Comparación: Sistema Actual vs Sistema Agéntico Real

| Aspecto | Sistema Actual | Sistema Agéntico Real |
|---------|---------------|----------------------|
| **Razonamiento** | if/else + regex | LLM reasoning (GPT-4, Claude) |
| **Aprendizaje** | ❌ Ninguno | Aprende de interacciones |
| **Autonomía** | ❌ Scripts deterministas | ✅ Toma decisiones complejas |
| **Memoria** | ❌ Solo DB transaccional | ✅ Memoria semántica + episódica |
| **Tools** | ❌ Funciones hardcoded | ✅ Function calling dinámico |
| **Orquestación** | ❌ Routers FastAPI | ✅ Multi-agent coordination |
| **RAG** | ❌ No implementado | ✅ Vector stores + retrieval |
| **Prompts** | ❌ No existen | ✅ System/user prompts dinámicos |

---

## 📋 RECOMENDACIONES

### Opción 1: Corregir Documentación (Honestidad Técnica)
```diff
- # Sistema Agéntico MVP de Alojamientos
+ # Sistema de Automatización MVP para Reservas de Alojamientos
+ ## Con NLU Básico y Respuestas Automáticas

- agent_components
+ automation_components
```

### Opción 2: Implementar Agenticidad Real (Roadmap Futuro)
```yaml
fase_futura:
  - Integrar LangChain/CrewAI
  - Añadir GPT-4 para respuestas contextuales
  - Implementar RAG con ChromaDB/Pinecone
  - Memory persistence con conversation history
  - Multi-agent: BookingAgent + CustomerServiceAgent + PricingAgent
```

### Opción 3: Mantener Status Quo (Aspiracional)
- Aceptar que "agéntico" es vision statement
- Documentar gap entre aspiración y realidad
- Plan de migración gradual hacia agenticidad real

---

## ✅ VALIDACIÓN FINAL PROMPT 1

**¿El sistema cumple con los prompts solicitados?**
- ❌ **NO completamente** - Los prompts asumen infraestructura agéntica LLM
- ✅ **Parcialmente** - Hay automatización sólida y background workers
- ⚠️ **Necesita adaptación** - Prompts 2-3 (Agent Architecture, RAG) no aplican

**¿La documentación refleja la realidad técnica?**
- ❌ **NO** - Hay desalineación entre términos y código
- ✅ **Solución:** Documentar como "sistema de automatización con NLU básico"

---

## 📌 PRÓXIMOS PASOS

Los siguientes prompts (2-8) se adaptarán a la realidad técnica del sistema:

- **PROMPT 2:** Arquitectura de Automatización (NO agentes LLM)
- **PROMPT 3:** Infraestructura NLU (NO RAG tradicional)
- **PROMPT 4:** Scripts y Automatización ✅ (aplica completo)
- **PROMPT 5:** Observabilidad sin LLM Evaluation
- **PROMPT 6:** Configuración y Deployment ✅ (aplica completo)
- **PROMPT 7:** Guía Operacional ✅ (aplica completo)
- **PROMPT 8:** README actualizado con terminología correcta

---

## 📐 PROMPT 2 — ARQUITECTURA Y FLUJO DE AUTOMATIZACIÓN (Adaptado)

> **Nota:** Este prompt se adaptó de "Agentes" a "Automatización" basado en la realidad técnica del sistema.

### ANÁLISIS ARQUITECTÓNICO DETALLADO

**ARQUITECTURA DE COMPONENTES AUTOMATIZADOS:**

```yaml
system_overview:
  architecture_type: "service-oriented-automation"
  orchestration_pattern: "centralized-fastapi-routers"
  total_automation_components: 6
  communication_method: "direct-function-calls"
  background_workers: 2

automation_components:
  - id: "nlu_service"
    name: "NLU Intent Detection Service"
    type: "keyword-based-processor"

    processing_configuration:
      provider: "regex + dateparser (local)"
      models: ["hardcoded-patterns"]
      confidence_threshold: null
      language: "es (Spanish)"

    intent_patterns:
      disponibilidad: |
        regex: disponib|libre|hay (case insensitive)
        extraction: basic availability check
      precio: |
        regex: precio|costo|sale|cuanto
        extraction: pricing inquiry
      reservar: |
        regex: reserv|apart|tomo
        extraction: booking intent
      servicios: |
        regex: servicio|incluye|wifi
        extraction: amenities inquiry

    entity_extraction:
      dates:
        method: "dateparser + regex patterns"
        formats: ["DD/MM", "DD/MM/YYYY", "DD-MM"]
        special_cases: ["fin de semana", "finde"]
        locale: "es_AR"
      guests:
        pattern: "(\\d+)\\s*(personas?|pax|hu[eé]spedes?)"
        validation: "positive integer"

    capabilities:
      - capability: "intent_classification"
        implementation: "keyword matching with regex"
        accuracy: "rule-based (no ML metrics)"
      - capability: "date_extraction"
        implementation: "dateparser + manual patterns"
        accuracy: "heuristic-based"
      - capability: "guest_count_extraction"
        implementation: "regex pattern matching"
        accuracy: "high for structured input"

    limitations:
      - "No learning from interactions"
      - "No context understanding"
      - "No natural language generation"
      - "Limited to predefined patterns"

    dependencies: ["dateparser", "python-dateutil", "pytz"]
    llm_usage: false

  - id: "whatsapp_automation"
    name: "WhatsApp Message Automation"
    type: "webhook-response-automation"

    webhook_configuration:
      verification_endpoint: "GET /api/v1/whatsapp"
      message_endpoint: "POST /api/v1/whatsapp"
      signature_validation: "HMAC-SHA256"
      secret_header: "X-Hub-Signature-256"

    message_processing:
      supported_types: ["text", "audio", "image", "pdf"]
      audio_transcription: "faster-whisper integration"
      response_templates: "hardcoded Spanish templates"

    automation_rules:
      - trigger: "intent=disponibilidad"
        action: "query_accommodation_availability"
        response: "template_availability_check"
      - trigger: "intent=precio"
        action: "calculate_pricing"
        response: "template_pricing_info"
      - trigger: "intent=reservar + dates + guests"
        action: "create_prereservation"
        response: "template_prereservation_created"
      - trigger: "audio_message"
        action: "transcribe_and_process"
        response: "template_audio_processed"

    capabilities:
      - "Webhook signature verification"
      - "Media download (audio/images)"
      - "Template-based responses"
      - "Error handling with fallbacks"

    dependencies: ["httpx", "WHATSAPP_ACCESS_TOKEN"]
    llm_usage: false

  - id: "reservation_automation"
    name: "Reservation Business Logic Service"
    type: "transactional-automation"

    business_rules:
      pricing_calculation:
        base_price: "from accommodation.base_price"
        weekend_multiplier: "accommodation.weekend_multiplier (default 1.2)"
        weekend_detection: "saturday=5, sunday=6 weekday()"
        deposit_percentage: 30

      anti_double_booking:
        redis_locks: "lock:acc:{id}:{checkin}:{checkout}"
        lock_ttl: 1800  # 30 minutes
        postgres_constraint: "EXCLUDE USING gist (accommodation_id WITH =, period WITH &&)"

      expiration_logic:
        prereservation_ttl: 30  # minutes
        auto_cancellation: true
        reminder_notifications: true

    state_transitions:
      - from: "initial"
        to: "pre_reserved"
        trigger: "successful_lock_and_insert"
      - from: "pre_reserved"
        to: "confirmed"
        trigger: "payment_received"
      - from: "pre_reserved"
        to: "cancelled"
        trigger: "expiration_or_manual_cancel"

    integration_points:
      - service: "MercadoPago"
        purpose: "payment processing"
        webhook: "/api/v1/mercadopago"
      - service: "EmailService"
        purpose: "confirmation notifications"
      - service: "WhatsAppService"
        purpose: "status updates"

    dependencies: ["Redis", "PostgreSQL", "SQLAlchemy async"]
    llm_usage: false

  - id: "expiration_worker"
    name: "Pre-reservation Expiration Worker"
    type: "background-autonomous-task"

    schedule:
      interval: 300  # seconds (5 minutes)
      execution_method: "asyncio.create_task in lifespan"

    automation_logic:
      batch_processing:
        batch_size: 200
        sql_query: "SELECT WHERE status=pre_reserved AND expires_at < now"
        update_status: "cancelled"

      cleanup_actions:
        redis_lock_release: true
        email_notifications: true
        metrics_increment: "PRERESERVATIONS_EXPIRED counter"

      error_handling:
        strategy: "log_and_continue"
        max_retries: 0
        fallback: "skip_batch"

    observability:
      metrics:
        - "PRERESERVATIONS_EXPIRED (per accommodation)"
        - "PRERESERVATION_EXPIRY_DURATION (histogram)"
        - "PRERESERVATION_REMINDERS_SENT (per channel)"
      logging: "structured with accommodation_id context"

    dependencies: ["SQLAlchemy async", "email_service"]
    llm_usage: false

  - id: "ical_sync_worker"
    name: "iCal Synchronization Worker"
    type: "background-autonomous-task"

    schedule:
      interval: 300  # seconds (5 minutes)
      execution_method: "asyncio.create_task in lifespan"

    sync_logic:
      data_sources:
        - type: "airbnb_ical"
          format: "icalendar RFC5545"
          custom_properties: ["X-CODE", "X-SOURCE"]
        - type: "booking_ical"
          format: "standard icalendar"

      deduplication:
        strategy: "UID + accommodation_id"
        conflict_resolution: "external_source_wins"

      blocking_reservations:
        status: "confirmed"
        source: "external_ical"
        editable: false

    observability:
      metrics:
        - "ICAL_LAST_SYNC_AGE_MIN (gauge, global)"
        - "ICAL_SYNC_AGE_MINUTES (per accommodation)"
        - "ICAL_EVENTS_IMPORTED (counter)"
        - "ICAL_SYNC_ERRORS (counter)"
        - "ICAL_SYNC_DURATION (histogram)"
      health_integration: "contributes to /healthz age check"

    dependencies: ["icalendar", "httpx", "Prometheus"]
    llm_usage: false

  - id: "audio_processor"
    name: "Audio Transcription Processor"
    type: "ai-powered-service"

    ai_configuration:
      model_provider: "OpenAI Whisper (local)"
      model_name: "base"
      language: "es"
      compute_type: "int8"
      device: "cpu"

    processing_pipeline:
      input_formats: ["OGG/Opus", "WAV", "MP3"]
      preprocessing: "convert to WAV 16kHz mono via ffmpeg"
      transcription: "faster-whisper with beam_size=5"
      confidence_calculation: "avg(segment.avg_logprob) normalized"

    quality_control:
      min_confidence: 0.6
      low_confidence_response: "template_audio_unclear"
      error_responses: "template_audio_processing_failed"

    capabilities:
      - "Multi-format audio support"
      - "Quality-based response routing"
      - "Temporary file management"
      - "Error resilience"

    limitations:
      - "No speaker identification"
      - "No custom vocabulary"
      - "No streaming transcription"
      - "Local processing only (no cloud)"

    dependencies: ["faster-whisper", "ffmpeg", "tempfile"]
    llm_usage: "whisper-stt-only"

operational_flows:
  - flow_name: "whatsapp_text_message_processing"
    trigger: "POST /api/v1/whatsapp with text message"
    description: "Process incoming WhatsApp text message end-to-end"

    steps:
      - step: 1
        component: "whatsapp_automation"
        action: "verify_webhook_signature"
        input: "raw webhook payload + X-Hub-Signature-256"
        output: "verified payload or 403 error"
        next_step_condition: "signature_valid"

      - step: 2
        component: "whatsapp_automation"
        action: "parse_whatsapp_payload"
        input: "verified JSON payload"
        output: "normalized message contract"
        next_step_condition: "message_extracted"

      - step: 3
        component: "nlu_service"
        action: "analyze_message_intent"
        input: "message.texto"
        output: "intents, dates, guests"
        next_step_condition: "always"

      - step: 4
        component: "reservation_automation"
        action: "handle_intent_based_action"
        input: "intent + extracted entities"
        output: "business action result"
        next_step_condition: "action_completed"

      - step: 5
        component: "whatsapp_automation"
        action: "send_template_response"
        input: "action result + response template"
        output: "WhatsApp API call"
        next_step_condition: "response_sent"

    error_scenarios:
      - error_type: "invalid_signature"
        handling: "return 403 Forbidden immediately"
        recovery: "log security incident"
      - error_type: "redis_lock_failed"
        handling: "return processing_or_unavailable error"
        recovery: "user can retry later"
      - error_type: "date_overlap_constraint"
        handling: "return date_overlap error template"
        recovery: "suggest alternative dates"

  - flow_name: "audio_message_processing"
    trigger: "POST /api/v1/whatsapp with audio message"
    description: "Transcribe audio and process as text"

    steps:
      - step: 1
        component: "whatsapp_automation"
        action: "download_audio_media"
        input: "media_id from WhatsApp"
        output: "audio file bytes"
        next_step_condition: "download_successful"

      - step: 2
        component: "audio_processor"
        action: "transcribe_audio"
        input: "audio bytes (OGG/Opus)"
        output: "text + confidence score"
        next_step_condition: "confidence >= 0.6"

      - step: 3
        component: "nlu_service"
        action: "analyze_transcribed_text"
        input: "transcription.text"
        output: "intents, dates, guests"
        next_step_condition: "intents_detected"

      - step: 4
        component: "reservation_automation"
        action: "process_audio_derived_intent"
        input: "transcription + NLU results"
        output: "reservation action"
        next_step_condition: "action_completed"

    error_scenarios:
      - error_type: "low_confidence_transcription"
        handling: "send audio_unclear template"
        recovery: "request text message instead"
      - error_type: "transcription_failed"
        handling: "send audio_processing_failed template"
        recovery: "suggest alternative input method"

  - flow_name: "prereservation_expiration_cycle"
    trigger: "Background worker every 300 seconds"
    description: "Automatic cleanup of expired pre-reservations"

    steps:
      - step: 1
        component: "expiration_worker"
        action: "query_expired_prereservations"
        input: "batch_size=200"
        output: "list of expired reservation IDs"
        next_step_condition: "found_expired_reservations"

      - step: 2
        component: "expiration_worker"
        action: "bulk_update_to_cancelled"
        input: "reservation IDs"
        output: "updated rows count"
        next_step_condition: "update_successful"

      - step: 3
        component: "expiration_worker"
        action: "increment_prometheus_metrics"
        input: "accommodation IDs + counts"
        output: "metrics updated"
        next_step_condition: "always"

      - step: 4
        component: "expiration_worker"
        action: "send_expiration_emails"
        input: "reservation details"
        output: "email notifications sent"
        next_step_condition: "always (best effort)"

    error_scenarios:
      - error_type: "database_connection_failed"
        handling: "log error and skip cycle"
        recovery: "next cycle in 300 seconds"
      - error_type: "email_sending_failed"
        handling: "log warning but continue"
        recovery: "user will see status in admin panel"

automation_ecosystem:
  integration_services:
    - service_name: "MercadoPagoService"
      type: "payment_gateway_integration"
      purpose: "Process payments and webhooks"
      used_by_components: ["reservation_automation"]
      implementation:
        language: "Python"
        file: "backend/app/services/mercadopago.py"
        dependencies: ["httpx", "MERCADOPAGO_ACCESS_TOKEN"]
      webhook_validation: "x-signature header verification"

    - service_name: "EmailService"
      type: "notification_service"
      purpose: "Send transactional emails"
      used_by_components: ["expiration_worker", "reservation_automation"]
      implementation:
        language: "Python"
        file: "backend/app/services/email.py"
        dependencies: ["SMTP configuration"]
      templates: ["confirmation.html", "expiration.html", "reminder.html"]

    - service_name: "ICalService"
      type: "calendar_integration"
      purpose: "Import/export calendar events"
      used_by_components: ["ical_sync_worker"]
      implementation:
        language: "Python"
        file: "backend/app/services/ical.py"
        dependencies: ["icalendar", "httpx"]
      custom_properties: ["X-CODE", "X-SOURCE"]

response_template_management:
  storage_location: "hardcoded in services (no template engine yet)"
  localization: "Spanish (Argentina)"
  template_examples:
    availability_response: |
      "✅ ¡Buenas noticias! El alojamiento está disponible para {dates}.
      💰 Precio: ${total_price} ARS ({nights} noches)
      🏠 Capacidad: {capacity} huéspedes
      ¿Te gustaría reservar?"
    prereservation_created: |
      "✅ ¡Pre-reserva creada!
      📋 Código: {code}
      📅 {check_in} al {check_out}
      💰 Total: ${total_price} ARS
      💳 Seña: ${deposit_amount} ARS
      ⏰ Expira en 30 minutos"

performance_characteristics:
  average_response_time: "< 3s for text, < 15s for audio"
  concurrent_processing_limit: "limited by DB connections (10 pool)"
  resource_requirements:
    memory: "< 512MB for API + workers"
    cpu: "< 1 vCPU for normal load"
    storage: "< 1GB for audio processing temp files"
  scalability_constraints:
    - "Single Redis instance (no cluster)"
    - "Single PostgreSQL instance"
    - "No horizontal scaling implemented"
    - "Audio processing CPU-bound"

validation_questions:
  - "¿Los templates de respuesta deberían externalizarse a archivos?"
  - "¿Se necesita soporte para múltiples idiomas además de español?"
  - "¿El flujo de audio debería incluir fallback a texto manual?"
  - "¿Se requiere persistencia de conversaciones para contexto?"
  - "¿Los workers de background necesitan monitoring más granular?"
```

---

## 🚫 PROMPT 3 — INFRAESTRUCTURA RAG DETALLADA (No Implementada)

> **HALLAZGO CRÍTICO:** El sistema NO tiene infraestructura RAG tradicional. Este prompt se adapta para documentar el sistema NLU básico actual.

### ANÁLISIS DE AUSENCIA DE RAG

**INFRAESTRUCTURA RAG ESPERADA vs REALIDAD:**

```yaml
rag_infrastructure_analysis:
  status: "NOT_IMPLEMENTED"
  expected_components:
    vector_stores: ["Pinecone", "Weaviate", "ChromaDB", "FAISS"]
    embedding_models: ["OpenAI embeddings", "SentenceTransformers", "Cohere"]
    retrieval_strategies: ["semantic search", "hybrid search", "reranking"]

  actual_implementation:
    knowledge_base: "NONE - no vector storage"
    document_ingestion: "NONE - no document processing"
    semantic_search: "NONE - keyword matching only"
    contextual_responses: "NONE - template based only"

# DOCUMENTACIÓN DEL SISTEMA NLU BÁSICO ACTUAL (en lugar de RAG)
nlu_basic_infrastructure:
  implementation_type: "rule-based-keyword-matching"

  data_sources:
    - source_id: "hardcoded_patterns"
      type: "regex_patterns"
      location: "backend/app/services/nlu.py"
      format: ["Python regex"]
      total_patterns: 4
      total_size: "< 1KB"
      update_frequency: "manual code changes only"
      access_method: "direct code modification"
      preprocessing_required: ["compile regex on module load"]

  intent_classification:
    method: "keyword_regex_matching"
    patterns:
      disponibilidad:
        regex: "disponib|libre|hay"
        case_sensitive: false
        accuracy: "high for exact matches, zero for variations"
      precio:
        regex: "precio|costo|sale|cuanto"
        case_sensitive: false
        accuracy: "high for exact matches"
      reservar:
        regex: "reserv|apart|tomo"
        case_sensitive: false
        accuracy: "medium (may catch false positives)"
      servicios:
        regex: "servicio|incluye|wifi"
        case_sensitive: false
        accuracy: "medium"

  entity_extraction:
    dates:
      method: "dateparser + regex"
      supported_formats:
        - "DD/MM/YYYY"
        - "DD/MM"
        - "DD-MM-YYYY"
      special_patterns:
        - pattern: "fin de semana|finde"
          behavior: "map to next Saturday-Sunday"
        - pattern: "DD/MM al DD/MM"
          behavior: "extract date range"
      locale_settings:
        date_order: "DMY"
        language: "es"
        timezone: "America/Argentina/Buenos_Aires"
      preprocessing: "normalize separators"

    guest_count:
      pattern: "(\\d+)\\s*(personas?|pax|hu[eé]spedes?)"
      validation: "integer > 0"
      max_supported: 20
      preprocessing: "normalize spacing"

  knowledge_representation:
    format: "hardcoded_conditionals"
    accommodation_data:
      source: "PostgreSQL accommodations table"
      fields_used: ["base_price", "capacity", "amenities", "policies"]
      dynamic_queries: true
      caching: false

    pricing_logic:
      weekend_detection: "Python datetime.weekday() == 5,6"
      multipliers: "accommodation.weekend_multiplier (default 1.2)"
      calculation: "base_price * nights * multiplier"
      currency: "ARS (Argentine Peso)"

  response_generation:
    method: "template_substitution"
    template_engine: "NONE - f-string formatting"
    localization: "hardcoded Spanish"
    personalization: "minimal (name substitution only)"

    template_examples:
      availability_check: |
        f"Verificando disponibilidad para {guests} huéspedes del {check_in} al {check_out}..."
      price_quote: |
        f"El precio para {nights} noches es ${total_price} ARS (incluye seña del {deposit_percentage}%)"
      error_no_availability: |
        f"Lo siento, no hay disponibilidad para esas fechas. ¿Te interesan otras fechas?"

  limitations_identified:
    knowledge_base:
      - "No semantic understanding of variations"
      - "No learning from user interactions"
      - "No contextual conversation memory"
      - "No support for complex queries"
      - "No multilingual support"

    entity_extraction:
      - "Limited date format support"
      - "No relative date parsing (próximo mes, etc.)"
      - "No location entity extraction"
      - "No duration parsing (3 noches)"

    response_generation:
      - "No natural language generation"
      - "No conversation context maintenance"
      - "No adaptive responses based on user behavior"
      - "No A/B testing of response effectiveness"

# GAP ANALYSIS: Current vs RAG-Enabled System
gap_analysis:
  current_capabilities:
    intent_detection: "basic_keyword_matching"
    entity_extraction: "regex_patterns"
    response_generation: "static_templates"
    knowledge_access: "direct_database_queries"

  rag_enabled_capabilities:
    intent_detection: "transformer_based_classification"
    entity_extraction: "ner_models + context"
    response_generation: "llm_with_retrieved_context"
    knowledge_access: "semantic_search_over_embeddings"

  upgrade_pathway:
    phase_1_minimal_rag:
      - "Add sentence-transformers for accommodation descriptions"
      - "ChromaDB for local vector storage"
      - "Simple semantic search for amenities queries"
      - "Maintain existing regex fallbacks"

    phase_2_full_rag:
      - "OpenAI/Anthropic LLM integration"
      - "Vector storage of policies, local attractions, FAQs"
      - "Conversation memory with embeddings"
      - "Dynamic response generation"

    phase_3_advanced:
      - "Multi-modal RAG (images of accommodations)"
      - "Real-time web search integration"
      - "Personalized recommendations based on history"
      - "Multi-language support"

data_flow_current_vs_rag:
  current_flow:
    input: "WhatsApp text message"
    processing:
      - "regex.search() for each intent pattern"
      - "dateparser.parse() for date extraction"
      - "re.search() for guest count"
      - "if/else routing to templates"
    output: "static template with variable substitution"

  rag_enabled_flow:
    input: "WhatsApp text message"
    processing:
      - "encode message to embeddings"
      - "vector similarity search in knowledge base"
      - "retrieve relevant accommodation info, policies, FAQs"
      - "LLM prompt with retrieved context"
      - "generate contextual response"
    output: "dynamic, context-aware natural language response"

implementation_recommendations:
  immediate_improvements:
    - "Externalize regex patterns to configuration file"
    - "Add more date format patterns (Mañana, Hoy, Próximo fin de semana)"
    - "Implement conversation state tracking in Redis"
    - "Add response templates for more scenarios"

  rag_migration_plan:
    dependencies:
      - "Choose LLM provider (OpenAI GPT-4, Anthropic Claude, local Llama)"
      - "Select vector database (Pinecone SaaS, ChromaDB local, PostgreSQL pgvector)"
      - "Define knowledge corpus (accommodations, policies, local area guide)"

    implementation_phases:
      week_1: "Set up vector database and embedding pipeline"
      week_2: "Ingest accommodation data and create embeddings"
      week_3: "Implement hybrid search (keyword + semantic)"
      week_4: "LLM integration with retrieved context"
      week_5: "A/B testing framework and evaluation metrics"

missing_information:
  - "¿Existe presupuesto para LLM API calls (GPT-4, Claude)?"
  - "¿Se requiere on-premise LLM por privacy/regulaciones?"
  - "¿Qué información específica debería incluirse en knowledge base?"
  - "¿Se necesita soporte multiidioma (inglés, portugués)?"
  - "¿Existe data histórica de conversaciones para training?"
  - "¿Qué métricas de éxito se usarían para evaluar RAG vs sistema actual?"
```

---

## 📜 PROMPT 4 — SCRIPTS Y AUTOMATIZACIÓN

### INVENTARIO EXHAUSTIVO DE SCRIPTS

**ANÁLISIS DETALLADO:**

```yaml
scripts_by_category:
  setup:
    - script_path: "scripts/generate_production_secrets.sh"
      language: "bash"
      purpose: "Generate secure random secrets for production environment"
      usage: "./scripts/generate_production_secrets.sh"
      parameters:
        - name: "domain"
          type: "string"
          required: false
          description: "Domain name for SSL and JWT configuration"
      dependencies:
        external: ["openssl", "pwgen"]
        internal: []
      execution_context:
        working_directory: "project_root"
        environment_variables: ["none"]
      examples:
        - command: "./scripts/generate_production_secrets.sh example.com"
          description: "Generate .env.production with secure secrets for example.com"

    - script_path: "setup_ngrok.sh"
      language: "bash"
      purpose: "Configure ngrok tunnel for WhatsApp webhook development"
      usage: "./setup_ngrok.sh"
      parameters: []
      dependencies:
        external: ["ngrok", "jq"]
        internal: []
      execution_context:
        working_directory: "project_root"
        environment_variables: ["NGROK_AUTH_TOKEN"]
      examples:
        - command: "./setup_ngrok.sh"
          description: "Start ngrok tunnel and update webhook URLs"

    - script_path: "scripts/setup_whatsapp_quick.sh"
      language: "bash"
      purpose: "Interactive WhatsApp Business API configuration wizard"
      usage: "./scripts/setup_whatsapp_quick.sh"
      parameters: []
      dependencies:
        external: ["curl", "jq"]
        internal: []
      execution_context:
        working_directory: "project_root"
        environment_variables: ["WHATSAPP_ACCESS_TOKEN"]
      examples:
        - command: "./scripts/setup_whatsapp_quick.sh"
          description: "Configure WhatsApp webhook and verify connection"

    - script_path: "scripts/setup_mercadopago_quick.sh"
      language: "bash"
      purpose: "Interactive Mercado Pago payment integration setup"
      usage: "./scripts/setup_mercadopago_quick.sh"
      parameters: []
      dependencies:
        external: ["curl", "jq"]
        internal: []
      execution_context:
        working_directory: "project_root"
        environment_variables: ["MERCADOPAGO_ACCESS_TOKEN"]
      examples:
        - command: "./scripts/setup_mercadopago_quick.sh"
          description: "Configure Mercado Pago webhooks and test payment flow"

    - script_path: "scripts/setup_ssl.sh"
      language: "bash"
      purpose: "Automated SSL certificate setup with Let's Encrypt"
      usage: "./scripts/setup_ssl.sh <domain>"
      parameters:
        - name: "domain"
          type: "string"
          required: true
          description: "Domain name for SSL certificate"
      dependencies:
        external: ["certbot", "nginx"]
        internal: []
      execution_context:
        working_directory: "project_root"
        environment_variables: ["DOMAIN"]
      examples:
        - command: "./scripts/setup_ssl.sh mydomain.com"
          description: "Generate SSL certificate and configure nginx"

  development:
    - script_path: "backend/start.sh"
      language: "bash"
      purpose: "Start development environment with hot reload"
      usage: "cd backend && ./start.sh"
      parameters:
        - name: "mode"
          type: "string"
          required: false
          description: "dev|prod mode (default: dev)"
      dependencies:
        external: ["uvicorn", "docker-compose"]
        internal: ["requirements.txt"]
      execution_context:
        working_directory: "backend/"
        environment_variables: ["ENVIRONMENT", "DATABASE_URL"]
      examples:
        - command: "cd backend && ./start.sh"
          description: "Start API with uvicorn --reload"
        - command: "cd backend && ./start.sh prod"
          description: "Start with gunicorn for production testing"

    - script_path: "backend/generate_nginx_conf.sh"
      language: "bash"
      purpose: "Generate nginx configuration from template"
      usage: "cd backend && ./generate_nginx_conf.sh"
      parameters: []
      dependencies:
        external: ["envsubst"]
        internal: ["nginx.conf.template"]
      execution_context:
        working_directory: "backend/"
        environment_variables: ["DOMAIN", "BASE_URL"]
      examples:
        - command: "cd backend && ./generate_nginx_conf.sh"
          description: "Generate nginx.conf from template with environment variables"

  testing:
    - script_path: "test_anti_double_booking.sh"
      language: "bash"
      purpose: "Critical test for concurrent reservation prevention"
      usage: "./test_anti_double_booking.sh"
      parameters: []
      dependencies:
        external: ["curl", "jq", "parallel"]
        internal: ["API running on localhost:8000"]
      execution_context:
        working_directory: "project_root"
        environment_variables: ["API_BASE_URL"]
      examples:
        - command: "./test_anti_double_booking.sh"
          description: "Simulate concurrent reservations to test PostgreSQL constraint"

    - script_path: "test_constraint_specific.sh"
      language: "bash"
      purpose: "Test specific PostgreSQL constraint scenarios"
      usage: "./test_constraint_specific.sh"
      parameters: []
      dependencies:
        external: ["psql", "curl"]
        internal: []
      execution_context:
        working_directory: "project_root"
        environment_variables: ["DATABASE_URL"]
      examples:
        - command: "./test_constraint_specific.sh"
          description: "Test daterange overlap constraint with edge cases"

    - script_path: "test_end_to_end.sh"
      language: "bash"
      purpose: "Complete user journey testing (WhatsApp → Payment → Confirmation)"
      usage: "./test_end_to_end.sh"
      parameters:
        - name: "phone"
          type: "string"
          required: false
          description: "WhatsApp phone number for testing"
      dependencies:
        external: ["curl", "jq"]
        internal: ["all services running"]
      execution_context:
        working_directory: "project_root"
        environment_variables: ["WHATSAPP_ACCESS_TOKEN", "MERCADOPAGO_ACCESS_TOKEN"]
      examples:
        - command: "./test_end_to_end.sh +5491123456789"
          description: "Test complete reservation flow for specified phone"

    - script_path: "test_idempotency.sh"
      language: "bash"
      purpose: "Test idempotency of webhook processing"
      usage: "./test_idempotency.sh"
      parameters: []
      dependencies:
        external: ["curl", "jq"]
        internal: []
      execution_context:
        working_directory: "project_root"
        environment_variables: ["API_BASE_URL"]
      examples:
        - command: "./test_idempotency.sh"
          description: "Send duplicate webhooks and verify no double processing"

    - script_path: "test_mercadopago.sh"
      language: "bash"
      purpose: "Test Mercado Pago webhook signature validation"
      usage: "./test_mercadopago.sh"
      parameters: []
      dependencies:
        external: ["curl", "openssl"]
        internal: []
      execution_context:
        working_directory: "project_root"
        environment_variables: ["MERCADOPAGO_WEBHOOK_SECRET"]
      examples:
        - command: "./test_mercadopago.sh"
          description: "Test webhook signature validation with valid/invalid signatures"

    - script_path: "test_whatsapp_webhook.sh"
      language: "bash"
      purpose: "Test WhatsApp webhook signature validation"
      usage: "./test_whatsapp_webhook.sh"
      parameters: []
      dependencies:
        external: ["curl", "openssl"]
        internal: []
      execution_context:
        working_directory: "project_root"
        environment_variables: ["WHATSAPP_APP_SECRET"]
      examples:
        - command: "./test_whatsapp_webhook.sh"
          description: "Test webhook signature validation with HMAC-SHA256"

    - script_path: "scripts/test-ci-local.sh"
      language: "bash"
      purpose: "Run complete CI pipeline locally before push"
      usage: "./scripts/test-ci-local.sh"
      parameters: []
      dependencies:
        external: ["docker", "pytest", "flake8", "black"]
        internal: ["backend/requirements.txt"]
      execution_context:
        working_directory: "project_root"
        environment_variables: ["CI"]
      examples:
        - command: "./scripts/test-ci-local.sh"
          description: "Run full CI pipeline (lint, format, test) locally"

  deployment:
    - script_path: "scripts/deploy_quick.sh"
      language: "bash"
      purpose: "Quick production deployment with safety checks"
      usage: "./scripts/deploy_quick.sh"
      parameters: []
      dependencies:
        external: ["docker-compose", "envsubst"]
        internal: [".env.production"]
      execution_context:
        working_directory: "project_root"
        environment_variables: ["DOMAIN", "all production secrets"]
      examples:
        - command: "./scripts/deploy_quick.sh"
          description: "Deploy to production with automated checks and rollback"

    - script_path: "backend/deploy.sh"
      language: "bash"
      purpose: "Backend-specific deployment script"
      usage: "cd backend && ./deploy.sh"
      parameters:
        - name: "environment"
          type: "string"
          required: false
          description: "staging|production (default: staging)"
      dependencies:
        external: ["docker", "alembic"]
        internal: []
      execution_context:
        working_directory: "backend/"
        environment_variables: ["DATABASE_URL", "REDIS_URL"]
      examples:
        - command: "cd backend && ./deploy.sh production"
          description: "Deploy backend to production environment"

    - script_path: "scripts/pre-deploy-check.sh"
      language: "bash"
      purpose: "Comprehensive pre-deployment validation"
      usage: "./scripts/pre-deploy-check.sh"
      parameters: []
      dependencies:
        external: ["docker", "psql", "redis-cli"]
        internal: ["all configuration files"]
      execution_context:
        working_directory: "project_root"
        environment_variables: ["all required environment variables"]
      examples:
        - command: "./scripts/pre-deploy-check.sh"
          description: "Validate configuration, dependencies, and services before deploy"

    - script_path: "scripts/smoke-test-prod.sh"
      language: "bash"
      purpose: "Post-deployment smoke testing"
      usage: "./scripts/smoke-test-prod.sh <domain>"
      parameters:
        - name: "domain"
          type: "string"
          required: true
          description: "Production domain to test"
      dependencies:
        external: ["curl", "jq"]
        internal: []
      execution_context:
        working_directory: "project_root"
        environment_variables: ["none"]
      examples:
        - command: "./scripts/smoke-test-prod.sh mydomain.com"
          description: "Test critical endpoints on production domain"

  rag_operations:
    # NO HAY SCRIPTS RAG - Sistema no implementa RAG
    - note: "No RAG scripts found - system uses basic NLU"

  maintenance:
    - script_path: "scripts/post-deploy-verify.sh"
      language: "bash"
      purpose: "Verify deployment success and system health"
      usage: "./scripts/post-deploy-verify.sh"
      parameters: []
      dependencies:
        external: ["curl", "jq", "docker"]
        internal: []
      execution_context:
        working_directory: "project_root"
        environment_variables: ["BASE_URL"]
      examples:
        - command: "./scripts/post-deploy-verify.sh"
          description: "Check all services are healthy after deployment"

    - script_path: "scripts/production-checklist.sh"
      language: "bash"
      purpose: "Production readiness checklist validation"
      usage: "./scripts/production-checklist.sh"
      parameters: []
      dependencies:
        external: ["docker", "ssl-cert-check"]
        internal: []
      execution_context:
        working_directory: "project_root"
        environment_variables: ["all production variables"]
      examples:
        - command: "./scripts/production-checklist.sh"
          description: "Validate production configuration and security"

    - script_path: "scripts/quick_validation.sh"
      language: "bash"
      purpose: "Quick system validation after changes"
      usage: "./scripts/quick_validation.sh"
      parameters: []
      dependencies:
        external: ["curl", "jq"]
        internal: ["API running"]
      execution_context:
        working_directory: "project_root"
        environment_variables: ["API_BASE_URL"]
      examples:
        - command: "./scripts/quick_validation.sh"
          description: "Quick health check of critical system components"

command_overlay:
  canonical_commands:
    setup: "make install && make migrate"
    run: "make up"
    test: "make test"
    build: "docker-compose build"
    deploy: "./scripts/deploy_quick.sh"
    clean: "make clean"

  makefile_integration:
    total_commands: 45
    categories:
      - "Setup (5 commands)"
      - "Testing (8 commands)"
      - "Development (10 commands)"
      - "Database (6 commands)"
      - "Code Quality (6 commands)"
      - "Deployment (5 commands)"
      - "Monitoring (5 commands)"

    key_commands:
      "make test": "cd backend && pytest tests/ -v"
      "make test-e2e": "./test_end_to_end.sh"
      "make deploy": "./scripts/deploy_quick.sh"
      "make smoke-test": "./scripts/smoke-test-prod.sh"
      "make pre-deploy-check": "./scripts/pre-deploy-check.sh"
      "make backup": "docker-compose exec postgres pg_dump..."
      "make logs": "cd backend && docker-compose logs -f"

script_dependencies_graph:
  - script: "scripts/deploy_quick.sh"
    depends_on: ["scripts/pre-deploy-check.sh", ".env.production"]
    used_by: ["make deploy"]

  - script: "scripts/pre-deploy-check.sh"
    depends_on: ["docker-compose.yml", "backend/requirements.txt"]
    used_by: ["scripts/deploy_quick.sh"]

  - script: "test_end_to_end.sh"
    depends_on: ["test_whatsapp_webhook.sh", "test_mercadopago.sh"]
    used_by: ["make test-e2e", "scripts/test-ci-local.sh"]

  - script: "setup_ngrok.sh"
    depends_on: ["scripts/setup_whatsapp_quick.sh"]
    used_by: ["development workflow"]

  - script: "scripts/smoke-test-prod.sh"
    depends_on: ["scripts/post-deploy-verify.sh"]
    used_by: ["scripts/deploy_quick.sh", "make smoke-test"]

automation_intelligence:
  script_orchestration:
    pattern: "makefile_centralized"
    workflow_engine: "GNU Make"
    parallel_execution: "limited (make -j not used)"
    dependency_tracking: "manual in Makefile"

  error_handling:
    strategy: "fail_fast"
    common_pattern: "set -e in bash scripts"
    rollback_capability: "manual (deploy scripts have backup)"
    logging: "stdout with colored output"

  configuration_management:
    environment_detection: "ENVIRONMENT variable"
    secret_injection: "environment variables"
    template_processing: "envsubst for nginx.conf"
    validation: "pre-flight checks in deployment scripts"

critical_scripts_analysis:
  production_impact:
    high:
      - "scripts/deploy_quick.sh"
      - "scripts/pre-deploy-check.sh"
      - "test_anti_double_booking.sh"
    medium:
      - "scripts/smoke-test-prod.sh"
      - "scripts/setup_ssl.sh"
      - "test_end_to_end.sh"
    low:
      - "setup_ngrok.sh"
      - "scripts/quick_validation.sh"

  maintenance_requirements:
    daily: ["scripts/post-deploy-verify.sh"]
    weekly: ["scripts/production-checklist.sh"]
    monthly: ["scripts/setup_ssl.sh (cert renewal)"]
    on_change: ["scripts/pre-deploy-check.sh", "test_anti_double_booking.sh"]

validation_needed:
  - "¿Los scripts de backup automático están implementados?"
  - "¿Existe monitoreo de la salud de scripts críticos?"
  - "¿Los scripts tienen logging estructurado para troubleshooting?"
  - "¿Se necesita paralelización de tests para reducir tiempo de CI?"
  - "¿Los scripts de deployment tienen rollback automático?"
```

---

## 📊 PROMPT 5 — OBSERVABILIDAD Y EVALUACIÓN

### ANÁLISIS EXHAUSTIVO DE INFRAESTRUCTURA DE MONITOREO

```yaml
logging:
  framework: "structlog"
  configuration_file: "backend/app/core/logging.py"

  structured_logging:
    enabled: true
    format: "JSON"
    timestamp_format: "ISO8601"
    fields: ["timestamp", "level", "logger", "message", "request_id"]

  log_levels:
    - level: "DEBUG"
      usage: "Development debugging, detailed SQL queries"
      examples: ["database_query_debug", "redis_connection_debug"]

    - level: "INFO"
      usage: "Normal operational events, business logic flow"
      examples:
        - "pre_reservation_created"
        - "whatsapp_message_received"
        - "payment_webhook_processed"
        - "ical_sync_completed"
        - "http_request"

    - level: "WARNING"
      usage: "Potential issues, fallbacks, degraded performance"
      examples:
        - "rate_limited"
        - "low_confidence_audio"
        - "email_send_failed"
        - "redis_connection_slow"

    - level: "ERROR"
      usage: "Application errors, failed operations"
      examples:
        - "invalid_whatsapp_signature"
        - "database_connection_failed"
        - "payment_processing_error"
        - "audio_transcription_failed"

  log_destinations:
    - destination: "stdout"
      format: "JSON structured"
      retention: "container_lifecycle"

    - destination: "docker_logs"
      format: "JSON via docker logging driver"
      retention: "configurable via docker-compose"

  context_enrichment:
    request_context:
      - "request_id (UUID)"
      - "user_id (phone/email)"
      - "accommodation_id"
      - "reservation_code"
      - "channel_source (whatsapp/admin/api)"

    business_context:
      - "check_in/check_out dates"
      - "total_price"
      - "payment_status"
      - "reservation_status"

  automation_logging:
    - component: "ExpirationWorker"
      log_events:
        - "expire_prereservations_started"
        - "pre_reservations_expired"
        - "expire_prereservations_completed"
      context: ["batch_size", "count", "duration_ms"]

    - component: "ICalSyncWorker"
      log_events:
        - "ical_sync_started"
        - "ical_events_imported"
        - "ical_sync_error"
        - "ical_sync_completed"
      context: ["accommodation_id", "events_count", "source_url"]

    - component: "WhatsAppService"
      log_events:
        - "whatsapp_send_skipped_env"
        - "whatsapp_webhook_received"
        - "whatsapp_message_processed"
      context: ["to_phone", "message_type", "signature_valid"]

monitoring:
  tools: ["Prometheus", "prometheus-fastapi-instrumentator"]

  metrics_collection:
    auto_instrumented:
      - metric: "http_requests_total"
        type: "Counter"
        labels: ["method", "endpoint", "status_code"]
        collection_method: "prometheus-fastapi-instrumentator"

      - metric: "http_request_duration_seconds"
        type: "Histogram"
        labels: ["method", "endpoint"]
        collection_method: "prometheus-fastapi-instrumentator"

      - metric: "http_requests_in_progress"
        type: "Gauge"
        labels: ["method", "endpoint"]
        collection_method: "prometheus-fastapi-instrumentator"

    custom_business_metrics:
      - metric: "NLU_PRE_RESERVE"
        type: "Counter"
        labels: ["action", "source"]
        purpose: "Track NLU to pre-reservation conversion"
        location: "backend/app/metrics.py"

      - metric: "PRERESERVATIONS_EXPIRED"
        type: "Counter"
        labels: ["accommodation_id"]
        purpose: "Track expired pre-reservations by accommodation"
        location: "backend/app/jobs/cleanup.py"

      - metric: "PRERESERVATION_EXPIRY_DURATION"
        type: "Histogram"
        purpose: "Duration of expiration job execution"
        location: "backend/app/jobs/cleanup.py"

      - metric: "PRERESERVATION_REMINDERS_SENT"
        type: "Counter"
        labels: ["channel"]
        purpose: "Track reminder notifications sent"
        location: "backend/app/jobs/cleanup.py"

    ical_sync_metrics:
      - metric: "ICAL_LAST_SYNC_AGE_MIN"
        type: "Gauge"
        purpose: "Global metric for health checks"
        aggregation: "minimum across all accommodations"
        location: "backend/app/metrics.py"

      - metric: "ICAL_SYNC_AGE_MINUTES"
        type: "Gauge"
        labels: ["accommodation_id"]
        purpose: "Per-accommodation sync freshness"
        location: "backend/app/metrics.py"

      - metric: "ICAL_SYNC_ERRORS"
        type: "Counter"
        labels: ["accommodation_id", "error_type"]
        purpose: "Track sync failures by type"
        location: "backend/app/metrics.py"

      - metric: "ICAL_SYNC_DURATION"
        type: "Histogram"
        purpose: "iCal sync job execution time"
        location: "backend/app/metrics.py"

      - metric: "ICAL_EVENTS_IMPORTED"
        type: "Counter"
        labels: ["accommodation_id", "source"]
        purpose: "Track events imported from external calendars"
        location: "backend/app/metrics.py"

  dashboards:
    - name: "NO_DASHBOARDS_IMPLEMENTED"
      platform: "none"
      note: "Metrics exposed on /metrics but no Grafana dashboards"
      recommendation: "Add Grafana container to docker-compose"

  alerting:
    - alert_name: "NO_ALERTING_IMPLEMENTED"
      platform: "none"
      note: "No alerting configured"
      recommendation: "Add Prometheus AlertManager"

  health_monitoring:
    endpoints:
      - endpoint: "/api/v1/healthz"
        purpose: "Comprehensive health check with latencies"
        checks:
          - "Database connection + latency (500ms threshold)"
          - "Redis connection + latency (200ms threshold)"
          - "Disk space (10% threshold)"
          - "Memory usage (placeholder)"
          - "iCal sync age (configurable threshold)"
        response_format: "JSON with status and component details"

      - endpoint: "/api/v1/readyz"
        purpose: "Kubernetes readiness probe"
        checks: ["Basic service availability"]
        response_format: "Simple status"

      - endpoint: "/metrics"
        purpose: "Prometheus metrics exposition"
        format: "Prometheus text format"
        bypass_rate_limiting: true

llm_evaluation:
  status: "NOT_APPLICABLE"
  frameworks: []
  evaluation_datasets: []
  metrics: []

  reasoning: |
    System does not use LLMs for reasoning or generation:
    - NLU is regex-based, not ML-based
    - Responses are template-based, not generated
    - Only AI component is Whisper STT (local)
    - No conversational AI requiring evaluation

  future_considerations:
    if_rag_implemented:
      frameworks: ["RAGAS", "LangSmith", "TruLens"]
      evaluation_metrics:
        - "retrieval_precision"
        - "retrieval_recall"
        - "answer_relevancy"
        - "answer_correctness"
        - "context_precision"
        - "faithfulness"
      datasets:
        - "accommodation_qa_pairs"
        - "booking_conversation_samples"
        - "policy_questions"

    if_conversational_ai:
      metrics:
        - "intent_classification_accuracy"
        - "entity_extraction_f1"
        - "response_appropriateness"
        - "conversation_completion_rate"
        - "user_satisfaction_scores"

audio_transcription_evaluation:
  current_implementation:
    model: "faster-whisper base"
    language: "es (Spanish)"
    quality_control:
      confidence_threshold: 0.6
      confidence_calculation: "avg(segment.avg_logprob) normalized"
      fallback_behavior: "request text input"

  quality_metrics:
    implemented:
      - metric: "transcription_confidence"
        calculation: "average segment confidence scores"
        threshold: 0.6
        action_on_low: "send audio_unclear template"

    missing_but_valuable:
      - metric: "word_error_rate (WER)"
        note: "Would require ground truth transcriptions"
      - metric: "character_error_rate (CER)"
        note: "Would require manual validation dataset"
      - metric: "processing_latency"
        note: "Could track time from audio received to response sent"

  evaluation_challenges:
    - "No ground truth dataset for Spanish hotel domain"
    - "WhatsApp audio quality varies significantly"
    - "Background noise common in voice messages"
    - "Argentina-specific accents and colloquialisms"
    - "No automatic evaluation pipeline"

performance_monitoring:
  response_time_tracking:
    text_messages:
      target: "< 3s P95"
      measurement: "request start to WhatsApp API call"
      current_instrumentation: "http_request_duration_seconds histogram"

    audio_messages:
      target: "< 15s P95"
      measurement: "audio received to transcription complete"
      current_instrumentation: "none (should add custom metric)"

    background_jobs:
      expiration_worker:
        target: "< 60s per cycle"
        measurement: "PRERESERVATION_EXPIRY_DURATION histogram"

      ical_sync_worker:
        target: "< 120s per sync"
        measurement: "ICAL_SYNC_DURATION histogram"

error_tracking:
  error_categorization:
    business_errors:
      - "date_overlap" (expected, handled gracefully)
      - "accommodation_not_found"
      - "invalid_dates"
      - "payment_failed"

    technical_errors:
      - "database_connection_failed"
      - "redis_connection_failed"
      - "whatsapp_api_error"
      - "audio_transcription_failed"

    security_errors:
      - "invalid_whatsapp_signature"
      - "invalid_mercadopago_signature"
      - "rate_limit_exceeded"

  error_handling_patterns:
    graceful_degradation:
      - "Redis unavailable → allow requests but log warning"
      - "Email service down → continue flow but notify admin"
      - "Low audio confidence → request text alternative"

    fail_fast:
      - "Invalid webhook signatures → immediate 403"
      - "Database unavailable → 500 error"
      - "Required environment variables missing → startup failure"

tracing:
  enabled: false
  distributed_tracing: false
  note: |
    No distributed tracing implemented. Current system is monolithic
    with simple request ID correlation. For future microservices
    architecture, consider OpenTelemetry integration.

  request_correlation:
    method: "request_id middleware"
    propagation: "X-Request-ID header"
    logging_integration: "structlog context binding"

cost_tracking:
  enabled: false

  current_costs:
    infrastructure: "self-hosted (Docker Compose)"
    llm_apis: "none (no LLM usage)"
    third_party_apis:
      - "WhatsApp Business API (free tier + usage)"
      - "Mercado Pago (commission per transaction)"

  future_cost_considerations:
    if_llm_integration:
      tracking_needed:
        - "OpenAI API tokens per conversation"
        - "Embedding generation costs"
        - "Vector database storage costs"
      tracking_dimensions: ["user_id", "conversation_id", "model_used"]

operational_runbooks:
  high_error_rate:
    threshold: "> 5% error rate"
    investigation_steps:
      - "Check /metrics for error breakdown"
      - "Check /healthz for component status"
      - "Review recent logs for error patterns"
      - "Verify external service availability"

  slow_response_times:
    threshold: "> 6s P95 response time"
    investigation_steps:
      - "Check database latency in /healthz"
      - "Check Redis latency in /healthz"
      - "Review background job performance"
      - "Check system resources (CPU, memory)"

  failed_background_jobs:
    symptoms: "ICAL_SYNC_ERRORS increasing or stale ICAL_LAST_SYNC_AGE_MIN"
    investigation_steps:
      - "Check external iCal URL availability"
      - "Review ical_sync_worker logs"
      - "Verify network connectivity"
      - "Check accommodation configuration"

missing_observability_components:
  critical:
    - "Grafana dashboards for metrics visualization"
    - "Prometheus AlertManager for alerting"
    - "Log aggregation (ELK stack or similar)"

  important:
    - "Distributed tracing (OpenTelemetry)"
    - "Error tracking service (Sentry)"
    - "Uptime monitoring (external)"

  nice_to_have:
    - "Business intelligence dashboards"
    - "Real user monitoring (RUM)"
    - "A/B testing framework"
```

---

## ⚙️ PROMPT 6 — CONFIGURACIÓN Y DEPLOYMENT

### ANÁLISIS EXHAUSTIVO DE GESTIÓN DE CONFIGURACIÓN

```yaml
configuration_management:
  config_files:
    - file: ".env.template"
      purpose: "Template with all required environment variables"
      format: "KEY=value shell format"
      environment_specific: false
      sections:
        - "Environment (ENVIRONMENT=development/staging/production)"
        - "Database (PostgreSQL connection + pool settings)"
        - "Redis (connection + password)"
        - "WhatsApp Business API (tokens + secrets)"
        - "Mercado Pago (access token + webhook secret)"
        - "Application (JWT, domain, base URL)"
        - "Audio/NLU (whisper model + confidence threshold)"
        - "Security (CORS origins, admin emails)"
        - "Email/SMTP (notifications)"

    - file: ".env"
      purpose: "Runtime environment configuration"
      format: "KEY=value"
      environment_specific: true
      source: "copied from .env.template or .env.production"

    - file: ".env.production"
      purpose: "Production-specific secure configuration"
      format: "KEY=value"
      environment_specific: true
      generation: "scripts/generate_production_secrets.sh"

    - file: "backend/app/core/config.py"
      purpose: "Pydantic settings with validation"
      format: "Python class with field validators"
      environment_specific: false
      features:
        - "Type validation (str, int, bool)"
        - "URL format validation"
        - "Required field enforcement"
        - "Default value generation (secrets.token_urlsafe)"
        - "PostgreSQL URL normalization (asyncpg)"
        - "Redis password injection"

    - file: "docker-compose.yml"
      purpose: "Container orchestration configuration"
      format: "YAML"
      environment_specific: false
      services: ["postgres", "redis", "api", "nginx"]

  environment_variables:
    required:
      - name: "DATABASE_URL"
        description: "PostgreSQL connection string"
        type: "string"
        format: "postgresql+asyncpg://user:pass@host:port/db"
        validation: "Must start with postgresql://"
        example: "postgresql+asyncpg://alojamientos:password@db:5432/alojamientos_db"

      - name: "REDIS_URL"
        description: "Redis connection string"
        type: "string"
        format: "redis://[:password@]host:port/db"
        validation: "Must start with redis://"
        example: "redis://:password@redis:6379/0"

      - name: "WHATSAPP_ACCESS_TOKEN"
        description: "WhatsApp Business Cloud API token"
        type: "secret"
        source: "Meta Developer Console"
        validation: "Required for production"

      - name: "WHATSAPP_APP_SECRET"
        description: "WhatsApp webhook signature verification"
        type: "secret"
        source: "Meta Developer Console"
        validation: "Required for webhook security"

      - name: "MERCADOPAGO_ACCESS_TOKEN"
        description: "Mercado Pago API access token"
        type: "secret"
        source: "Mercado Pago Developer Panel"
        validation: "Required for payment processing"

      - name: "JWT_SECRET"
        description: "JWT token signing secret"
        type: "secret"
        generation: "secrets.token_urlsafe(32)"
        validation: "Must be cryptographically secure"

    optional_with_defaults:
      - name: "ENVIRONMENT"
        description: "Runtime environment"
        type: "string"
        default: "development"
        allowed_values: ["development", "staging", "production"]

      - name: "RATE_LIMIT_REQUESTS"
        description: "Rate limit max requests per window"
        type: "integer"
        default: 60

      - name: "AUDIO_MIN_CONFIDENCE"
        description: "Minimum confidence for audio transcription"
        type: "float"
        default: 0.6
        range: "0.0-1.0"

      - name: "JOB_EXPIRATION_INTERVAL_SECONDS"
        description: "Background job execution interval"
        type: "integer"
        default: 300
        unit: "seconds"

  secrets_management:
    method: "environment-variables"
    rotation_policy: "manual"
    generation_tool: "scripts/generate_production_secrets.sh"
    storage_locations:
      development: ".env (git-ignored)"
      staging: ".env.staging (encrypted)"
      production: ".env.production (server-only)"

    secret_categories:
      api_tokens:
        - "WHATSAPP_ACCESS_TOKEN"
        - "MERCADOPAGO_ACCESS_TOKEN"
        - "SMTP_PASS"

      signing_secrets:
        - "JWT_SECRET"
        - "WHATSAPP_APP_SECRET"
        - "MERCADOPAGO_WEBHOOK_SECRET"
        - "ICS_SALT"

      database_credentials:
        - "POSTGRES_PASSWORD"
        - "REDIS_PASSWORD"

    secret_validation:
      - "No hardcoded secrets in code"
      - "All secrets loaded from environment"
      - "Validation in config.py with pydantic"
      - "Startup failure if required secrets missing"

  multi_environment:
    environments: ["development", "staging", "production"]

    differences:
      development:
        - "SQLite fallback for tests"
        - "CORS allow all origins"
        - "No rate limiting"
        - "Detailed error messages"
        - "API docs exposed (/docs, /redoc)"

      staging:
        - "PostgreSQL required"
        - "Redis required"
        - "Limited CORS origins"
        - "Rate limiting enabled"
        - "API docs exposed"

      production:
        - "All security features enabled"
        - "No API docs exposed"
        - "Strict CORS policy"
        - "Error details hidden"
        - "SSL/TLS enforced"

deployment:
  deployment_method: "docker-compose"

  containerization:
    enabled: true
    dockerfile_location: "backend/Dockerfile"
    base_images:
      - "python:3.12-slim (for API)"
      - "postgres:16-alpine (for database)"
      - "redis:7-alpine (for cache)"
      - "nginx:alpine (for reverse proxy)"
    orchestration: "docker-compose"

    container_architecture:
      api:
        build_context: "backend/"
        ports: ["8000:8000"]
        volumes:
          - "./backend:/app"
          - "/tmp/whatsapp_media:/tmp/whatsapp_media"
          - "/tmp/audio_processing:/tmp/audio_processing"
        dependencies: ["postgres", "redis"]
        health_check: "curl http://localhost:8000/api/v1/readyz"

      postgres:
        image: "postgres:16-alpine"
        ports: [] # No external ports in production
        volumes: ["postgres_data:/var/lib/postgresql/data"]
        environment:
          - "POSTGRES_DB=${DB_NAME}"
          - "POSTGRES_USER=${DB_USER}"
          - "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}"
        health_check: "pg_isready"

      redis:
        image: "redis:7-alpine"
        command: "redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}"
        volumes: ["redis_data:/data"]
        health_check: "redis-cli ping"

      nginx:
        image: "nginx:alpine"
        ports: ["80:80", "443:443"]
        volumes:
          - "./nginx/nginx.conf:/etc/nginx/nginx.conf:ro"
          - "./nginx/ssl:/etc/nginx/ssl:ro"
        dependencies: ["api"]

  ci_cd:
    platform: "GitHub Actions"

    workflows:
      - name: "ci.yml"
        trigger: "push, pull_request"
        steps:
          - "Checkout code"
          - "Setup Python 3.12"
          - "Install dependencies"
          - "Run flake8 linting"
          - "Run black formatting check"
          - "Run pytest with coverage"
          - "Upload coverage reports"

      - name: "deploy-staging.yml"
        trigger: "push to main"
        steps:
          - "Run CI pipeline"
          - "Build Docker images"
          - "Deploy to staging environment"
          - "Run smoke tests"
          - "Notify on Slack"

      - name: "security-scan.yml"
        trigger: "schedule (weekly)"
        steps:
          - "Dependency vulnerability scan"
          - "Docker image security scan"
          - "Secret detection scan"
          - "Generate security report"

    quality_gates:
      - "All tests must pass (37 tests)"
      - "Code coverage > 85%"
      - "No flake8 violations"
      - "Black formatting enforced"
      - "No high-severity security vulnerabilities"

  infrastructure:
    hosting: "self-hosted-docker-compose"
    scaling: "manual"

    resources:
      minimum_requirements:
        memory: "2GB RAM"
        cpu: "2 vCPU"
        storage: "20GB SSD"

      recommended_production:
        memory: "4GB RAM"
        cpu: "4 vCPU"
        storage: "50GB SSD"

    networking:
      internal_networks:
        - "backend (postgres, redis, api)"
        - "frontend (nginx, api)"
      external_access:
        - "HTTP/HTTPS through nginx"
        - "WhatsApp webhooks"
        - "Mercado Pago webhooks"

    ssl_configuration:
      method: "Let's Encrypt via Certbot"
      automation: "scripts/setup_ssl.sh"
      renewal: "Certbot auto-renewal"

  deployment_process:
    automated_script: "scripts/deploy_quick.sh"

    pre_deployment:
      validation_script: "scripts/pre-deploy-check.sh"
      checks:
        - "Configuration file validation"
        - "Secret availability verification"
        - "External service connectivity"
        - "Database migration readiness"
        - "SSL certificate validity"

    deployment_steps:
      1: "Backup current configuration"
      2: "Copy production environment file"
      3: "Stop running containers"
      4: "Pull latest images"
      5: "Start containers with health checks"
      6: "Run database migrations"
      7: "Verify service health"

    post_deployment:
      verification_script: "scripts/smoke-test-prod.sh"
      tests:
        - "Health endpoint connectivity"
        - "Database query execution"
        - "Redis connectivity"
        - "Webhook endpoint availability"
        - "SSL certificate validation"

    rollback_procedure:
      trigger: "Failed smoke tests or manual intervention"
      steps:
        - "Stop new containers"
        - "Restore previous configuration"
        - "Start previous container versions"
        - "Verify system stability"
        - "Alert operations team"

dependencies_installation:
  package_manager: "pip"
  installation_command: "pip install -r requirements.txt"
  lock_file: "requirements.txt"
  dependency_categories:
    web_framework:
      - "fastapi==0.109.0"
      - "uvicorn[standard]==0.27.0"
      - "gunicorn==21.2.0"

    database:
      - "sqlalchemy==2.0.25"
      - "asyncpg==0.29.0"
      - "alembic==1.13.1"

    cache_and_storage:
      - "redis==5.0.1"

    integrations:
      - "httpx==0.26.0"
      - "faster-whisper==0.10.0"
      - "icalendar==5.0.11"

    observability:
      - "prometheus-client==0.20.0"
      - "prometheus-fastapi-instrumentator==6.1.0"
      - "structlog==24.1.0"

    security:
      - "python-jose[cryptography]==3.3.0"
      - "passlib[bcrypt]==1.7.4"

startup_procedures:
  initialization_script: "backend/start.sh"

  startup_sequence:
    1: "Load environment variables"
    2: "Validate configuration with pydantic"
    3: "Connect to PostgreSQL"
    4: "Connect to Redis"
    5: "Run database migrations (if needed)"
    6: "Start background workers (asyncio.create_task)"
    7: "Initialize Prometheus metrics"
    8: "Start FastAPI server"

  health_checks:
    startup_probe: "/api/v1/readyz"
    liveness_probe: "/api/v1/healthz"
    readiness_probe: "/api/v1/readyz"

  startup_time: "< 30 seconds"

  failure_scenarios:
    database_unreachable:
      behavior: "Exit with error code 1"
      retry: "Container restart via Docker"

    redis_unreachable:
      behavior: "Log warning, start in degraded mode"
      retry: "Automatic reconnection attempts"

    missing_secrets:
      behavior: "Exit with validation error"
      retry: "Manual configuration fix required"

environment_promotion:
  development_to_staging:
    trigger: "Manual or on successful CI"
    differences: ["Environment variables", "External service endpoints"]

  staging_to_production:
    trigger: "Manual approval after staging validation"
    differences: ["Production secrets", "SSL configuration", "Performance tuning"]

  configuration_drift_prevention:
    - "All environments use same docker-compose.yml"
    - "Only environment variables differ"
    - "Configuration validation in CI"
    - "Infrastructure as code approach"
```

---

## 📖 PROMPT 7 — GUÍA OPERACIONAL COMPLETA

### RUNBOOK PARA OPERACIONES DIARIAS

```markdown
# Guía Operacional - Sistema MVP Reservas Alojamientos

## Inicio Rápido

### Requisitos Previos
- Docker y Docker Compose instalados
- Git para clonar el repositorio
- Acceso SSH al servidor (producción)
- Variables de entorno configuradas
- Certificados SSL válidos (producción)

### Instalación Inicial
```bash
# 1. Clonar repositorio
git clone https://github.com/eevans-d/SIST_CABANAS_MVP.git
cd SIST_CABANAS_MVP

# 2. Configurar variables de entorno
cp .env.template .env
nano .env  # Completar con valores reales

# 3. Generar secretos para producción (opcional)
./scripts/generate_production_secrets.sh tu-dominio.com

# 4. Levantar servicios
make up

# 5. Ejecutar migraciones
make migrate

# 6. Verificar instalación
make test
curl http://localhost:8000/api/v1/healthz
```

### Configuración Mínima
- **DATABASE_URL**: Conexión a PostgreSQL
- **REDIS_URL**: Conexión a Redis
- **WHATSAPP_ACCESS_TOKEN**: Token de WhatsApp Business API
- **MERCADOPAGO_ACCESS_TOKEN**: Token de Mercado Pago
- **JWT_SECRET**: Secreto para firma de tokens

### Primer Ejecución
```bash
# Desarrollo local
make dev

# Producción
./scripts/deploy_quick.sh
```

## Operaciones Diarias

### Inicio del Sistema
```bash
# Opción 1: Comando make
make up

# Opción 2: Docker Compose directo
cd backend && docker-compose up -d

# Verificar que todos los servicios iniciaron
make ps
```

### Verificación de Salud
```bash
# Health check completo
curl http://localhost:8000/api/v1/healthz | jq

# Health check simple
curl http://localhost:8000/api/v1/readyz

# Verificar métricas Prometheus
curl http://localhost:8000/metrics

# Estado de contenedores
docker-compose ps

# Logs en tiempo real
make logs
```

### Monitoreo Básico
**Qué monitorear:**
- Estado de contenedores (docker-compose ps)
- Latencias de base de datos (< 500ms)
- Latencias de Redis (< 200ms)
- Edad de sincronización iCal (< 20 minutos)
- Tasa de errores (< 5%)
- Espacio en disco (> 10% libre)

**Comandos de monitoreo:**
```bash
# Ver métricas de negocio
curl http://localhost:8000/metrics | grep -E "(prereservations|ical|nlu)"

# Verificar espacio en disco
df -h

# Ver logs de errores recientes
docker-compose logs --tail=100 api | grep ERROR

# Estado de background jobs
docker-compose logs --tail=50 api | grep -E "(expiration_worker|ical_worker)"
```

## Procedimientos Comunes

### Reiniciar Servicios
**Cuándo**: Después de cambios de configuración, actualizaciones

**Reinicio completo:**
```bash
make restart
```

**Reinicio por servicio:**
```bash
docker-compose restart api
docker-compose restart postgres
docker-compose restart redis
docker-compose restart nginx
```

### Ejecutar Migraciones de Base de Datos
**Cuándo**: Después de actualizaciones que incluyan cambios de schema

```bash
# Método 1: Make command
make migrate

# Método 2: Docker directo
docker-compose exec api alembic upgrade head

# Verificar estado de migraciones
docker-compose exec api alembic current
docker-compose exec api alembic history
```

### Backup de Base de Datos
**Cuándo**: Antes de deploys importantes, rutina diaria

```bash
# Backup completo
make backup

# Backup manual con timestamp
docker-compose exec postgres pg_dump -U alojamientos alojamientos_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup con compresión
docker-compose exec postgres pg_dump -U alojamientos -Fc alojamientos_db > backup_$(date +%Y%m%d_%H%M%S).dump
```

### Restaurar Base de Datos
**Cuándo**: Recuperación ante fallas, rollback

```bash
# Restaurar desde backup
docker-compose exec -T postgres psql -U alojamientos alojamientos_db < backup_file.sql

# Restaurar desde dump comprimido
docker-compose exec -T postgres pg_restore -U alojamientos -d alojamientos_db backup_file.dump
```

### Ver y Analizar Logs
**Logs en tiempo real:**
```bash
make logs                    # Todos los servicios
make logs-api               # Solo API
make logs-db                # Solo PostgreSQL
make logs-redis             # Solo Redis
```

**Buscar patrones específicos:**
```bash
# Errores en las últimas 24 horas
docker-compose logs --since=24h api | grep ERROR

# Webhooks de WhatsApp
docker-compose logs api | grep whatsapp_webhook

# Pre-reservas creadas
docker-compose logs api | grep pre_reservation_created

# Jobs de background
docker-compose logs api | grep -E "(expiration_worker|ical_worker)"
```

### Limpiar Espacio en Disco
**Cuándo**: Espacio < 15%, rutina semanal

```bash
# Limpiar contenedores detenidos
docker system prune -f

# Limpiar imágenes no utilizadas
docker image prune -f

# Limpiar volúmenes no utilizados (CUIDADO)
docker volume prune -f

# Limpiar logs de Docker
truncate -s 0 /var/lib/docker/containers/*/*-json.log
```

## Troubleshooting

### Error: API no responde
**Síntomas**: HTTP 500, timeouts, conexión rechazada

**Diagnóstico:**
```bash
# 1. Verificar estado del contenedor
docker-compose ps api

# 2. Ver logs recientes
docker-compose logs --tail=50 api

# 3. Verificar salud de dependencias
curl http://localhost:8000/api/v1/healthz

# 4. Verificar recursos del sistema
docker stats
```

**Soluciones:**
1. Reiniciar servicio: `docker-compose restart api`
2. Verificar configuración: revisar .env
3. Verificar base de datos: `make db-shell`
4. Verificar Redis: `make redis-shell`

### Error: Base de datos no conecta
**Síntomas**: "connection refused", "database does not exist"

**Diagnóstico:**
```bash
# Verificar contenedor de PostgreSQL
docker-compose ps postgres

# Intentar conexión manual
make db-shell

# Ver logs de PostgreSQL
make logs-db
```

**Soluciones:**
1. Verificar variables de entorno (DATABASE_URL, POSTGRES_PASSWORD)
2. Recrear contenedor: `docker-compose up -d --force-recreate postgres`
3. Verificar volumen de datos: `docker volume ls`

### Error: Redis no conecta
**Síntomas**: "connection refused", locks fallan

**Diagnóstico:**
```bash
# Verificar contenedor de Redis
docker-compose ps redis

# Intentar conexión manual
make redis-shell

# Ver logs de Redis
make logs-redis
```

**Soluciones:**
1. Verificar REDIS_PASSWORD en .env
2. Reiniciar Redis: `docker-compose restart redis`
3. El sistema puede funcionar sin Redis (modo degradado)

### Error: Webhooks no llegan
**Síntomas**: WhatsApp/Mercado Pago webhooks fallan

**Diagnóstico:**
```bash
# Verificar logs de webhooks
docker-compose logs api | grep -E "(whatsapp_webhook|mercadopago_webhook)"

# Verificar configuración de nginx
curl -I http://localhost/api/v1/whatsapp

# Verificar SSL en producción
curl -I https://tu-dominio.com/api/v1/whatsapp
```

**Soluciones:**
1. Verificar configuración de URLs en Meta/Mercado Pago
2. Verificar firmas (WHATSAPP_APP_SECRET, MERCADOPAGO_WEBHOOK_SECRET)
3. Verificar nginx y SSL: `./scripts/setup_ssl.sh`
4. Verificar firewall y puertos abiertos

### Performance Issues
**Síntomas**: Respuestas lentas, timeouts

**Diagnóstico:**
```bash
# Verificar latencias en health check
curl http://localhost:8000/api/v1/healthz | jq '.checks'

# Verificar métricas de duración
curl http://localhost:8000/metrics | grep http_request_duration

# Verificar recursos del sistema
docker stats
top
```

**Soluciones:**
1. Verificar queries lentas en PostgreSQL
2. Verificar memoria disponible
3. Optimizar pool de conexiones DB
4. Revisar background jobs (expiration, ical sync)

## Mantenimiento

### Rutinas Diarias
- [ ] Verificar estado de servicios (`make ps`)
- [ ] Revisar logs de errores (`docker-compose logs api | grep ERROR`)
- [ ] Verificar espacio en disco (`df -h`)
- [ ] Backup automático (`make backup`)

### Rutinas Semanales
- [ ] Limpieza de Docker (`docker system prune -f`)
- [ ] Verificar certificados SSL (`./scripts/production-checklist.sh`)
- [ ] Revisar métricas de performance
- [ ] Actualizar dependencias si es necesario

### Rutinas Mensuales
- [ ] Renovación automática SSL (Certbot)
- [ ] Análisis de logs históricos
- [ ] Revisión de seguridad (`./scripts/security-audit.sh`)
- [ ] Planificación de capacidad

### Actualización de Componentes
```bash
# Actualización del código
git pull origin main
make restart

# Actualización de dependencias (cuidado)
cd backend
pip install -r requirements.txt --upgrade
make test

# Actualización de imágenes Docker
docker-compose pull
docker-compose up -d --force-recreate
```

### Backup y Recuperación
**Backup automático diario:**
```bash
# Configurar cron job
crontab -e
# Añadir: 0 2 * * * cd /path/to/project && make backup
```

**Estrategia de backup:**
- Base de datos: Diario, retención 7 días
- Configuración: Semanal, retención 30 días
- Logs: Rotación diaria, retención 7 días

**Proceso de recuperación:**
1. Detener servicios
2. Restaurar base de datos desde backup
3. Verificar configuración
4. Iniciar servicios
5. Verificar salud del sistema

## Referencia Rápida

### Comandos Esenciales
| Comando | Propósito |
|---------|-----------|
| `make up` | Levantar todos los servicios |
| `make down` | Detener todos los servicios |
| `make restart` | Reiniciar servicios |
| `make logs` | Ver logs en tiempo real |
| `make test` | Ejecutar suite de tests |
| `make migrate` | Aplicar migraciones DB |
| `make backup` | Backup de base de datos |
| `make clean` | Limpiar recursos Docker |

### Variables de Entorno Críticas
| Variable | Propósito | Valor Ejemplo |
|----------|-----------|---------------|
| `DATABASE_URL` | Conexión PostgreSQL | `postgresql+asyncpg://...` |
| `REDIS_URL` | Conexión Redis | `redis://:pass@host:6379/0` |
| `WHATSAPP_ACCESS_TOKEN` | API WhatsApp | `EAAG...` |
| `MERCADOPAGO_ACCESS_TOKEN` | API Mercado Pago | `APP_USR-...` |
| `ENVIRONMENT` | Entorno actual | `production` |

### Endpoints Clave
| Endpoint | Propósito |
|----------|-----------|
| `/api/v1/healthz` | Health check completo |
| `/api/v1/readyz` | Readiness probe |
| `/metrics` | Métricas Prometheus |
| `/api/v1/whatsapp` | Webhook WhatsApp |
| `/api/v1/mercadopago` | Webhook Mercado Pago |

## Contactos y Escalamiento
- **Desarrollo**: Ver GitHub Issues
- **Infraestructura**: Administrador del servidor
- **Integraciones**: Soporte WhatsApp Business / Mercado Pago
- **Base de datos**: DBA o administrador de sistema
```

---

## 📚 PROMPT 8 — README Y DOCUMENTACIÓN PÚBLICA

### EVALUACIÓN Y MEJORAS DEL README ACTUAL

**ANÁLISIS DEL README.md EXISTENTE:**

```markdown
# README.md - Análisis y Recomendaciones de Mejora

## 🔍 Estado Actual del README.md

### ✅ Fortalezas Identificadas
- **Badges informativos**: CI, Deploy, Security Scan, licencia
- **Estado del proyecto claro**: "10.0/10 PRODUCTION PERFECT"
- **Funcionalidades bien listadas**: Anti-doble booking, WhatsApp, Mercado Pago
- **Quick Start presente**: Comandos básicos incluidos
- **Stack tecnológico documentado**: FastAPI, PostgreSQL, Redis
- **Enlaces a documentación**: Referencias a archivos específicos

### ❌ Problemas Críticos Detectados

1. **Terminología Incorrecta**:
   - Título usa "Sistema Agéntico" (técnicamente incorrecto)
   - No hay agentes IA reales en el código
   - Confusión entre automatización y agenticidad

2. **Duplicación de Contenido**:
   - Información repetida en múltiples secciones
   - Headers duplicados y malformateados
   - Inconsistencias en formato Markdown

3. **Información Desactualizada**:
   - Referencias a "Fase 3" cuando el proyecto está más avanzado
   - Fechas antiguas (2025-10-02)
   - Links a archivos que pueden no existir

4. **Estructura Confusa**:
   - Falta jerarquía clara de información
   - Mezcla de información técnica y de usuario
   - No hay CTA (Call to Action) claro

### 📝 README.md Mejorado Recomendado

```markdown
# Sistema MVP de Reservas de Alojamientos

> **Automatización completa para reservas de cabañas con WhatsApp, anti-doble-booking y pagos integrados**

[![CI](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/ci.yml/badge.svg)](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/ci.yml)
[![Deploy Staging](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/deploy-staging.yml/badge.svg)](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/deploy-staging.yml)
[![Security Scan](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/security-scan.yml/badge.svg)](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/security-scan.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.109-009688)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## 🎯 ¿Qué Hace Este Sistema?

Sistema completo de **automatización de reservas** que permite:

- 📱 **WhatsApp Business**: Los huéspedes reservan por WhatsApp con procesamiento automático de mensajes de texto y audio
- 🚫 **Anti-Doble-Booking**: Prevención garantizada con locks Redis + constraints PostgreSQL
- 💳 **Pagos Mercado Pago**: Integración completa con webhooks y confirmación automática
- 📅 **Sincronización iCal**: Import/export automático con Airbnb, Booking.com y otros
- 🤖 **NLU Básico**: Detección de intenciones y extracción de fechas/huéspedes
- 📊 **Observabilidad**: Métricas Prometheus, health checks y logs estructurados

---

## 🚀 Quick Start (5 minutos)

### Desarrollo Local

```bash
# 1. Clonar y configurar
git clone https://github.com/eevans-d/SIST_CABANAS_MVP.git
cd SIST_CABANAS_MVP
cp .env.template .env

# 2. Levantar servicios
make up

# 3. Ejecutar migraciones
make migrate

# 4. Verificar funcionamiento
curl http://localhost:8000/api/v1/healthz
# Respuesta esperada: {"status": "healthy", ...}
```

**🌐 Accesos:**
- **API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **Métricas**: http://localhost:8000/metrics

### Deploy a Producción

```bash
# 1. Configurar secretos
./scripts/generate_production_secrets.sh tu-dominio.com

# 2. Deploy automatizado
./scripts/deploy_quick.sh

# 3. Configurar SSL y webhooks
./scripts/setup_ssl.sh tu-dominio.com
./scripts/setup_whatsapp_quick.sh
./scripts/setup_mercadopago_quick.sh
```

📖 **Guía completa**: [PRODUCTION_SETUP.md](docs/PRODUCTION_SETUP.md)

---

## 🏗️ Arquitectura del Sistema

### Stack Tecnológico

**Backend Core:**
- **FastAPI 0.109** - API REST async con documentación automática
- **SQLAlchemy 2.0** - ORM async con soporte para PostgreSQL
- **PostgreSQL 16** - Base de datos con extension btree_gist para constraints geométricos
- **Redis 7** - Cache y locks distribuidos para prevenir race conditions

**Integraciones:**
- **WhatsApp Business Cloud API** - Webhooks con validación HMAC-SHA256
- **Mercado Pago** - Gateway de pagos con webhooks idempotentes
- **Whisper STT** - Transcripción de audio via faster-whisper
- **iCal RFC5545** - Sincronización de calendarios externos

**DevOps:**
- **Docker Compose** - Orquestación de servicios
- **GitHub Actions** - CI/CD con tests automatizados
- **Nginx** - Reverse proxy con SSL/TLS
- **Prometheus** - Métricas y observabilidad

### Componentes Principales

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │   Mercado Pago   │    │   iCal Sources  │
│   Webhooks      │    │   Webhooks       │    │   (Airbnb/Bkng) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Router Layer                        │
│  /whatsapp  │  /mercadopago  │  /admin  │  /ical  │  /health   │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Service Layer                               │
│   NLU Service  │  Reservation Service  │  Payment Service      │
│   Audio STT    │  Email Service       │  iCal Sync Service    │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │    │  Background     │
│   (Data + Locks)│    │  (Cache + RT)   │    │  Workers        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🛡️ Características de Seguridad

### Anti-Doble-Booking Garantizado

```sql
-- Constraint PostgreSQL que impide solapamientos
CREATE EXTENSION btree_gist;
ALTER TABLE reservations
ADD CONSTRAINT no_overlap_reservations
EXCLUDE USING gist (
    accommodation_id WITH =,
    period WITH &&
) WHERE (reservation_status IN ('pre_reserved','confirmed'));
```

**Prevención multicapa:**
1. **Locks Redis**: `lock:acc:{id}:{checkin}:{checkout}` con TTL 30min
2. **PostgreSQL Constraint**: EXCLUDE USING gist con daterange
3. **Race Condition Handling**: IntegrityError → respuesta informativa

### Validación de Webhooks

- **WhatsApp**: HMAC-SHA256 con header `X-Hub-Signature-256`
- **Mercado Pago**: Validación con header `x-signature`
- **Rate Limiting**: Por IP + endpoint con bypass para health checks
- **CORS**: Configuración restrictiva por ambiente

---

## 🧪 Testing y Calidad

### Suite de Tests (37 tests pasando)

```bash
# Tests críticos
./test_anti_double_booking.sh    # Concurrencia de reservas
./test_end_to_end.sh            # Flujo completo WhatsApp→Pago→Confirmación
./test_constraint_specific.sh   # Validación constraints PostgreSQL
./test_idempotency.sh           # Webhooks duplicados
./test_whatsapp_webhook.sh      # Validación firmas HMAC
./test_mercadopago.sh           # Integración pagos

# Tests unitarios
make test                       # Suite completa con pytest
make test-unit                  # Solo tests rápidos (SQLite)
make test-integration           # Tests que requieren PostgreSQL
make test-coverage              # Con reporte de cobertura
```

### Calidad de Código

- **Coverage**: 87% (objetivo: >85%)
- **Linting**: flake8 con max-line-length=100
- **Formatting**: black enforced en CI
- **Type Checking**: mypy (parcial)
- **Security**: Automated vulnerability scanning

---

## 📊 Observabilidad

### Métricas Disponibles

```bash
# Endpoint de métricas Prometheus
curl http://localhost:8000/metrics

# Ejemplos de métricas de negocio:
# - prereservations_expired_total
# - ical_sync_duration_seconds
# - nlu_pre_reserve_total
# - http_request_duration_seconds
```

### Health Checks

```bash
# Health check completo con latencias
curl http://localhost:8000/api/v1/healthz | jq

# Readiness probe para Kubernetes
curl http://localhost:8000/api/v1/readyz
```

**Monitoreo incluye:**
- Latencia DB (threshold: 500ms)
- Latencia Redis (threshold: 200ms)
- Edad sincronización iCal (threshold: 20min)
- Espacio en disco (threshold: 10% libre)

---

## 📚 Documentación

| Documento | Propósito |
|-----------|-----------|
| **[PRODUCTION_SETUP.md](docs/PRODUCTION_SETUP.md)** | Deploy en producción paso a paso |
| **[API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** | Endpoints y payloads |
| **[WHATSAPP_INTEGRATION.md](docs/WHATSAPP_INTEGRATION.md)** | Configuración WhatsApp Business |
| **[MERCADOPAGO_INTEGRATION.md](docs/MERCADOPAGO_INTEGRATION.md)** | Setup de pagos |
| **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** | Solución de problemas comunes |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | Guía para contribuidores |

---

## 🔧 Comandos Útiles

```bash
# Desarrollo
make dev                    # Entorno de desarrollo
make logs                   # Ver logs en tiempo real
make shell                  # Shell del contenedor API
make db-shell              # psql del PostgreSQL
make redis-shell           # redis-cli

# Deployment
make deploy                # Deploy a producción
make pre-deploy-check      # Validaciones pre-deploy
make smoke-test           # Tests post-deploy
make backup               # Backup de base de datos

# Maintenance
make clean                # Limpiar containers/images
make restart              # Reiniciar todos los servicios
make migrate              # Aplicar migraciones DB
```

---

## 🚦 Estado del Proyecto

### ✅ MVP Completado (Octubre 2025)

**Funcionalidades Core:**
- [x] Sistema de reservas con pre-reservas temporales
- [x] Integración WhatsApp con procesamiento de texto y audio
- [x] Pagos Mercado Pago con confirmación automática
- [x] Anti-doble-booking con constraints PostgreSQL
- [x] Sincronización iCal bidireccional
- [x] Jobs de background (expiración, sync, recordatorios)
- [x] Observabilidad completa (métricas, logs, health checks)

**Testing y Calidad:**
- [x] 37 tests automatizados (87% coverage)
- [x] CI/CD con GitHub Actions
- [x] Deploy automatizado con rollback
- [x] Documentación exhaustiva

### 🔄 Roadmap Futuro

**Fase 4 - Robustez Operacional:**
- [ ] Rate limiting observable con métricas detalladas
- [ ] Templates de mensajes contextuales
- [ ] Confirmaciones visuales (PDFs, imágenes)
- [ ] Auto-respuestas mejoradas con contexto
- [ ] Circuit breakers y retry logic

**Consideraciones Futuras:**
- [ ] Migración a agentes IA reales (LangChain + GPT-4)
- [ ] Implementación RAG para respuestas contextuales
- [ ] Multi-tenancy para múltiples propiedades
- [ ] Dashboards de analytics en tiempo real

---

## 🤝 Contribuir

1. **Fork** el repositorio
2. **Crear** rama feature (`git checkout -b feature/mi-mejora`)
3. **Commit** cambios (`git commit -am 'feat: nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/mi-mejora`)
5. **Crear** Pull Request

**Requisitos:**
- Tests pasando (`make test`)
- Formato correcto (`make format-check`)
- Documentación actualizada

---

## 📄 Licencia

[MIT License](LICENSE) - Libre para uso comercial y personal.

---

## 🆘 Soporte

- **🐛 Bugs**: [GitHub Issues](https://github.com/eevans-d/SIST_CABANAS_MVP/issues)
- **💡 Feature Requests**: [GitHub Discussions](https://github.com/eevans-d/SIST_CABANAS_MVP/discussions)
- **📖 Documentación**: [docs/](docs/)
- **🔧 Troubleshooting**: [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## ⭐ Reconocimientos

Este proyecto implementa las mejores prácticas para sistemas de reservas:
- **Prevención doble-booking** inspirada en sistemas de aerolíneas
- **Webhook security** siguiendo estándares de Meta/Facebook
- **Observabilidad** basada en metodologías SRE
- **Testing** con enfoque en casos críticos de negocio

**Desarrollado con ❤️ para la industria de alojamientos turísticos**
```

---

## 📊 RESUMEN EJECUTIVO DE AUDITORÍA

### HALLAZGOS PRINCIPALES

#### ✅ **FORTALEZAS DEL SISTEMA**

1. **Arquitectura Sólida de Automatización**
   - 6 componentes bien organizados con responsabilidades claras
   - Service layer pattern implementado correctamente
   - Background workers autónomos con métricas

2. **Seguridad Robusta**
   - Anti-doble-booking garantizado (PostgreSQL + Redis)
   - Validación de firmas webhooks (HMAC-SHA256)
   - Rate limiting por IP + endpoint
   - Secrets management via environment variables

3. **Observabilidad Excelente**
   - 10 métricas Prometheus custom
   - Health checks con latencias medidas
   - Logging estructurado JSON con contexto
   - 37 tests automatizados (87% coverage)

4. **DevOps Maduro**
   - 36 scripts bash para todo el ciclo de vida
   - CI/CD automatizado con GitHub Actions
   - Deploy seguro con pre-checks y rollback
   - Docker Compose con health checks

#### ❌ **BRECHAS CRÍTICAS IDENTIFICADAS**

1. **Desalineación Terminológica SEVERA**
   - ❌ **"Sistema Agéntico"** es técnicamente INCORRECTO
   - ❌ NO hay agentes IA reales (LangChain, CrewAI, etc.)
   - ❌ NO hay LLM reasoning ni autonomous decision making
   - ❌ NO hay RAG ni vector stores
   - ✅ **Realidad**: Sistema de automatización sofisticado

2. **NLU Limitado**
   - Basado en regex patterns hardcodeados
   - No machine learning ni clasificación inteligente
   - No contexto conversacional ni memoria
   - No soporte multi-idioma

3. **Infraestructura de Observabilidad Incompleta**
   - Falta Grafana dashboards
   - No hay alerting (AlertManager)
   - No hay distributed tracing
   - No hay log aggregation centralizada

#### ⚠️ **RIESGOS IDENTIFICADOS**

| Riesgo | Severidad | Impacto | Mitigación |
|--------|-----------|---------|------------|
| **Terminología Misleading** | Alta | Confusión técnica, expectativas incorrectas | Corregir documentación inmediatamente |
| **NLU Básico** | Media | Limitaciones en comprensión de usuarios | Roadmap a NLU con ML |
| **Single Points of Failure** | Media | Redis/PostgreSQL únicos | Implementar clustering |
| **Falta de Alerting** | Media | Detección tardía de problemas | Añadir Prometheus AlertManager |

### 📊 MATRIZ DE MADUREZ TÉCNICA

| Componente | Madurez | Justificación |
|------------|---------|---------------|
| **Backend Architecture** | ⭐⭐⭐⭐⭐ | Service layer, async/await, type hints |
| **Database Design** | ⭐⭐⭐⭐⭐ | Constraints innovadoras, migraciones |
| **Security** | ⭐⭐⭐⭐⭐ | Webhook validation, rate limiting |
| **Testing** | ⭐⭐⭐⭐⚪ | 87% coverage, tests críticos |
| **DevOps** | ⭐⭐⭐⭐⚪ | Scripts completos, CI/CD |
| **Observability** | ⭐⭐⭐⚪⚪ | Métricas sí, dashboards no |
| **NLU/AI** | ⭐⭐⚪⚪⚪ | Solo regex, no ML |
| **Documentación** | ⭐⭐⭐⭐⚪ | Exhaustiva pero inconsistente |

### 🎯 RECOMENDACIONES PRIORITARIAS

#### **Prioridad 1: URGENTE (1-2 semanas)**

1. **Corregir Terminología**
   ```diff
   - "Sistema Agéntico MVP de Alojamientos"
   + "Sistema de Automatización MVP para Reservas de Alojamientos"
   ```

2. **Actualizar README.md**
   - Remover referencias a "agentes IA"
   - Clarificar que es automatización rule-based
   - Añadir sección de limitaciones

3. **Añadir Disclaimers**
   - En documentación técnica
   - En presentaciones de producto
   - En comunicación con stakeholders

#### **Prioridad 2: ALTA (1-2 meses)**

4. **Implementar Observabilidad Completa**
   - Grafana dashboards para métricas business
   - Prometheus AlertManager con Slack notifications
   - Log aggregation (ELK stack o similar)

5. **Mejorar NLU Básico**
   - Externalizar patterns a configuration files
   - Añadir más formatos de fecha
   - Implementar conversation state tracking

6. **Robustez Operacional**
   - Circuit breakers para servicios externos
   - Retry logic con exponential backoff
   - Health checks más granulares

#### **Prioridad 3: FUTURO (3-6 meses)**

7. **Migración a Agenticidad Real** (Si se requiere)
   - Integrar LangChain + GPT-4/Claude
   - Implementar RAG con ChromaDB/Pinecone
   - Memory persistence y conversation history
   - Multi-agent orchestration

### 💰 ESTIMACIÓN DE ESFUERZO

| Iniciativa | Esfuerzo | Recursos | ROI |
|------------|----------|----------|-----|
| **Corregir Terminología** | 1-2 días | 1 dev | Alto (evita confusión) |
| **Observabilidad Completa** | 1-2 semanas | 1 devops | Alto (operations) |
| **NLU Mejorado** | 2-3 semanas | 1 dev | Medio (UX) |
| **Agenticidad Real** | 2-3 meses | 2-3 devs | TBD (estratégico) |

### ✅ CONCLUSIONES FINALES

**El sistema auditado es:**
- ✅ **Técnicamente sólido** como automatización
- ✅ **Production-ready** con seguridad robusta
- ✅ **Well-architected** con observabilidad parcial
- ❌ **Mal etiquetado** terminológicamente
- ⚠️ **Limitado** en capacidades de NLU/AI

**Recomendación principal:**
Corregir la terminología INMEDIATAMENTE para alinear expectativas con realidad técnica. El sistema es excelente como automatización, pero NO es agéntico en el sentido moderno de AI agents.

**Decision point:**
¿Mantener como automatización sofisticada o invertir en migración a agenticidad real con LLMs?

---

## 🔄 ESTADO FINAL DEL DOCUMENTO

**Fecha de finalización:** 2025-10-10
**Progreso:** PROMPTS 1-8/8 ✅ COMPLETADOS
**Total de páginas:** ~80
**Total de líneas:** ~2,200
**Archivos YAML:** 6 estructurados
**Hallazgos críticos:** 4 identificados
**Recomendaciones:** 7 priorizadas

---

*📋 **AUDITORÍA TÉCNICA COMPLETA FINALIZADA** 📋*

*Este documento proporciona una evaluación exhaustiva del sistema con recomendaciones accionables para stakeholders técnicos y de negocio.*
