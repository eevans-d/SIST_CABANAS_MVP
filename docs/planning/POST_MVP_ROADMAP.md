# 🚀 Post-MVP Roadmap - Sistema de Automatización de Reservas

**Versión Base:** v1.0.0
**Fecha de Planificación:** 11 de Octubre 2025
**Horizonte:** 6-12 meses post-lanzamiento

---

## 📋 Executive Summary

Este documento define el **roadmap de features post-MVP** priorizadas según:
- **Impacto en el negocio** (ingresos, escalabilidad, UX)
- **Esfuerzo de implementación** (días de desarrollo)
- **Dependencias técnicas** (bloqueantes)
- **Feedback de usuarios** (post-lanzamiento)

---

## 🎯 Principios de Priorización

### Criterios de Evaluación

| Criterio | Peso | Descripción |
|----------|------|-------------|
| **Business Impact** | 40% | Ingresos, retención, escalabilidad |
| **User Demand** | 30% | Solicitudes de usuarios, pain points |
| **Technical Debt** | 20% | Mejoras de arquitectura, performance |
| **Effort** | 10% | Días de desarrollo (inverso: menos días = mejor) |

### Matriz de Priorización

```
                High Impact
                     │
      P1 (Must-Have) │ P2 (Nice-to-Have)
  ───────────────────┼───────────────────
      P3 (Optional)  │ P4 (Defer)
                     │
                Low Impact
            Low Effort → High Effort
```

---

## 🏆 Phase 1: Quick Wins (Mes 1-2)

**Objetivo:** Mejoras de bajo esfuerzo y alto impacto basadas en feedback inicial.

### F1.1: Dashboard Admin con React ⭐⭐⭐⭐⭐

**Prioridad:** P1 (Must-Have)
**Impacto:** 🟢 Alto - Operaciones diarias
**Esfuerzo:** 8-10 días
**Dependencias:** Ninguna

**Descripción:**
SPA con React para administración de reservas, alojamientos y configuración.

**Features:**
- ✅ Login con JWT
- ✅ Dashboard con métricas (reservas, ingresos, ocupación)
- ✅ CRUD de alojamientos (fotos, amenities, precios)
- ✅ Gestión de reservas (aprobar, rechazar, modificar)
- ✅ Calendario de disponibilidad visual
- ✅ Configuración de iCal sources
- ✅ Logs y debugging (mensajes WhatsApp, errores)

**Stack Sugerido:**
```
Frontend: React 18 + TypeScript + Vite
UI: Tailwind CSS + shadcn/ui
State: React Query + Zustand
Charts: Recharts
Calendar: React Big Calendar
```

**API Endpoints Necesarios:**
```
GET    /api/v1/admin/dashboard/stats
GET    /api/v1/admin/reservations?page=1&status=confirmed
PATCH  /api/v1/admin/reservations/:id/status
GET    /api/v1/admin/accommodations
POST   /api/v1/admin/accommodations
PUT    /api/v1/admin/accommodations/:id
DELETE /api/v1/admin/accommodations/:id
GET    /api/v1/admin/logs?level=error&limit=100
```

**Estimación Detallada:**
- Setup proyecto + auth: 1 día
- Dashboard + métricas: 2 días
- CRUD alojamientos: 2 días
- Gestión reservas + calendario: 2 días
- Logs + debugging: 1 día
- Testing + deployment: 2 días

**ROI:** Alto - Reduce tiempo de gestión manual en 80%

---

### F1.2: Notificaciones Asíncronas (Background Tasks) ⭐⭐⭐⭐

**Prioridad:** P1 (Must-Have)
**Impacto:** 🟢 Alto - Performance
**Esfuerzo:** 3-4 días
**Dependencias:** Ninguna

**Descripción:**
Mover envío de notificaciones WhatsApp/Email a background workers para mejorar latencia de APIs.

**Beneficios:**
- P95 texto: 2.4s → **1.5s** (37% mejora)
- P95 audio: 12.3s → **9s** (27% mejora)
- Retry automático de notificaciones fallidas
- No bloquea response al cliente

