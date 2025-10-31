# 🎯 Plan Maestro UX — Administrador + Huéspedes

**Fecha:** 31 de octubre 2025
**Versión:** 1.0
**Estado:** ✅ APROBADO — En ejecución Fase 1

---

## 📊 Objetivos y Métricas Norte

### Administración (Dueño/Operador)
- ⏱️ **Tiempo gestión diaria:** < 15 min/día
- 🚀 **P95 vistas Admin:** < 2s
- 🛡️ **Error rate:** < 1%
- ❌ **Doble-bookings:** 0 (constraint + locks + UX calendario)
- ⚡ **Confirmación pre-reservas:** < 10 min promedio

### Huéspedes
- 💬 **Respuesta inicial WhatsApp:** < 3s (P95)
- 📈 **Conversión a pre-reserva:** > 25%
- 💳 **Conversión a pago (seña):** > 60% de pre-reservas
- 😊 **NPS:** > 65

### Métricas de Producto (Instrumentar)
- **Funnel:** consulta → cotización → pre-reserva → pago → confirmación
- **Tiempos:** por etapa + tasa de abandono
- **P95 y error rate:** por endpoint y por intención NLU
- **Reintentos de pago, expiraciones**

---

## 👥 Personas y Jobs-to-be-Done

### Administrador/Operador
**Necesita:**
- Ver estado del negocio de un vistazo
- Bloquear fechas al vuelo
- Confirmar/cancelar reservas
- Reenviar link de pago
- Detectar problemas (webhooks/MP)
- Salud del sistema clara

### Huésped
**Necesita:**
- Disponibilidad clara
- Precio total transparente y rápido
- Link de pago confiable
- Confirmación al instante
- Facilidad para cambiar/cancelar

---

## 🗺️ Mapa End-to-End (Service Blueprint)

### Frontstage (Huésped/WhatsApp)
```
Mensaje → NLU básica → Cotización → Link de pago → Confirmación → Instrucciones check-in
```

### Backstage (Admin/API/DB)
```
Validación fechas (constraint + locks) → Pre-reserva → MP webhook idempotente →
Update reserva → Notificaciones → iCal sync
```

### Soporte
```
Reintentos de pago (cron) → Reportes webhooks inválidos → Alertas latencia/errores
```

---

## 🏗️ Arquitectura de Experiencia

- **Canal principal huéspedes:** WhatsApp Business (texto + audio)
- **UI Admin:** React 18 + Vite + Tailwind (ya existe en `frontend/admin-dashboard`)
- **Integraciones:** Mercado Pago, iCal (Airbnb/Booking), Redis Locks, Postgres btree_gist

---

## 📅 FASE 1 — UX Admin (3–5 días) ← 🔥 EN CURSO

**Objetivo:** Operación diaria sin fricción, P95 < 2s.

### 1.1 Home KPIs (vista 1-pantalla)
**Componente:** `DashboardHome.tsx`

**Datos a mostrar:**
- **Totales:** reservas confirmadas, pre-reservas activas, canceladas
- **Revenue:** total y del mes
- **Tasa conversión:** pre-reserva → confirmada
- **Últimas 24h:** nuevas reservas, pagos recibidos
- **Indicadores técnicos:** healthz (OK/Degradado), error rate, p95, estado iCal (última sync)

**Comportamiento:**
- Auto-refresh cada 30s
- Skeletons durante carga
- Fallback "degradado" en errores

**Endpoint:**
```
GET /api/v1/admin/dashboard
Response: {
  totals: { confirmed, pre_reserved, cancelled, total_revenue, month_revenue },
  conversion_rate: float,
  last_24h: { new_reservations, payments_received },
  health: { status, db_latency_ms, redis_latency_ms, ical_last_sync_age_minutes },
  performance: { error_rate, p95_latency_ms }
}
```

**Criterios de Aceptación:**
- ✅ Carga inicial < 1.5s (P95)
- ✅ Todos los KPIs con tooltips y timestamps
- ✅ Estado técnico visible (OK, lento, error)

---

### 1.2 Reservas (lista + filtros avanzados)
**Componente:** `ReservationsList.tsx`

**Features:**
- Paginación server-side
- Filtros: status, check_in/check_out range, canal, texto (nombre/teléfono/email)
- Orden por columnas: created_at, check_in, total_price
- Acciones masivas: export CSV, reenviar link pago, cancelar expiradas
- Estados vacíos con CTA

