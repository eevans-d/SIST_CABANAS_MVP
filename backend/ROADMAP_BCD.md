# 📍 Roadmap Post-MVP: Opciones B, C y D (Prioridad Máxima)

Fecha: 27/09/2025
Estado: Aprobado para ejecución inmediata
Horizonte: 10–14 días (2 sprints cortos)

## 🎯 Objetivos
- B) Entregar funcionalidades post-MVP de ALTO IMPACTO sin tocar el schema bloqueado
- C) Optimizar performance y robustez observando SLOs y métricas reales
- D) Implementar suite E2E y pruebas de carga como gates de calidad

## 🧭 Hoja de Ruta (Alta Resolución)

Sprint 1 (Días 1–5)
- B.1 Email notifications (SMTP/IMAP): confirmación, expiración, recordatorio de pago
- B.2 Admin mínimo (read-only + acciones seguras): listado/filtrado reservas, reenvío de emails, export CSV
- D.1 E2E base: levantar stack con docker-compose, datos seed, journeys API principales

Sprint 2 (Días 6–10)
- C.1 Performance/hardening: pool DB, workers, índices, timeouts, límites
- D.2 Webhooks E2E: WhatsApp/MP de punta a punta con firmas, idempotencia, retrys
- D.3 Carga/estrés: escenarios de 50–100 rps en endpoints críticos y locks

Buffer (Días 11–14)
- Fixes puntuales + tuning a partir de métricas, cerrar documentación, checklist de release

---

## 🏗️ Blueprint por Iniciativa

### B) Funcionalidades Post-MVP

B.1 Notificaciones Email (SMTP)
- Servicio: `app/services/email.py` (SMTP + plantillas Jinja2)
- Plantillas: `templates/email/*.html` (confirmación, expiración, recordatorio)
- Disparadores:
  - on_pre_reserve_created → email con código y vencimiento
  - on_confirmed → email de confirmación + datos check-in
  - on_expired → email de expiración (si hay email del huésped)
- Config env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
- Métricas: `email_sent_total{type=...}`, `email_failed_total`
- Tests: unit (mock SMTP) + E2E (assert recibido vía bandeja IMAP opcional/placeholder)

B.2 Admin mínimo (seguro, sin schema nuevo)
- Autenticación: JWT existente (rol admin por env variable lista blanca)
- Endpoints: `/admin/reservations?status&from&to&acc_id`, `/admin/actions/resend-email`, `/admin/export.csv`
- UI ligera: FastAPI + Jinja2/HTMX (sin framework pesado)
- Seguridad: CSRF para POST, rate limit por IP (Nginx), logs estructurados sin PII
- Tests: integración API + snapshot simple de HTML (status 200 y contenidos clave)


### C) Optimización y Hardening

C.1 Performance/Robustez
- App server: gunicorn + uvicorn workers (2–4) -> CPU cores
- Pool DB (asyncpg): tamaño base 15–30, overflow 10, timeouts de 5–10s
- Índices: revisar `reservations(accommodation_id, check_in)` y GIST ya existente (no tocar constraint)
- Nginx: keepalive, timeouts, gzip, límites de request; cache público 1h para iCal
- Redis: latencia P95, ajustar maxmemory-policy (ya LRU) y timeouts de conexión
- Alertas: añadir métricas SLO: p95_reservation_create_seconds, error_rate_total


### D) E2E + Carga

D.1 E2E Base
- Compose test env: `docker-compose -f docker-compose.test.yml`
- Seed: script `scripts/seed.py` (alojamiento demo + precios)
- Journeys:
  - Pre-reserva → Confirmación → iCal export
  - Webhook WhatsApp (texto) → NLU → respuesta
  - Webhook MP (paid) → reserva confirmada

D.2 Webhooks Reales (Mock firmados)
- Reproducción: payloads reales firmados (fixtures)
- Idempotencia: mismo payment_id → no duplica
- Errores: firma inválida → 403, faltantes → 400

D.3 Carga/Estrés
- Herramienta: k6 o Locust (scripts bajo `scripts/load/`)
- Escenarios:
  - 20 → 100 usuarios concurrentes pre-reserva
  - Confirmación simultánea (10–20) sobre misma reserva
  - Webhooks MP/WhatsApp 50 rps (bursts) con rate limit
- Gates: P95 < 3s (texto), < 15s (audio), error rate < 1%

---

## ✅ Checklists

General
- [ ] Variables SMTP configuradas y probadas
- [ ] Jinja2 instalado y templates validados
- [ ] Admin protegido por JWT + whitelist
- [ ] Métricas nuevas visibles en /metrics
- [ ] Logs sin PII (ver máscara)

B.1 Email
- [ ] Envío confirmación
- [ ] Envío expiración
- [ ] Envío recordatorio
- [ ] Retries exponenciales (x3)
- [ ] Test unitarios con mock SMTP

B.2 Admin
- [ ] Listado con filtros
- [ ] Reenvío de email
- [ ] Export CSV
- [ ] CSRF en POST
- [ ] Tests integración API/UI

C.1 Performance
- [ ] gunicorn + uvicorn workers configurados
- [ ] Pool DB ajustado
- [ ] Índices verificados
- [ ] Timeouts Nginx/App ajustados
- [ ] Nuevas métricas de latencia/error

D.1–D.3 E2E/Load
- [ ] docker-compose.test.yml
- [ ] seed de datos
- [ ] journeys E2E
- [ ] scripts k6/Locust
- [ ] Informe P95 + error rate

---

## 📦 Entregables
- Código: `app/services/email.py`, `app/routers/admin.py`, `templates/email/*`
- Config: `.env.template` SMTP_*, `docker-compose.test.yml`
- Tests: `tests_e2e/`, `scripts/load/*.js|py`, fixtures de payloads firmados
- Docs: `docs/POST_MVP.md` con resultados y tuning aplicado

---

## 📐 Criterios de Aceptación
- Emails enviados (3 tipos) con tasa de fallo < 1%
- Admin accesible, seguro, y funcional (listado, reenvío, export)
- SLOs mantenidos en P95 (texto < 3s, audio < 15s)
- E2E verdes (3 journeys) y gates de carga cumplidos

---

## ⚠️ Riesgos y Mitigaciones
- SMTP externo lento → retries + colas simples en Redis (opcional)
- Picos de webhook → rate limit + backoff + idempotencia
- Plantillas mail rotas → previsualización local + tests de snapshot

---

## 🔢 Estimación Gruesa
- B.1: 1.5–2 días
- B.2: 2–3 días
- C.1: 2 días
- D.1–D.3: 3–4 días

Total: 8.5–11 días (incluye buffer)

---

## 🧪 Gates de Calidad (obligatorios)
- Build/Lint: PASS
- Unit/Integration: PASS
- E2E Journeys: PASS
- Carga (k6/Locust): PASS con SLOs
- Security: Sin PII en logs, JWT/CSRF activos

---

## ▶️ Siguiente Paso
- Aprobar roadmap (este documento) y comenzar Sprint 1 con foco en B.1 + B.2 + D.1.