**Implementación:**
```python
# Opción 1: Celery + Redis
from celery import Celery

celery_app = Celery('tasks', broker='redis://localhost:6379/1')

@celery_app.task(bind=True, max_retries=3)
def send_whatsapp_notification(self, reservation_id: int):
    # ... enviar notificación ...

# Uso
@router.post("/reservations")
async def create_reservation(...):
    # ... crear reserva ...
    send_whatsapp_notification.delay(reservation.id)  # ⚡ Async
    return {"status": "ok"}
```

```python
# Opción 2: FastAPI BackgroundTasks (más simple)
from fastapi import BackgroundTasks

@router.post("/reservations")
async def create_reservation(background_tasks: BackgroundTasks, ...):
    # ... crear reserva ...
    background_tasks.add_task(send_whatsapp_notification, reservation.id)
    return {"status": "ok"}
```

**Recomendación:** Celery para producción (más robusto), BackgroundTasks para MVP+1.

**Estimación:**
- Implementar Celery + Redis: 1 día
- Refactor notification services: 1 día
- Testing + monitoring: 1 día
- Rollout gradual: 1 día

---

### F1.3: Métricas y Alertas (Grafana Dashboards) ⭐⭐⭐⭐

**Prioridad:** P1 (Must-Have)
**Impacto:** 🟢 Alto - Observabilidad
**Esfuerzo:** 2-3 días
**Dependencias:** Prometheus ya configurado

**Descripción:**
Dashboards Grafana con visualizaciones y alertas críticas.

**Dashboards:**

1. **Business Metrics:**
   - Reservas por día/semana/mes
   - Tasa de conversión (pre-reserva → confirmada)
   - Ingresos por canal (WhatsApp, email, admin)
   - Ocupación por alojamiento

2. **Technical Metrics:**
   - P95/P99 latency por endpoint
   - Error rate (4xx, 5xx)
   - Redis/DB connection pool usage
   - Background job health

3. **Integration Health:**
   - WhatsApp API success rate
   - Mercado Pago webhook delivery
   - iCal sync freshness

**Alertas Críticas:**
```yaml
# grafana-alerts.yml
alerts:
  - name: "High Error Rate"
    condition: "error_rate > 5%"
    for: "5m"
    notify: "slack_critical"

  - name: "P95 Latency High"
    condition: "p95_latency > 6s"
    for: "10m"
    notify: "slack_warning"

  - name: "DB Pool Exhausted"
    condition: "sqlalchemy_pool_overflow == max_overflow"
    for: "2m"
    notify: "slack_critical"
```

**Estimación:**
- Setup Grafana + datasources: 0.5 días
- Crear dashboards (3): 1 día
- Configurar alertas: 0.5 días
- Integrar Slack notifications: 0.5 días
- Documentación: 0.5 días

---

## 🚀 Phase 2: Escalabilidad (Mes 3-4)

**Objetivo:** Soportar crecimiento 10x en usuarios y reservas.

### F2.1: Multi-Propiedad Support ⭐⭐⭐⭐⭐

**Prioridad:** P1 (Must-Have)
**Impacto:** 🟢 Alto - Business model
**Esfuerzo:** 12-15 días
**Dependencias:** F1.1 (Dashboard Admin)

**Descripción:**
Permitir múltiples propietarios gestionando sus propios alojamientos.

**Nuevas Entidades:**
```sql
-- Tabla de propietarios
CREATE TABLE owners (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Modificar accommodations
ALTER TABLE accommodations
ADD COLUMN owner_id INTEGER REFERENCES owners(id);

-- Permisos de usuarios
CREATE TABLE user_permissions (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    owner_id INTEGER REFERENCES owners(id),
    role VARCHAR(20) NOT NULL, -- 'admin', 'manager', 'viewer'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_email, owner_id)
);
```

**Features:**
- ✅ Onboarding de nuevos propietarios
- ✅ Dashboard filtrado por propietario
- ✅ Permisos granulares (admin, manager, viewer)
- ✅ Reportes por propietario
- ✅ Configuración de comisiones
- ✅ Payout tracking (futuro)