**Endpoint:**
```
GET /api/v1/admin/reservations?page=1&page_size=20&status=pre_reserved&q=juan&sort=-check_in
Response: {
  items: [{ id, code, guest_name, check_in, check_out, status, total_price, ... }],
  pagination: { page, page_size, total, total_pages },
  filters_applied: { status, q, sort }
}
```

**Criterios:**
- ✅ Query params estandarizados
- ✅ P95 < 1.5s con 10k+ registros
- ✅ Validación 422 con mensajes amigables

---

### 1.3 Reserva (detalle)
**Componente:** `ReservationDetail.tsx`

**Features:**
- Datos completos de reserva
- Timeline de eventos: pre-reserva → pago → confirmación → iCal
- Botones: Confirmar / Cancelar / Reenviar Link MP / Editar / Notas
- Logs rápidos: webhooks asociados, intentos de pago, idempotencia

**Endpoints:**
```
GET /api/v1/admin/reservations/{id}
POST /api/v1/admin/reservations/{id}/confirm
POST /api/v1/admin/reservations/{id}/cancel
POST /api/v1/admin/reservations/{id}/resend-payment
```

**Criterios:**
- ✅ Acciones sin recargar (optimistic UI + rollback en error)
- ✅ Cada acción con toast y registro en timeline

---

### 1.4 Calendario (mensual por alojamiento)
**Componente:** `Calendar.tsx`

**Features:**
- Visual de ocupación por mes
- Hover: precio/estado/huésped
- Bloqueos manuales
- Indicadores de overlaps bloqueados (tooltip con razón)
- Navegación mensual
- Quick link: crear pre-reserva

**Endpoint:**
```
GET /api/v1/admin/calendar?accommodation_id=1&year=2025&month=11
Response: {
  days: [{ date, reservations: [{ id, code, guest_name, status, price }], blocked: bool }]
}
```

**Criterios:**
- ✅ Render < 2s con 1 año de datos
- ✅ Marcas visuales back-to-back (checkout = próximo checkin)

---

### 1.5 Webhooks (monitor)
**Componente:** `WebhooksMonitor.tsx`

**Features:**
- Tabla últimos N (WhatsApp/MP)
- Columnas: timestamp, proveedor, tipo, firma válida, latencia, status (200/4xx), intento N
- Filtros: proveedor/tipo/fecha
- KPIs: tasa de falla por proveedor últimas 24h

**Endpoint:**
```
GET /api/v1/admin/webhooks?provider=mercadopago&limit=50
Response: {
  items: [{ id, timestamp, provider, type, signature_valid, latency_ms, status_code, attempt }],
  stats: { total, failed, avg_latency_ms }
}
```

---

### 1.6 Salud/Config
**Componente:** `HealthConfig.tsx`

**Features:**
- Healthz: DB/Redis/iCal
- Métrica: p95, error rate
- Versión backend
- CORS allowlist visible/editable
- Export JSON config

**Endpoint:**
```
GET /api/v1/admin/health
Response: {
  status: "healthy|degraded|unhealthy",
  checks: { database: {}, redis: {}, ical: {} },
  performance: { p95_ms, error_rate },
  version: "1.0.0",
  cors: ["https://..."]
}
```

---

## 🚀 Acciones de Implementación Fase 1

### Backend (FastAPI)
1. **Crear router:** `app/routers/admin.py`
   - Decoradores con `dependencies=[Depends(verify_admin_jwt)]`
   - Endpoints: dashboard, reservations (list/detail/actions), calendar, webhooks, health

2. **Schemas consistentes:**
   - `PaginatedResponse[T]` genérico
   - `ErrorResponse` uniforme: `{code, message, details, trace_id}`
   - DTOs de admin con campos calculados (revenue, conversion_rate)

3. **Services:**
   - `AdminDashboardService` con agregaciones SQL optimizadas
   - `ReservationAdminService` con filtros dinámicos y paginación
   - `WebhookLogService` para historial y stats

4. **Permisos:**
   - JWT con scope `admin`
   - Middleware de autorización

### Frontend (React + Vite)
1. **Layout:** `AdminLayout.tsx`
   - Sidebar con navegación
   - Header con user info y notificaciones
   - Toast container global

