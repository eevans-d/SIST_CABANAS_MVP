# ✅ Blueprint-Checklist 100% — Desarrollo + UX Admin + Fly.io

Fecha: 2025-10-28
Propósito: Ejecutar, paso a paso, TODO lo necesario para tener el sistema 100% funcional y desplegado en Staging/Producción (Fly.io), con una UX de Administrador completa y robusta.

---

## 📌 Macro-Checklist (panorama)

- [ ] 0. Preparación y Auditoría rápida (30–60 min)
- [ ] 1. Staging en Fly.io (infra + deploy) (0.5–1 día)
- [ ] 2. UX Admin (Home, Reservas, Calendario, Webhooks, Salud/Config) (2–3 días)
- [ ] 3. API Polish (paginación/errores/OpenAPI/JWT scopes/CORS) (1–2 días)
- [ ] 4. Observabilidad + Alertas (1 día)
- [ ] 5. Performance Tuning (0.5–1 día)
- [ ] 6. Seguridad (0.5 día)
- [ ] 7. QA Final (0.5–1 día)
- [ ] 8. Go-Live Producción + Monitoreo 24–48h (0.5 día)

Tiempo total sugerido: 5–7 días (+ buffer 1–2 días)

---

## 0) Preparación y Auditoría (30–60 min)

Checklist
- [ ] Ejecutar pre-check scripts (repo/scripts) y validador 7/7
- [ ] Revisar fly.toml (región eze, health/metrics, workers, strategy)
- [ ] Confirmar Dockerfile backend (puerto 8080, start-fly.sh aplica migraciones)
- [ ] Completar guía de secretos (ops/GUIA_OBTENER_SECRETOS_PASO_A_PASO.md)

Criterios de Aceptación
- [ ] Validación 7/7 PASS
- [ ] `backend/docs/DEPLOYMENT_SUMMARY.md` actualizado y PASS

Dependencias
- Git limpio; Docker/Compose instalados

Referencias
- backend/scripts/validate_predeploy.py
- backend/scripts/generate_deployment_summary.py
- ops/GUIA_OBTENER_SECRETOS_PASO_A_PASO.md

---

## 1) Staging en Fly.io (0.5–1 día)

Checklist
- [ ] Crear app Fly (o verificar existente) — `sist-cabanas-mvp`
- [ ] Proveer Postgres (Fly Postgres o externo) con `btree_gist` activo
- [ ] Proveer Redis (Upstash recomendado) y volcar `REDIS_URL`
- [ ] Cargar secretos desde `env/.env.fly.staging` (script ops)
- [ ] Deploy a Fly y validar healthz/metrics/logs
- [ ] Configurar dominios CORS (ALLOWED_ORIGINS)

Criterios de Aceptación
- [ ] `/api/v1/healthz` y `/metrics` OK en Fly
- [ ] `ops/smoke_and_benchmark.sh` PASS con P95 aceptable
- [ ] `backend/scripts/concurrency_overlap_test.py` PASS (opcional RUN_MUTATING)

Dependencias
- Fase 0 completada; secretos listos; flyctl instalado

Referencias
- fly.toml
- ops/set_fly_secrets.sh
- ops/smoke_and_benchmark.sh
- backend/scripts/concurrency_overlap_test.py

---

## 2) UX Admin (2–3 días)

Objetivo: que el Administrador resuelva su operación diaria con fluidez (P95 < 2s).

Checklist
- [ ] Home (KPIs): totales, confirmadas, pre-reservas, canceladas, revenue total y del mes; auto-refresh 30s; loading/error states
- [ ] Reservas (lista): paginación server-side, filtros (status/fechas/canal), búsqueda (nombre/teléfono/email), orden por columnas, skeletons
- [ ] Reservas (detalle): ver datos completos, transicionar estado (pre→confirm/cancel), reenviar link de pago (si aplica), toasts y confirm dialogs
- [ ] Calendario: vista mensual por alojamiento, tooltip (estado/huésped/precio), navegación mensual, indicador de overlaps bloqueados
- [ ] Webhooks: tabla de últimos N (WhatsApp/MP), firma válida, latencia, estado (200/4xx), filtros por proveedor/tipo/fecha, reintento (si API lo permite)
- [ ] Salud/Config: panel con healthz/metrics parseados (p95/error rate), lectura de CORS y versión backend, export JSON config
- [ ] Accesibilidad y responsive (mobile/tablet/desktop); 0 errores en consola

Criterios de Aceptación
- [ ] P95 vistas Admin < 2s (staging)
- [ ] 0 errores de consola; errores de API con mensajes claros (humano + code)

Dependencias
- Fase 1 lista (API en Staging); `VITE_API_URL` apuntando al backend de Fly

Referencias
- frontend/admin-dashboard/README.md
- Makefile: admin-install/admin-dev/admin-build/admin-preview
- ops/BLUEPRINT_CHECKLIST_OPTIMIZACION_UX.md (enfoque detallado por pantalla)

---

## 3) API Polish (1–2 días)