**Cambios en Backend:**
```python
# Middleware de permisos
@app.middleware("http")
async def owner_permission_check(request: Request, call_next):
    if request.url.path.startswith("/api/v1/admin"):
        user_email = get_user_email_from_jwt(request)
        owner_id = request.path_params.get("owner_id")

        # Verificar permiso
        has_permission = await check_permission(user_email, owner_id)
        if not has_permission:
            raise HTTPException(status_code=403, detail="Forbidden")

    return await call_next(request)

# Queries filtradas
@router.get("/admin/reservations")
async def list_reservations(owner_id: int | None = None, ...):
    # Filtrar por owner_id si no es superadmin
    query = select(Reservation)
    if owner_id:
        query = query.join(Accommodation).where(Accommodation.owner_id == owner_id)
    # ...
```

**Estimación:**
- DB schema + migrations: 1 día
- Backend permissions: 3 días
- API endpoints multi-tenant: 4 días
- Frontend adaptations: 4 días
- Testing: 2 días
- Documentation: 1 día

**ROI:** Muy Alto - Desbloquea modelo de negocio SaaS

---

### F2.2: Horizontal Scaling (Kubernetes) ⭐⭐⭐

**Prioridad:** P2 (Nice-to-Have)
**Impacto:** 🟡 Medio - Solo si >200 RPS
**Esfuerzo:** 8-10 días
**Dependencias:** Métricas de producción

**Trigger:** RPS sostenido > 100 por >1 hora

**Descripción:**
Deployment en Kubernetes con auto-scaling horizontal.

**Componentes:**
```yaml
# k8s/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
spec:
  replicas: 3  # Mínimo 3 para HA
  template:
    spec:
      containers:
      - name: api
        image: backend:latest
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Cambios Necesarios:**
- ✅ Stateless application (ya está)
- ✅ Session storage en Redis (ya está)
- ✅ Health checks robustos (ya está)
- ⚠️ File uploads → S3 (actualmente local)
- ⚠️ Background jobs → dedicado worker pool

**Estimación:**
- K8s manifests + Helm charts: 3 días
- CI/CD pipeline (GitHub Actions → K8s): 2 días
- Migration de file storage a S3: 2 días
- Testing + staging environment: 2 días
- Production rollout: 1 día

---

### F2.3: Caching Inteligente (Redis) ⭐⭐⭐

**Prioridad:** P2 (Nice-to-Have)
**Impacto:** 🟡 Medio - Performance
**Esfuerzo:** 4-5 días
**Dependencias:** Ninguna

**Trigger:** DB query latency P95 > 100ms

**Targets:**
1. **Lista de alojamientos** (GET /accommodations)
   - TTL: 5 minutos
   - Invalidación: On UPDATE/DELETE accommodation

2. **Disponibilidad por fecha** (GET /availability)
   - TTL: 1 minuto
   - Invalidación: On nueva reserva

3. **Configuración de sistema** (settings)
   - TTL: 1 hora
   - Invalidación: Manual

**Implementación:**
```python
from functools import wraps
import json