2. **Vistas:**
   - `pages/Dashboard.tsx` (Home KPIs)
   - `pages/Reservations.tsx` (lista)
   - `pages/ReservationDetail.tsx`
   - `pages/Calendar.tsx`
   - `pages/Webhooks.tsx`
   - `pages/Health.tsx`

3. **Componentes reusables:**
   - `KPICard.tsx` (con skeleton)
   - `DataTable.tsx` (paginación + filtros)
   - `Timeline.tsx` (eventos)
   - `StatusBadge.tsx`
   - `ActionButton.tsx` (con loading + confirm)

4. **State management:**
   - React Query para fetching y cache
   - Context API para auth/user
   - Optimistic updates con rollback

5. **API client:**
   - Axios con interceptors (auth, error handling)
   - Base URL configurable (`VITE_API_URL`)

---

## 📅 FASE 2 — UX Huésped (WhatsApp-first) (3–5 días)

**Objetivo:** Respuesta instantánea, claridad total, confianza y conversión.

### 2.1 Conversación guiada por estados
**Estados:** disponibilidad → cotización → pre-reserva → pago → confirmación → check-in

**Flujos:**
1. **Disponibilidad:**
   - Detectar intent + rango fechas (dateparser)
   - Resolver ambigüedad solicitando confirmación de fechas
   - Sugerir alternativas si ocupado

2. **Cotización:**
   - Precio total con desglose (noches base + fines de semana)
   - Políticas (depósito %, cancelación)
   - CTA: "¿Confirmo esta reserva?"

3. **Pre-reserva:**
   - Recolectar: nombre, teléfono/email
   - Mostrar: código único, expiración clara (ej: 24h)
   - Próximo paso: link de pago

4. **Pago:**
   - Generar link Mercado Pago
   - Enviar con CTA + recordatorio de expiración
   - Reintentos automáticos (T-12h, T-2h)

5. **Confirmación:**
   - Voucher simple (texto + código)
   - Políticas check-in/out
   - Contacto

6. **Cambios/Cancelaciones:**
   - Flujos predefinidos y claros
   - Respuestas humanas

### 2.2 Plantillas y tono
- Mensajes cortos, viñetas, emojis discretos
- Variables: `{check_in, check_out, noches, total, depósito, vencimiento}`
- Audio: si confianza STT < umbral → pedir confirmación de texto

### 2.3 Manejo de ambigüedades
- Fechas ambiguas (finde, próximo sábado): confirmar con 2–3 opciones
- Cantidad huéspedes omitida: pedir número antes de cotizar
- Error overlap: sugerir fechas alternativas (siguiente disponibilidad)

### 2.4 Confianza y pruebas sociales
- Mencionar integración con Airbnb/Booking
- Link de pago seguro (Mercado Pago oficial)
- Advertir no compartir códigos

**Criterios de Aceptación:**
- ✅ Respuesta promedio < 3s (P95) para texto
- ✅ 0 links de pago duplicados (idempotencia)
- ✅ Tasa de errores NLU < 5% de conversaciones

**Acciones técnicas:**
- Reforzar regex/keywords NLU según distribución real
- Dateparser con locale es-AR; fallback a confirmaciones guiadas
- Métricas por intención y paso de funnel
- Experimentos A/B en textos (copy)

---

## 📅 FASE 3 — Polish Técnico Transversal (2–3 días)

### 3.1 API y manejo de errores
- Uniformar respuestas: `{code, message, details, trace_id}`
- Mapear overlap a 409 Conflict con mensaje accionable
- 429 con `Retry-After` en rate limit

### 3.2 Observabilidad UX
**Métricas:**
- `reservation_create_total{channel}`
- `reservation_overlap_total{channel}`
- `webhook_signature_invalid_total{provider}`
- `job_duration_seconds{job}`
- `req_latency_seconds_bucket` por ruta (p95 derivada)

**Dashboard Grafana:**
- Panel de UX (funnel + tiempos)
- Panel de health (DB/Redis/iCal)
- Panel de webhooks (firmas/latencia)

### 3.3 Performance
**Presupuestos:**
- P95 < 3s (texto)
- P95 < 15s (audio STT)

**Optimizaciones:**
- `EXPLAIN ANALYZE` en queries de lista/calendario
- Index hints si aplica
- Límites de `page_size` razonables
- Compresión Gzip habilitada

