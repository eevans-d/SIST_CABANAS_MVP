# 📌 Plan de Ejecución Completa — Fly.io + UX Admin (100% Listo para Producción)

Fecha: 2025-10-28
Estado: Propuesto (lista para ejecución inmediata)
Alcance: Llevar el sistema a 100% desarrollo funcional y despliegue en Fly.io, optimizando la experiencia del Administrador (dueño del complejo) y robusteciendo operación.

---

## 🎯 Objetivos y Éxito

- Disponibilidad en Staging y Producción en Fly.io, con rollback automático.
- Anti doble-booking garantizado (constraint + locks) bajo carga y concurrencia real.
- Admin Dashboard útil y ágil: KPIs, reservas, calendario, monitores de webhooks y salud, con P95<2s.
- Seguridad y cumplimiento: validación de firmas, JWT scopes, CORS, rotación básica de secretos.
- Observabilidad accionable: métricas Prometheus operativas y umbrales de alerta definidos.

Definición de Éxito (DoD Global):
- P95 APIs críticas < 300ms (staging); P95 Admin views < 2s; error rate < 1%.
- Pre-deploy validator 7/7 PASS; health checks OK; smoke tests y overlap test OK.
- Admin puede: ver KPIs, listar/filtrar/buscar reservas, ver calendario por alojamiento, revisar webhooks y salud.
- Deploy a Producción con plan de monitoreo y rollback en < 5 min.

---

## 🧩 Suposiciones y Dependencias

- Backend FastAPI + PostgreSQL 16 + Redis 7; ya operativos y con tests unit/integration.
- Redis gestionado (Upstash) o app Redis en Fly (sujeto a decisión); Postgres: Fly Postgres (volúmenes) o externo.
- WhatsApp Business y Mercado Pago con credenciales válidas y webhooks configurados hacia las URLs de Fly.
- Admin Dashboard compilado (Vite) y servible via Nginx o Fly static app; CORS permitido para dominios finales.

---

## 🧱 Fase 0 — Preparación y Auditoría (0.5 día)

Tareas
- Revisar `fly.toml` (región, puertos, health checks, concurrency, proceses). Confirmar región primaria (eze) y mínimo 1 máquina.
- Verificar Dockerfile (multi-stage, gunicorn/uvicorn workers, puerto 8000). Confirmar compatibilidad con Fly.
- Completar `.env.fly.staging` con secretos y URLs externas (DB, Redis, WhatsApp, MP).
- Verificar CI/CD de deploy a Fly (secrets en GitHub Actions) o ejecutar manual.

Criterios de Aceptación
- Pre-deploy validator 7/7 PASS.
- `fly launch`/`fly deploy` con healthz listo en URL pública.

Riesgos/Mitigación
- Credenciales faltantes → usar `ops/FLY_SECRETS_MATRIX.md` y `ops/set_fly_secrets.sh`.

---

## 🚀 Fase 1 — Despliegue en Staging (Fly.io) (0.5–1 día)

Tareas
- Crear app `sist-cabanas-mvp` (o `-staging`) en Fly.
- Base de datos:
  - Opción A (recomendado): Fly Postgres managed (volumen persistente) con `btree_gist` y parámetros acorde.
  - Opción B: Postgres externo gestionado (RDS/Neon/Supabase) con `btree_gist`.
- Redis:
  - Opción A: Upstash (simplicidad y latencia aceptable) → set `REDIS_URL`.
  - Opción B: Fly Redis app (si se prefiere on-Fly).
- Set de secretos: `flyctl secrets set` o GitHub Actions env.
- Deploy: `fly deploy` con health checks `/api/v1/healthz` y `/api/v1/readyz`.
- Migraciones: aseguradas vía entrypoint/start-script (alembic upgrade head) antes de servir.
- Rate limit, CORS, y headers de seguridad activos.

Criterios de Aceptación
- Healthz OK; `/metrics` accesible; logs sin errores críticos.
- `ops/smoke_and_benchmark.sh` PASS; `backend/scripts/concurrency_overlap_test.py` PASS (RUN_MUTATING opcional).

Riesgos/Mitigación
- Timeouts de cold start → subir `min_machines_running=1` y workers ajustados.

---

## 🧭 Fase 2 — UX Admin: Funcionalidad y Flujo (2–3 días)

Objetivo: que el administrador resuelva su día a día sin fricción.

Módulos y Tareas
1) Home (KPIs)
- KPIs: total reservas, confirmadas, pre-reservas, canceladas, revenue total/mes.
- Auto-refresh 30s; estados loading y error; tooltips de definiciones.
- Accesos rápidos: crear pre-reserva, export iCal, ver últimos webhooks.

2) Reservas
- Lista con paginación server-side, filtros (status, fechas, canal), búsqueda (nombre/teléfono/email), orden por columnas.
- Detalle reserva: datos completos, transición de estado (pre→confirm/cancel), reenvío link de pago.
- Estados visuales (badges), skeletons, toasts de resultado, confirm dialogs.

3) Calendario por Alojamiento
- Vista mensual, ocupación por día; tooltip con huésped/estado/precio; navegación entre meses.
- Indicador de solapes bloqueados (métrica de overlaps prevenidos).

4) Webhooks Monitor
- Tabla de últimas notificaciones (WhatsApp/MP): estado (200/4xx), firma válida, latencia, idempotencia.
- Filtros por proveedor/tipo/fecha; acción de reintento si API lo permite.

5) Salud / Operación
- Panel con `/healthz` y KPIs principales; `/metrics` parseado para mostrar p95 y tasas de error.

6) Config (solo lectura)
- Dominios permitidos CORS; versión del backend; estado de jobs; export JSON de config.

