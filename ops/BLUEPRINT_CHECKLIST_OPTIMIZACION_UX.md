# 🧭 Blueprint + Checklist de Optimización y UX (Post-MVP)

Estado: Propuesto (Oct 28, 2025)
Duración sugerida: 5–7 días hábiles (time-box por fases)
Meta: Pulir experiencia Admin, robustez operacional y calidad sin romper el MVP (shipping > perfección)

Reglas de Oro:
- Anti-feature creep: implementar SOLO lo que suma valor directo a UX/operación.
- Green-before-done: build/lint/tests deben pasar en cada PR.
- Doble-booking intocable: no modificar constraints; sólo monitoreo/pruebas.

---

## 📦 Entregables (resumen)
- Admin Dashboard (React + Vite + Tailwind): Home, Reservas, Calendario, Webhooks, Salud, Config.
- API polish: paginación/filtrado consistentes, errores unificados, docs OpenAPI enriquecidas.
- Observabilidad+: métricas granulares y alertas; logs con trazabilidad.
- Seguridad+: CORS ajustado, JWT con scopes, headers seguros, rotación de secretos (runbook).
- Rendimiento: índices DB revisados, gunicorn/uvicorn tuning, top queries con EXPLAIN.
- Ops: scripts utilitarios (seed segura, smoke rápido), documentación breve de usuario admin.

---

## 🗂 Fase A — Admin Dashboard (React 18 + Vite + Tailwind) [2–3 días]

Checklist (por pantalla)
1) Infra base UI
- [ ] Vite + React 18 + TS + Tailwind + ESLint/Prettier
- [ ] Auth JWT: login simple (POST /admin/login), almacenamiento seguro (memory + refresh endpoint si aplica)
- [ ] Interceptor HTTP (axios): Bearer token + manejo 401/429 con toasts
- [ ] .env: VITE_API_BASE_URL

2) Home (Panel)
- [ ] KPIs: reservas hoy/semana, tasa conversión pre-reserva→confirmada, último sync iCal
- [ ] Health widgets: DB/Redis/iCal/RateLimit (de /api/v1/healthz)
- [ ] Enlaces rápidos: crear pre-reserva, export iCal, ver webhooks recientes

3) Reservas (CRUD de pre-reservas)
- [ ] Lista con paginación (server-side), filtros fecha/estado/canal, búsqueda por nombre/teléfono
- [ ] Detalle: ver datos + transición estado (pre_reserved→confirmed/cancelled)
- [ ] Acción rápida: reenviar link de pago (si aplica)

4) Calendario
- [ ] Vista mensual por alojamiento (resumen de ocupación)
- [ ] Tooltip: estado, huésped, precio; navegación entre meses
- [ ] Indicador de solapes bloqueados (overlap detectado/prevenciones)

5) Webhooks Monitor
- [ ] Tabla: últimos N eventos (WhatsApp/MP), estado (200/4xx), firma válida, latencia
- [ ] Filtro por proveedor/tipo/fecha; botón reintentar (si endpoint soporta replay)

6) Salud/Operación
- [ ] Métricas destacadas (/metrics parseado): error_rate, req_latency_p95, ical_last_sync_age
- [ ] Jobs: próximo/último run (si se expone), botones manuales (si API permite)

7) Configuración
- [ ] CORS allowlist (solo lectura/aviso)
- [ ] Ajustes de SLO visibles (solo lectura)
- [ ] Export de configuración a JSON (descargable)

Criterios de Aceptación
- [ ] Todas las vistas cargan < 2s P95 con API remota
- [ ] Errores renderizados amigablemente (mensajes humanos + codes)
- [ ] 0 console errors; Lighthouse performance > 85 en dashboard (estático)

---

## 🔧 Fase B — API Polish (Back-end) [1–2 días]

1) Paginación/Filtrado/Orden
- [ ] Patrón unificado: ?page=?page_size=&q=&sort=
- [ ] Validaciones: límites page_size (1–100), sort whitelist