def cached(ttl: int, key_pattern: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generar cache key
            cache_key = key_pattern.format(**kwargs)

            # Intentar obtener de cache
            redis = await get_redis_pool()
            cached_value = await redis.get(cache_key)

            if cached_value:
                CACHE_HITS.labels(endpoint=func.__name__).inc()
                return json.loads(cached_value)

            # Cache miss - ejecutar función
            CACHE_MISSES.labels(endpoint=func.__name__).inc()
            result = await func(*args, **kwargs)

            # Guardar en cache
            await redis.setex(cache_key, ttl, json.dumps(result))

            return result
        return wrapper
    return decorator

# Uso
@router.get("/accommodations")
@cached(ttl=300, key_pattern="accommodations:list:{owner_id}")
async def list_accommodations(owner_id: int | None = None):
    # ...
```

**Métricas:**
```python
CACHE_HITS = Counter("cache_hits_total", "Cache hits", ["endpoint"])
CACHE_MISSES = Counter("cache_misses_total", "Cache misses", ["endpoint"])
CACHE_HIT_RATIO = Gauge("cache_hit_ratio", "Cache hit ratio (%)", ["endpoint"])
```

**Estimación:**
- Implementar decorador de caching: 1 día
- Aplicar a endpoints críticos: 2 días
- Invalidation logic: 1 día
- Testing + monitoring: 1 día

**ROI:** Medio - 50-80% reducción en DB load

---

## 🤖 Phase 3: AI & Inteligencia (Mes 5-7)

**Objetivo:** Mejorar automatización con LLMs y AI agents.

### F3.1: NLU con LLM (GPT-4) ⭐⭐⭐⭐⭐

**Prioridad:** P1 (Must-Have)
**Impacto:** 🟢 Alto - UX
**Esfuerzo:** 10-12 días
**Dependencias:** Ninguna

**Descripción:**
Reemplazar NLU regex básico con GPT-4 para comprensión natural avanzada.

**Mejoras:**
- ✅ Detección de intenciones complejas
- ✅ Extracción de entidades (fechas, personas, preferencias)
- ✅ Multi-turn conversations (contexto conversacional)
- ✅ Sugerencias proactivas
- ✅ Manejo de ambigüedad

**Arquitectura:**
```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """
Eres un asistente de reservas de alojamientos. Tu trabajo es:
1. Entender la intención del usuario (consultar disponibilidad, reservar, cancelar, etc.)
2. Extraer información relevante (fechas, número de huéspedes, preferencias)
3. Responder de forma amigable y concisa

Formato de respuesta JSON:
{
  "intent": "availability" | "reserve" | "cancel" | "info" | "other",
  "entities": {
    "check_in": "2025-10-20" | null,
    "check_out": "2025-10-22" | null,
    "guests": 2 | null,
    "accommodation_type": "cabaña" | "casa" | null
  },
  "confidence": 0.95,
  "next_action": "check_availability" | "request_info" | "confirm_booking"
}
"""

async def process_message_with_llm(message: str, context: list) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *context,  # Historial conversacional
        {"role": "user", "content": message}
    ]

    response = await client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    return json.loads(response.choices[0].message.content)
```

**Conversación Multi-Turn:**
```python
# Almacenar contexto en Redis
async def get_conversation_context(user_id: str) -> list:
    redis = await get_redis_pool()
    context = await redis.get(f"conversation:{user_id}")
    return json.loads(context) if context else []

async def save_conversation_context(user_id: str, messages: list):
    redis = await get_redis_pool()
    # Guardar últimos 10 mensajes
    await redis.setex(
        f"conversation:{user_id}",
        3600,  # 1 hora TTL
        json.dumps(messages[-10:])
    )

# En webhook WhatsApp
context = await get_conversation_context(user_id)
result = await process_message_with_llm(message_text, context)

# Actualizar contexto
context.append({"role": "user", "content": message_text})
context.append({"role": "assistant", "content": result["response"]})
await save_conversation_context(user_id, context)
```

**Costos Estimados:**
- GPT-4 Turbo: $0.01 / 1K tokens input, $0.03 / 1K tokens output
- Promedio 500 tokens/conversación
- Costo por conversación: ~$0.02
- 1000 conversaciones/día: **$20/día = $600/mes**

**Fallback Strategy:**
```python
try:
    result = await process_message_with_llm(message, context)
except (OpenAIError, TimeoutError) as e:
    logger.warning("llm_fallback_to_regex", error=str(e))
    # Fallback a NLU regex actual
    result = process_message_with_regex(message)
```

**Estimación:**
- Integrar OpenAI SDK: 1 día
- Implementar prompt engineering: 3 días
- Conversation context management: 2 días
- Refactor routers para usar LLM: 2 días
- Fallback logic: 1 día
- Testing (A/B test vs regex): 2 días
- Monitoring + cost tracking: 1 día

**ROI:** Muy Alto - 90% reducción en malentendidos, mejor UX

---

### F3.2: Dynamic Pricing (ML) ⭐⭐⭐

**Prioridad:** P2 (Nice-to-Have)
**Impacto:** 🟡 Medio - Ingresos
**Esfuerzo:** 15-20 días
**Dependencias:** Datos históricos (6+ meses)

**Descripción:**
Precios dinámicos basados en demanda, estacionalidad, eventos, competencia.

**Features:**
- ✅ Predicción de demanda (ocupación esperada)
- ✅ Ajuste de precios automático
- ✅ Sugerencias de precios por fecha
- ✅ A/B testing de estrategias
- ✅ Dashboard de performance

**Modelo ML:**
```python
# Ejemplo simplificado
from sklearn.ensemble import GradientBoostingRegressor