Criterios de Aceptación
- P95 de vistas Admin < 2s; 0 errores en consola; UX responsiva móvil y desktop.
- Mensajes de error claros y accionables (códigos + mensajes humanos).

---

## 🔧 Fase 3 — API Polish y Contratos (1–2 días)

Tareas
- Paginación/filtrado/orden unificados: `?page=&page_size=&q=&sort=` con límites y whitelist.
- Errores consistentes: `{code, message, details?, trace_id}`; mapear overlap a 409.
- 429 con Retry-After coherente.
- JWT scopes: `admin` para rutas `/api/v1/admin/*`.
- CORS: allowlist (admin UI + dominios staging/prod).
- OpenAPI enriquecido (examples, enums descriptivos, tags por módulo).

Criterios de Aceptación
- Swagger UI usable; respuestas uniformes; logging con `trace_id` propagado.

---

## 📈 Fase 4 — Observabilidad y Alertas (1 día)

Métricas clave
- `reservation_create_total{channel}`
- `reservation_overlap_total{channel}`
- `webhook_signature_invalid_total{provider}`
- `job_duration_seconds{job}`
- Histograma `req_latency_seconds_bucket` por ruta.

Alertas sugeridas (Grafana/Prometheus)
- `latency_p95 > 3s (10m)` warning; `> 6s` critical.
- `error_rate > 1% (5m)` warning; `> 5%` critical.
- `ical_last_sync_age_minutes > 30` warning.

---

## ⚙️ Fase 5 — Performance Tuning (0.5–1 día)

Tareas
- EXPLAIN ANALYZE en queries top (reservas, calendario) y añadir índices en filtros.
- Tuning de Gunicorn/Uvicorn workers (CPU x 1–2) y DB pool.
- Validar mejora/estabilidad con `runtime_benchmark.py`.

Criterios de Aceptación
- P95 estable y ≤ objetivo; sin regresiones.

---

## 🔐 Fase 6 — Seguridad (0.5 día)

Tareas
- Headers: HSTS, X-Content-Type-Options, X-Frame-Options (middleware).
- Revisión de JWT en Admin (scope) y expiración/refresh si aplica.
- Rotación básica de secretos (runbook) y auditoría de acceso.

Criterios de Aceptación
- Webhooks con firmas válidas siempre requeridas (WhatsApp/MP).
- CORS acotado; Admin protegido por JWT.

---

## 🧪 Fase 7 — QA y Validación Final (0.5–1 día)

Tareas
- Tests unitarios de errores comunes (422, 409 overlap, 429 rate limit).
- Smoke API y Admin (UAT checklist) con capturas.
- Validación de webhooks end-to-end (MP + WhatsApp) en staging.

Criterios de Aceptación
- Todo verde en CI; smoke PASS; documentación UAT archivada.

---

## 🟢 Fase 8 — Go-Live en Producción (0.5 día)

Tareas
- Clonar configuración de staging → prod; set de secretos prod.
- Deploy controlado; verificación health y métricas; activar alertas.
- Plan de rollback (Fly releases rollback) documentado.

Criterios de Aceptación
- 24–48h de monitoreo sin incidentes; reporte de estado final.

---

## 📅 Timeline Sugerido (5–7 días)

- Día 1: Fase 0 + 1 (staging up) y validaciones.
- Día 2–3: Fase 2 (UX Admin) — Home/Reservas/Calendario/Webhooks/Salud.
- Día 4: Fase 3 (API polish) + 4 (Obs).
- Día 5: Fase 5 (Perf) + 6 (Seguridad) + 7 (QA).
- Día 6–7 (buffer): Ajustes finales y Go-Live (Fase 8).

---

## ✅ Checklists Resumidas

- Staging listo
  - [ ] Healthz/Readyz OK
  - [ ] Smoke + Benchmark PASS
  - [ ] Overlap test PASS
  - [ ] Webhooks apuntando a staging

- UX Admin
  - [ ] KPIs + Auto-refresh
  - [ ] Lista reservas + filtros + búsqueda + orden
  - [ ] Detalle con cambios de estado
  - [ ] Calendario mensual por alojamiento
  - [ ] Monitor de webhooks y salud

- API/Seguridad
  - [ ] Paginación/errores unificados
  - [ ] JWT scope `admin` en /admin/*
  - [ ] CORS con allowlist
  - [ ] Headers de seguridad activos

- Observabilidad
  - [ ] Métricas clave expuestas
  - [ ] Alertas configuradas

- Producción
  - [ ] Deploy OK + Healthz
  - [ ] Monitoreo 24–48h
  - [ ] Plan de rollback probado

---

## 🧠 Riesgos y Mitigaciones

- Doble-booking por carrera de concurrencia → constraint + locks + pruebas de carga.
- Latencia elevada inter-regiones → fijar región (eze) y usar proveedores cercanos.
- Firmas webhook inválidas → validar siempre y log de intentos fallidos.
- Config CORS permisiva → allowlist estricta; tests de preflight.
- Secreto expuesto → rotación y auditoría de variables.

---

## 📜 Entregables Finales

- Staging/Prod en Fly.io, con health checks, métricas y alertas activas.
- Admin Dashboard funcional (Home/Reservas/Calendario/Webhooks/Salud/Config).
- Documentación actualizada: índice, blueprint UX, plan completo, UAT resultados.
- Scripts y Makefile para flujos comunes (admin-*, smoke, deploy).

---

## 🔚 DoD Global

- Build/Lint/Tests verdes; Pre-deploy 7/7 PASS; P95 dentro de SLO.
- Anti doble-booking verificado; webhooks firmados; CORS/JWT correctos.
- Documentación y runbooks en `ops/` y `backend/docs/` actualizados.