Checklist
- [ ] Paginación/filtrado/orden unificados: `?page=&page_size=&q=&sort=`
- [ ] Límites y whitelist de sort; validaciones 422 amigables
- [ ] Esquema de errores: `{code, message, details?, trace_id}` en todos los endpoints
- [ ] Mapear `IntegrityError` overlap a 409 con mensaje claro
- [ ] 429 con `Retry-After` acorde al rate limit
- [ ] JWT scopes: `admin` en rutas `/api/v1/admin/*`
- [ ] CORS allowlist (admin UI + dominios staging/prod)
- [ ] OpenAPI: ejemplos, enums descriptivos, tags por módulo

Criterios de Aceptación
- [ ] Swagger UI sin warnings; respuestas uniformes; trazas con `trace_id`
- [ ] P95 endpoints principales < 300ms (staging)

Dependencias
- Modelos/schemas bloqueados; sin cambios de esquema de DB

Referencias
- app/routers/*, app/services/*

---

## 4) Observabilidad + Alertas (1 día)

Checklist
- [ ] Métricas nuevas: `reservation_create_total{channel}`
- [ ] Métricas nuevas: `reservation_overlap_total{channel}`
- [ ] Métricas nuevas: `webhook_signature_invalid_total{provider}`
- [ ] Métricas nuevas: `job_duration_seconds{job}`
- [ ] Histograma `req_latency_seconds_bucket` por ruta (p95 derivada)
- [ ] Dashboards Prom/Grafana actualizados
- [ ] Alertas: p95>3s (10m) warning / >6s critical; error_rate>1% (5m) warning / >5% critical; ical_last_sync_age>30 warning

Criterios de Aceptación
- [ ] Métricas expuestas en `/metrics` y visibles en Grafana
- [ ] Alertas activas y notificando al canal configurado

Dependencias
- Fase 1 lista; `/metrics` expuesto

Referencias
- ops/STAGING_BENCHMARK_PLAN.md
- monitoring/

---

## 5) Performance Tuning (0.5–1 día)

Checklist
- [ ] EXPLAIN ANALYZE en queries calientes (reservas, calendario)
- [ ] Índices en columnas de filtro/orden
- [ ] Ajuste Gunicorn/Uvicorn workers/hilos según CPU y RAM
- [ ] Ajuste pool DB/Redis (timeouts/concurrency)
- [ ] Re-ejecutar benchmark sintético y comparar

Criterios de Aceptación
- [ ] P95 estable y ≤ objetivo en staging; sin regresiones notables

Referencias
- backend/scripts/runtime_benchmark.py

---

## 6) Seguridad (0.5 día)

Checklist
- [ ] Middleware headers: HSTS, X-Content-Type-Options, X-Frame-Options
- [ ] JWT scope `admin` validado en endpoints
- [ ] Rotación de secretos: procedimiento documentado + script
- [ ] Validación estricta de firmas (WhatsApp/MP) en webhooks; logs de intentos inválidos

Criterios de Aceptación
- [ ] Webhooks siempre requieren firma válida; 403 en inválidos
- [ ] CORS permite solo dominios esperados

Referencias
- ops/INCIDENT_RESPONSE_RUNBOOK.md, ops/DISASTER_RECOVERY.md

---

## 7) QA Final (0.5–1 día)

Checklist
- [ ] Tests unit de errores comunes (422, 409 overlap, 429)
- [ ] Smoke API (healthz, reservas, webhooks críticos)
- [ ] UAT Admin: checklist manual (Login, KPIs, reservas, filtros, búsqueda, orden, calendario, webhooks, salud)
- [ ] Evidencia: capturas + tiempos de respuesta

Criterios de Aceptación
- [ ] Todo verde en CI; smoke PASS; UAT completo sin bloqueantes

Referencias
- frontend/admin-dashboard/UAT_TESTING_CHECKLIST.md
- frontend/admin-dashboard/DEPLOYMENT_STATUS.md

---

## 8) Go-Live Producción (0.5 día) y Monitoreo 24–48h

Checklist
- [ ] Clonar config de Staging a Prod; setear secretos prod
- [ ] Deploy a Prod (rolling, auto_rollback ON)
- [ ] Validar health/metrics; activar alertas
- [ ] Monitoreo 24–48h; reporte final de estado y métricas

Criterios de Aceptación
- [ ] Sin incidentes críticos; SLOs cumplidos; rollback probado

Referencias
- ops/PROD_READINESS_CHECKLIST.md

---

## 📎 Anexos útiles

- Plan detallado: `ops/PLAN_COMPLETO_FLYIO_UX_ADMIN.md`
- Blueprint UX: `ops/BLUEPRINT_CHECKLIST_OPTIMIZACION_UX.md`
- Guía de Secretos: `ops/GUIA_OBTENER_SECRETOS_PASO_A_PASO.md`
- Índice: `DOCUMENTATION_INDEX.md`

---

## 🧠 Notas operativas

- Anti-feature creep: no expandir modelo ni integraciones fuera del alcance.
- Schema de DB bloqueado: no modificar tablas core.
- Validar anti doble-booking en staging tras cada cambio potencialmente sensible.
- Siempre correr validación 7/7 antes de cada deploy.