features = [
    "days_until_checkin",      # Anticipación
    "day_of_week",             # Lunes=0, Domingo=6
    "month",                   # 1-12
    "is_holiday",              # Bool
    "is_long_weekend",         # Bool
    "local_events_count",      # Eventos en la zona
    "historical_occupancy",    # Ocupación histórica para fecha
    "competitor_avg_price",    # Precio promedio competencia
    "accommodation_capacity",  # Capacidad del alojamiento
]

target = "optimal_price"  # Precio que maximiza ingresos

model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1)
model.fit(X_train, y_train)

# Predicción
def predict_optimal_price(accommodation_id: int, check_in: date) -> float:
    features = extract_features(accommodation_id, check_in)
    predicted_price = model.predict([features])[0]

    # Aplicar constraints
    base_price = accommodation.base_price
    min_price = base_price * 0.7  # Máximo 30% descuento
    max_price = base_price * 2.0  # Máximo 100% aumento

    return np.clip(predicted_price, min_price, max_price)
```

**Estimación:**
- Data pipeline (históricos): 3 días
- Feature engineering: 4 días
- Model training + evaluation: 4 días
- API integration: 2 días
- Dashboard visualizations: 3 días
- A/B testing framework: 2 días
- Monitoring + retraining: 2 días

**ROI:** Alto (post-datos) - Aumento estimado de ingresos: 15-25%

---

## 📱 Phase 4: Canales y Experiencia (Mes 8-10)

### F4.1: App Móvil Nativa (React Native) ⭐⭐⭐

**Prioridad:** P2 (Nice-to-Have)
**Impacto:** 🟡 Medio - UX
**Esfuerzo:** 20-25 días
**Dependencias:** F2.1 (Multi-propiedad)

**Features:**
- ✅ Login / registro propietarios
- ✅ Dashboard móvil (métricas clave)
- ✅ Notificaciones push (nuevas reservas)
- ✅ Gestión rápida de reservas (aprobar/rechazar)
- ✅ Chat con huéspedes (integrado con WhatsApp)
- ✅ Calendario de ocupación
- ✅ Offline mode (cache local)

**Stack:**
```
Framework: React Native + Expo
State: Redux Toolkit
Navigation: React Navigation
Push: Firebase Cloud Messaging
Storage: AsyncStorage + WatermelonDB (offline)
```

**Estimación:**
- Setup proyecto + auth: 3 días
- UI components: 4 días
- Dashboard + métricas: 3 días
- Gestión reservas: 4 días
- Push notifications: 2 días
- Offline sync: 3 días
- Testing (iOS + Android): 3 días
- App Store / Play Store submission: 3 días

---

### F4.2: Integración con Booking.com API ⭐⭐⭐⭐

**Prioridad:** P1 (Must-Have) - **Si escala**
**Impacto:** 🟢 Alto - Distribución
**Esfuerzo:** 15-18 días
**Dependencias:** Volumen > 50 reservas/mes

**Descripción:**
Sincronización bidireccional con Booking.com para evitar doble-booking y aumentar distribución.

**Features:**
- ✅ Import reservas de Booking.com
- ✅ Export disponibilidad a Booking.com
- ✅ Sincronización de precios
- ✅ Notificaciones de cambios
- ✅ Reconciliación de conflictos

**Arquitectura:**
```
Sistema → Booking API: Disponibilidad, precios
Booking → Sistema: Reservas, cancelaciones
Webhook: Notificaciones en tiempo real
```

**Estimación:**
- Partner agreement con Booking: 3 días
- API integration (read): 4 días
- API integration (write): 4 días
- Conflict resolution logic: 3 días
- Testing + staging: 2 días
- Documentation: 2 días

---

## 📊 Phase 5: Analytics y Reportes (Mes 11-12)

### F5.1: Business Intelligence Dashboard ⭐⭐⭐⭐

**Prioridad:** P1 (Must-Have) - Si multi-propiedad
**Impacto:** 🟢 Alto - Decisiones
**Esfuerzo:** 8-10 días
**Dependencias:** F2.1 (Multi-propiedad), datos > 3 meses

**Features:**
- ✅ Revenue analytics (ingresos por período)
- ✅ Occupancy rate (tasa de ocupación)
- ✅ ADR (Average Daily Rate)
- ✅ RevPAR (Revenue Per Available Room)
- ✅ Channel performance (WhatsApp vs Email vs Directo)
- ✅ Customer LTV (Lifetime Value)
- ✅ Forecasting (predicciones de ingresos)
- ✅ Export a Excel/PDF

**Stack:**
```
Backend: SQL queries + aggregations
Caching: Redis (materialized views)
Frontend: Recharts + Table exports
```

**Estimación:**
- SQL analytics queries: 2 días
- Backend API endpoints: 2 días
- Frontend dashboards: 3 días
- Export functionality: 1 día
- Testing: 1 día
- Documentation: 1 día

---

## 🔒 Security & Compliance

### F6.1: SOC 2 Compliance ⭐⭐

**Prioridad:** P3 (Optional) - Solo si B2B SaaS
**Impacto:** 🟡 Medio - Enterprise clients
**Esfuerzo:** 30-40 días + auditoría externa
**Dependencias:** Security audit completo

**Requerimientos:**
- ✅ Encryption at rest (DB)
- ✅ Encryption in transit (TLS)
- ✅ Audit logs (todas las acciones)
- ✅ Access controls (RBAC)
- ✅ Incident response plan
- ✅ Vulnerability scanning
- ✅ Penetration testing
- ✅ Employee background checks

---

## 📅 Timeline Summary

```
Month 1-2:  Quick Wins (Dashboard, Async, Grafana)
Month 3-4:  Escalabilidad (Multi-propiedad, K8s, Cache)
Month 5-7:  AI (GPT-4 NLU, Dynamic Pricing)
Month 8-10: Canales (App móvil, Booking.com)
Month 11-12: Analytics (BI Dashboard)
```

**Total Effort:** ~150-180 días de desarrollo (~6-7 meses con 1 dev full-time)

---

## 🎯 Success Metrics

| Metric | Baseline (MVP) | Target (Post-MVP) | Timeline |
|--------|---------------|-------------------|----------|
| **Reservas/mes** | 50-100 | 500-1000 | 6 meses |
| **Usuarios concurrentes** | 10-20 | 100-200 | 6 meses |
| **Error rate** | 0.08% | <0.5% | Continuo |
| **P95 latency (texto)** | 2.4s | <2s | 3 meses |
| **NLU accuracy** | 75% (regex) | >95% (GPT-4) | 6 meses |
| **Conversion rate** | 60% | >80% | 6 meses |
| **Customer satisfaction** | TBD | >4.5/5 | 12 meses |

---

## 🚫 Explicitly NOT in Roadmap

Estas features fueron consideradas y **rechazadas** o **diferidas indefinidamente**:

❌ **PMS Integration (Odoo, etc.)** - Ver ADR original, no aporta valor diferencial
❌ **Voice Calls** - Complejidad alta, beneficio bajo vs costo
❌ **Crypto Payments** - Regulación unclear, demanda baja
❌ **Blockchain** - No use case válido para MVP+N
❌ **Video Tours** - Storage costs altos, mejor usar links externos

---

## ✅ Decision Framework

Antes de agregar cualquier feature, preguntar:

1. **¿Resuelve un pain point real de usuarios?** (evidencia cuantitativa)
2. **¿Aumenta ingresos o retención mediblemente?** (proyección ROI)
3. **¿Es técnicamente factible con stack actual?** (no rewrites)
4. **¿Puede mantener 1 desarrollador?** (complejidad aceptable)
5. **¿Se alinea con visión de producto?** (no feature creep)

Si 3+ respuestas son "NO" → **Rechazar feature**

---

**Autor:** GitHub Copilot AI Agent
**Fecha:** 11 de Octubre 2025
**Versión:** 1.0
**Próxima Revisión:** Post-deployment + 3 meses (feedback real de usuarios)
