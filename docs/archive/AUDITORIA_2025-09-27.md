# Auditoría técnica avanzada – 2025-09-27

Este documento captura el estado actual del backend, validaciones realizadas, desvíos respecto a la guía del MVP y recomendaciones priorizadas para avanzar hacia despliegue.

## Resumen de control de versiones
- Rama: `main`
- Último commit: feat(nlu+whatsapp+metrics): orquestación NLU→pre-reserva (API y WhatsApp), métricas centralizadas, email templates y hardening Mercado Pago; jobs de expiración y recordatorios; health y deploy tuning; tests E2E y hardening añadidos
- Tag: `eod-2025-09-27`
- Remoto: no configurado (pendiente `git remote add origin <url>`)
- Suite de tests: 37 passed, 13 skipped, 4 warnings (antes del commit)

## Funcionalidad Core
- Pre-reservas: Redis lock + constraint Postgres; expiración automática (job) y recordatorios por email. Confirmación maneja expiradas con 200 + `error="expired"`.
- NLU → pre-reserva: endpoint `/api/v1/nlu/analyze` y orquestación en webhook WhatsApp con prompts automáticos (no-op fuera de prod).
- WhatsApp: validación de firma X-Hub-Signature-256; normalización de mensajes.
- Mercado Pago: verificación estricta de firma (v1) cuando hay secreto; actualizaciones idempotentes y confirmación en aprobado.
- iCal: export con token HMAC. Health chequea `last_ical_sync`, import a verificar.

## Integridad y anti double-booking
- Redis lock: `lock:acc:{id}:{checkin}:{checkout}` con TTL 1800s.
- Constraint Postgres: Alembic agrega `btree_gist`, columna `daterange`, `EXCLUDE USING gist` con rango half-open `[)` (permite back-to-back).
- Nota: la guía pedía `'[]'`; recomendación mantener `[)` por estándar hotelero y ajustar ADR/README.

## Seguridad
- Webhooks: HMAC validado para WhatsApp (sha256=…) y Mercado Pago (x-signature v1). Body leído una sola vez.
- Admin: JWT con whitelist por email + header CSRF simple (MVP). Endurecer post-MVP.
- Secretos via env; logging estructurado sin secretos.
- HTTPS: Nginx en compose (revisar config/SSL en repo).

## Observabilidad y health
- Prometheus en `/metrics` vía instrumentator + contadores custom centralizados.
- `/healthz`: DB, Redis, disco, memoria básica, iCal last sync age, flags de credenciales WhatsApp/MP, y runtime.
- Sugerencia: reachability cacheada (evitar llamadas externas en health síncrono) si se desea.

## Rendimiento
- Gunicorn + Uvicorn workers; timeouts/keep-alive configurables; pool DB por settings. Jobs batch-limit.
- Audio pipeline con ffmpeg + faster-whisper base; umbral de confianza.

## Deploy
- Dockerfile slim con ffmpeg, usuario no-root, healthcheck, gunicorn.
- Compose con healthchecks; observaciones:
  - Alinear indentación de `GUNICORN_*` en `environment`.
  - Servicio `scheduler` referencia `app.jobs.scheduler` (no encontrado) → ajustar o remover.
  - Confirmar `nginx.conf` y `ssl/` presentes, o adaptar a proxy alternativo.
  - Exposición de puertos de db/redis solo en dev.

## Email/Mensajería
- EmailService con TLS, reintentos, templates Jinja, métricas.
- WhatsApp sender no-op fuera de prod; seguro.

## Testing
- Cobertura amplia: anti-solapamiento, firmas inválidas, audio low-confidence, idempotencia MP, iCal dedup, NLU→pre-reserva, expiración.
- Suite estable y rápida.

## Desvíos y riesgos
- `daterange` `[)` vs. `[]` en guía: documentar decisión y alinear expectativas (permite back-to-back).
- `/healthz` reachability de servicios externos evaluada por flags; si se requiere comprobación real, usar sondeo asíncrono cacheado.
- `docker-compose.yml`: revisar indentación env y servicio `scheduler`.
- Falta `.env.template` (obligatorio según guía).
- GET verification de WhatsApp (challenge) no implementado aún.

## Recomendaciones (priorizadas)
- P0: corregir compose (`environment` y `scheduler`), añadir `.env.template`, documentar ADR `daterange [)`, implementar GET verify de WhatsApp, revisar iCal import job/wiring.
- P1: observabilidad (histogramas y dashboards), reachability cacheada, seguridad admin (rate limiting, JWT/CSRF mejorado), plantillas WhatsApp, link de pago, CI con lint/pre-commit.
- P2: logging centralizado, caching de plantillas, colas para mensajes si la carga lo exige.

## Próximos pasos sugeridos
1) Añadir `.env.template` con todas las variables (este repo).
2) Blueprint de despliegue con checklist y criterios de aceptación (ver documento dedicado).
3) Ajustes mínimos de compose + WhatsApp GET verify + ADR daterange.