2) Errores consistentes
- [ ] Esquema de error: {code, message, details?, trace_id}
- [ ] Mapear IntegrityError (overlap) → 409 con message claro
- [ ] 429 con Retry-After coherente al rate limit

3) OpenAPI enriquecido
- [ ] Examples por endpoint; tags amigables
- [ ] Schemas con descripciones; enum documentados

4) CORS endurecido
- [ ] Sólo dominios del Admin UI/staging/prod

5) JWT scopes (RBAC simple)
- [ ] Claims: {sub, scope: ["admin"]}
- [ ] Dependencia FastAPI para verificar scope en /admin/*

Criterios de Aceptación
- [ ] OpenAPI sin warnings (Swagger UI usable por QA)
- [ ] P95 de endpoints principales < 300ms (staging)

---

## 📈 Fase C — Observabilidad & Operaciones [1 día]

Métricas nuevas
- [ ] reservation_create_total{channel}
- [ ] reservation_overlap_total{channel}
- [ ] webhook_signature_invalid_total{provider}
- [ ] job_duration_seconds{job}
- [ ] req_latency_seconds_bucket (histogram por ruta principal)

Logs
- [ ] trace_id propagado a cada request (middleware)
- [ ] Campos: user_id/canal/reservation_code cuando aplica (sin datos sensibles)

Alertas (en Grafana/Prometheus)
- [ ] latency_p95 > 3s (10m) → warning; > 6s → critical
- [ ] error_rate > 1% (5m) → warning; > 5% → critical
- [ ] ical_last_sync_age_minutes > 30 → warning

---

## ⚙️ Fase D — Rendimiento [0.5–1 día]

- [ ] Revisar EXPLAIN ANALYZE en consultas top (reservas, calendario)
- [ ] Confirmar e indexar columnas usadas en filtros/orden
- [ ] Pool DB/Redis/Gunicorn workers conforme a CPU/mem (Fly)
- [ ] Feature flag opcional: cache de listados públicos (TTL 60s) SOLO si profiling lo exige

DoD
- [ ] Bench sintético (`runtime_benchmark.py`) mejora o se mantiene

---

## 🔐 Fase E — Seguridad [0.5 día]

- [ ] Headers: HSTS, X-Content-Type-Options, X-Frame-Options (vía Starlette middleware)
- [ ] Rotación de secretos: script + runbook
- [ ] Revisión de permisos en /admin/* con pruebas mínimas de autorización

---

## 🧪 Fase F — QA Ligero [0.5–1 día]

- [ ] Tests unitarios para errores comunes (422, 409 overlap, 429)
- [ ] Smoke API (httpx) para rutas críticas (healthz, reservas, webhooks)
- [ ] Checklist manual de UI (10 pasos) con capturas

---

## 🗓 Sugerencia de Agenda (5–7 días)

- Día 1–2: Fase A (UI base + Reservas + Home)
- Día 3: Fase A (Calendario + Webhooks)
- Día 4: Fase B (API polish) + C (Obs)
- Día 5: D (Perf) + E (Seguridad) + F (QA)
- Buffer 1–2 días: ajustes, bugs, docs

---

## ✅ Blueprint Checklist (macro)

- [ ] A. Admin Dashboard implementado (6 secciones) y documentado
- [ ] B. API unificada (paginación, errores, OpenAPI)
- [ ] C. Métricas y alertas ampliadas
- [ ] D. Índices/perform tuning aplicados y medidos
- [ ] E. Seguridad endurecida (CORS, headers, JWT scopes)
- [ ] F. QA ligero (tests + smoke + checklist UI)

---

## 📜 Notas y Límites (Out-of-scope)
- No integrar PMS externo (ver ADR vigente)
- No introducir caches complejas o microservicios
- No ampliar modelo de datos (schema locked)

---

## 🔚 Definition of Done (global)
- Build/lint/tests verdes
- Pre-deploy 7/7 PASS
- P95 < 3s, error rate < 1%
- Anti-doble-booking verificado (concurrency_overlap_test)
- Documentación actualizada (README Admin + Quick Start UI)
