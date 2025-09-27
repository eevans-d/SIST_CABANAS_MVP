# Blueprint y Checklist hacia Despliegue

Este blueprint detalla tareas, criterios de aceptación y orden recomendado para pasar del estado actual a un despliegue seguro.

## P0 – Imprescindible antes de despliegue
1) Variables de entorno estandarizadas
   - Entregar `.env.template` completo.
   - Criterio: todos los servicios levantan sin variables faltantes, y health OK.
2) docker-compose.yml
   - Corregir indentación de `GUNICORN_*` en `environment` (app).
   - Revisar/eliminar servicio `scheduler` o implementar `app.jobs.scheduler`.
   - Quitar puertos públicos de db/redis en prod.
   - Criterio: `docker compose up -d` estable; healthz OK para app, db y redis.
3) WhatsApp GET verification
   - Implementar `GET /webhooks/whatsapp` que responda el `hub.challenge` validando `WHATSAPP_VERIFY_TOKEN`.
   - Criterio: Webhook verificable desde Meta.
4) ADR daterange
   - Documentar decisión de `[)` y alinear README/ADR.
   - Criterio: documento presente y referenciado.
5) iCal import
   - Confirmar que el job de import existe y está cableado; si no, crear `jobs/import_ical.py` y programarlo.
   - Criterio: healthz refleja last sync actualizado (< 20 min) tras correr el job.

## P1 – Siguiente mejora tras primer despliegue
1) Observabilidad
   - Agregar histogramas (latency buckets) y panel base Grafana.
   - Criterio: /metrics con histogramas; dashboard importable.
2) Seguridad Admin
   - Rate-limiting (Nginx y/o aplicación), fortalecer CSRF, expiración corta de JWT.
   - Criterio: pruebas manuales pasan; nuevas pruebas automáticas mínimas.
3) Mensajería
   - Plantillas WhatsApp (renderizadas) para prompts y confirmaciones.
   - Criterio: mensajes coherentes y parametrizados.
4) Pagos
   - Generación de link de pago y E2E con webhook de aprobación.
   - Criterio: journey completo desde pre-reserva hasta confirmación por pago.
5) CI/Lint
   - Pre-commit (ruff/black/isort) y pipeline CI (lint + tests + seguridad básica).
   - Criterio: PRs requieren verde; estilo consistente.

## P2 – Robustez y escalado
1) Logging centralizado (Loki/ELK) con trazas.
2) Cache de plantillas y colas para tareas no críticas si crece la carga.
3) Pruebas E2E ampliadas (mensajería real, pagos sandbox, iCal con cuentas externas).

## Checklist rápida (marcado)
- [ ] `.env.template` creado y validado
- [ ] `docker-compose.yml` corregido (environment/scheduler/puertos)
- [ ] WhatsApp GET verify implementado
- [ ] ADR daterange `[)` documentado
- [ ] iCal import job verificado/cableado
- [ ] Healthz OK estable post-compose
- [ ] /metrics expone contadores e histogramas (P1)
- [ ] Nginx configurado con SSL y headers seguridad
- [ ] CI/Lint activo (P1)

## Criterios de salida a despliegue (go/no-go)
- Tests unitarios y de integración verdes.
- Healthz healthy (sin `error` y máximo `degraded` por memoria si corresponde).
- Logs sin secretos; métricas expuestas.
- Webhooks (WhatsApp/MP) verificados y con firma.
- Anti double-booking validado en Postgres real (btree_gist activo).