### 3.4 Seguridad/Privacidad
- Validación estricta de firmas (WhatsApp, MP)
- No loggear PII sensible; redactar tokens
- JWT scopes `admin` + expiración corta; refresh vía endpoint protegido
- Rate limit por IP+path; mensajes amigables de bloqueo

### 3.5 Accesibilidad
- Contraste AA
- Navegación teclado
- Roles ARIA
- Soporte responsive móvil/tablet (admin puede gestionar desde teléfono)

---

## 🧪 Experimentos y A/B Tests

### Experimentos propuestos:
1. **Copy de cotización:** "Precio total" vs. "Desglosado"
2. **Recordatorio de pago:** 2h antes vs. 12h antes de expirar
3. **Mensajes con prueba social** vs. neutrales
4. **Botón "Cambiar fechas"** vs. "Ver próximas fechas libres"

**Métricas de éxito:**
- Lift en conversión a pre-reserva y a pago
- Reducción de abandonos en etapa de pago
- Menor tiempo a confirmación

---

## 📋 Roadmap Ejecutable con Entregables

### Semana 1 (Staging + Admin MVP UX)
- ✅ Staging online (Neon + Upstash) ← **PENDIENTE DB URLs**
- 🔄 Home KPIs + Lista de reservas + Detalle + Calendario básico ← **EN CURSO**
- 🔄 Webhooks monitor + Salud
- 🔄 Instrumentación básica y `/metrics`

### Semana 2 (Huésped UX + NLU + Pagos)
- Flujos WhatsApp refinados (plantillas, ambigüedades)
- Reintentos automáticos de pago + recordatorios
- Expiración pre-reserva con mensajes claros
- A/B primer experimento de copy

### Semana 3 (Polish + Observabilidad + Accesibilidad)
- Errores uniformes, OpenAPI ejemplificado
- Dashboard Grafana UX
- Accesibilidad y responsive; carga P95 < 2s Admin
- QA final + checklist Go-Live

---

## ✅ Criterios de Aceptación por Fase

### Fase 1:
- ✅ P95 Admin < 2s
- ✅ Health/metrics OK
- ✅ Calendario usable
- ✅ Sin errores de consola

### Fase 2:
- ✅ Conversación WhatsApp completa hasta confirmación
- ✅ Conversión > benchmarks
- ✅ Errores NLU < 5%

### Fase 3:
- ✅ API sin warnings en Swagger
- ✅ Dashboards integrados
- ✅ A11Y AA
- ✅ P95 cumpliéndose

---

## 📦 Backlog Priorizado (Alto Valor, Bajo Riesgo)

1. Botón "bloquear fecha" en calendario con razón + nota
2. Export CSV de reservas con filtros aplicados
3. Reenviar link de pago desde detalle con 1 clic
4. Aviso preventivo de overlap en creación (antes de intentar)
5. Recordatorios automáticos (T-24h, T-2h) antes de expiración

---

## ⚠️ Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| NLU ambigua en fechas | Alto | Confirmar con opciones de calendario cercano |
| Webhook fallido (MP/WhatsApp) | Alto | Idempotencia + reintentos + monitor con alerta |
| Latencia en picos | Medio | Índices, paginación, límites; cola para audio |
| Doble-booking en concurrencia | Crítico | Constraint DB + locks Redis + tests de concurrencia |

---

## 📊 Métricas de Producto a Instrumentar

### Funnel:
```
consulta → cotización → pre-reserva → pago → confirmación
```

### Tiempos por etapa:
- Consulta → Cotización: P50, P95, P99
- Pre-reserva → Pago: P50, P95, P99
- Pago → Confirmación: P50, P95, P99

### Abandono por etapa:
- % abandono en cotización
- % abandono en pre-reserva (sin link pago)
- % abandono en pago (link no clickeado)

### Por canal:
- WhatsApp vs. Email
- Tasas de conversión por canal
- Tiempos de respuesta por canal

---

**Estado:** 🟢 Plan aprobado, Fase 1 en ejecución
**Próximo checkpoint:** 48 horas (2 de noviembre 2025)
**Owner:** GitHub Copilot + Usuario
**Stakeholders:** Administrador (dueño cabañas), Huéspedes (guests)
