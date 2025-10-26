# Checklist de Producción y Cutover

> **Objetivo:** Verificar que todo esté listo antes de llevar MVP a producción.
> **Responsable:** DevOps / Tech Lead.
> **Timing:** 1–2 días antes del cutover.

---

## 1. Infrastructura y Servicios

- [ ] **Fly Postgres**
  - [ ] Versión: PostgreSQL 16+
  - [ ] Backups automáticos habilitados
  - [ ] Retención: mínimo 7 días
  - [ ] Réplica de lectura en otra región (opcional, si tráfico > 100 req/s)

- [ ] **Redis / Upstash**
  - [ ] Plan: Starter (mínimo) o Pro si > 1000 req/s
  - [ ] Persistence habilitada (AOF)
  - [ ] Encryption: TLS forzado (redis://:pass@host:port → rediss://)

- [ ] **Fly App (Backend)**
  - [ ] VM size: shared-cpu-2x (mínimo) o dedicated-cpu-1x
  - [ ] Scaling: 2 máquinas (HA)
  - [ ] Auto-stop deshabilitado (webhooks 24/7)
  - [ ] Rolling deploy con auto-rollback habilitado

---

## 2. Configuración y Secretos

- [ ] **Variables de entorno**
  - [ ] `ENVIRONMENT=production` (no `staging`)
  - [ ] `LOG_LEVEL=info` (no `debug`)
  - [ ] Todos los secretos cargados (JWT_SECRET, ICS_SALT, credentials de terceros)

- [ ] **Dominios y HTTPS**
  - [ ] Dominio base: `tu-dominio.com`
  - [ ] TLS habilitado (Fly auto-certs o Let's Encrypt)
  - [ ] CORS configurado: solo dominios permitidos
  - [ ] HSTS headers presentes (`max-age=31536000`)

- [ ] **Rate Limiting y Seguridad**
  - [ ] Rate limit activo: 100 req/min por IP
  - [ ] Webhook signatures validadas (WhatsApp, Mercado Pago)
  - [ ] JWT validation on `/admin/*` endpoints
  - [ ] No hay logs de datos sensibles (passwords, tokens)

---

## 3. Database

- [ ] **Schema y Migraciones**
  - [ ] Alembic migration: `alembic upgrade head` corrió sin errores
  - [ ] Constraint anti-doble-booking activo: `EXCLUDE USING gist`
  - [ ] Indexes presentes: `accommodation_id`, `reservation_code`, `created_at`

- [ ] **Data Integrity**
  - [ ] Prueba de concurrencia (doble-booking): 1 de N intenta fallando ✅
  - [ ] Datos de seed (alojamientos iniciales) cargados
  - [ ] No hay NULL's en campos REQUIRED

---

## 4. APIs y Webhooks

- [ ] **REST API (Core)**
  - [ ] GET `/api/v1/accommodations` → 200
  - [ ] POST `/api/v1/reservations` → 201 con código pre-reserva
  - [ ] GET `/api/v1/reservations/{code}` → 200
  - [ ] Error handling consistente (4xx/5xx con JSON)

- [ ] **Webhooks (Terceros)**
  - [ ] WhatsApp: firma X-Hub-Signature-256 validada ✅
  - [ ] Mercado Pago: firma x-signature validada ✅
  - [ ] Idempotencia activada (48h TTL en idempotency_keys)
  - [ ] Respuestas 202 Accepted (no esperar procesamiento completo)

- [ ] **iCal**
  - [ ] Export: `/api/v1/ical/{token}.ics` accesible
  - [ ] Import: `/api/v1/ical/import` acepta POST con URL válida
  - [ ] Sync automático cada 5 min (job background activo)

---

## 5. Observabilidad

- [ ] **Prometheus Metrics**
  - [ ] `/metrics` expone endpoints clave
  - [ ] Gauges críticos: `ical_last_sync_age_minutes`, `active_reservations`
  - [ ] Histogramas: latencia por endpoint
  - [ ] Scrape config en Prometheus válido

- [ ] **Health Checks**
  - [ ] `/api/v1/healthz` → 200 "healthy" (BD, Redis, iCal OK)
  - [ ] `/api/v1/readyz` → 200 cuando listo para tráfico
  - [ ] Fly health check configurado (interval 15s, timeout 5s)

- [ ] **Logs**
  - [ ] Formato JSON estructurado (timestamp, level, trace_id)
  - [ ] Rotation: diario, retención 30 días
  - [ ] Agregador (Papertrail, Datadog, o similar) configurado
  - [ ] Búsqueda de errores 5xx facilitada

- [ ] **Alertas**
  - [ ] Prometheus alert rules compiladas sin errores
  - [ ] Canales: Slack, Email, o PagerDuty
  - [ ] Alert thresholds basados en SLOs (error-rate > 1%, p95 > 3s)

---

## 6. Rendimiento y SLOs

- [ ] **Benchmarks validados en staging**
  - [ ] p95 `/api/v1/healthz`: < 200ms ✅
  - [ ] p95 `POST /api/v1/reservations`: < 3s ✅
  - [ ] error-rate global: < 1% ✅
  - [ ] Concurrencia testeada: 10 req/s mínimo

- [ ] **Escalado**
  - [ ] Load test local: 100 req/s → p95 < 2s
  - [ ] Confirmación: Fly puede escalar automáticamente (o manual)

---

## 7. Seguridad

- [ ] **Escaneo de Vulnerabilidades**
  - [ ] `safety check`: 0 known CVEs en requirements.txt
  - [ ] `trivy image`: Dockerfile scan OK
  - [ ] No hay secretos en git (SAST check)

- [ ] **Encriptación**
  - [ ] HTTPS obligatorio (redirigir HTTP → HTTPS)
  - [ ] TLS 1.2+ mínimo
  - [ ] Base de datos: conexiones encriptadas
  - [ ] Redis: TLS forzado (rediss://)

- [ ] **Autenticación y Autorización**
  - [ ] JWT HS256 con SECRET seguro (>= 32 chars)
  - [ ] Admin endpoints: JWT validation + ADMIN_ALLOWED_EMAILS
  - [ ] CORS: solo dominios permitidos, no `*`

---

## 8. Operación y Runbooks

- [ ] **Runbooks documentados**
  - [ ] `incident-response-runbook.md`: procedimiento para alertas críticas
  - [ ] `disaster-recovery.md`: pasos para restaurar desde backup
  - [ ] `rollback-plan.md`: cómo revertir a versión anterior

- [ ] **Contactos y Escalación**
  - [ ] On-call engineer asignado
  - [ ] Canales de comunicación configurados (Slack, email)
  - [ ] Horario de soporte definido

- [ ] **Capacitación**
  - [ ] Tech lead entiende stack (FastAPI, Alembic, Fly)
  - [ ] Backup person sabe cómo ver logs y hacer rollback

---

## 9. Compliance y Datos

- [ ] **GDPR / Privacidad (si aplica a Argentina)**
  - [ ] Política de privacidad publicada
  - [ ] Logs no contienen PII sin motivo
  - [ ] Retención de datos: clara y limitada

- [ ] **Datos de Clientes**
  - [ ] Backup: pg_dump diario, retención 7 días
  - [ ] Integridad: checksums en backups
  - [ ] Restauración: probada (dry-run)

---

## 10. Proceso de Despliegue Final

### Día D-1

- [ ] Comunicar a users: "Maintenance window Oct 27, 22:00-23:00 ART"
- [ ] Snapshot DB (backup manual)
- [ ] Últimos tests: smoke en staging ✅

### Día D (Cutover)

1. [ ] **14:00 UTC / 11:00 ART:** Freeze en desarrollo (no commits)
2. [ ] **14:05 UTC:** Deploy a producción
   ```bash
   flyctl deploy --strategy rolling -a sist-cabanas-prod
   ```
3. [ ] **14:15 UTC:** Health checks
   ```bash
   curl https://sist-cabanas.app/api/v1/healthz
   ```
4. [ ] **14:20 UTC:** Smoke test básico
   - GET `/accommodations` → sin error
   - POST `/reservations` con test data → 201 Created
5. [ ] **14:30 UTC:** Monitoreo activo (1–2 horas)
   - Datadog/Prometheus dashboard abierto
   - Logs en cola para buscar errores
6. [ ] **15:30 UTC:** OK signal → comunicar a users "Production live"

### Rollback (si falla)

```bash
# Ver releases
flyctl releases -a sist-cabanas-prod

# Rollback a versión anterior
flyctl releases rollback -a sist-cabanas-prod

# Confirmar
curl https://sist-cabanas.app/api/v1/healthz
```

---

## Checklist de Cierre

- [ ] Todos los items de 1–9 completos (✅ o N/A)
- [ ] Runbooks revisados y accesibles
- [ ] On-call engineer disponible durante cutover
- [ ] Rollback plan ensayado (simulación)
- [ ] Green light: Tech Lead o CEO aprueba
- [ ] **Proceder con despliegue**

---

## Contactos de Emergencia

| Rol | Nombre | Teléfono | Email | Horario |
|-----|--------|----------|-------|---------|
| Tech Lead | | | | 24/7 on-call |
| DevOps | | | | Business hours |
| CEO/Stakeholder | | | | Alert only |

---

## Notas Post-Producción

- Día 1: Monitoreo intenso (alertas en rojo → rollback inmediato)
- Semana 1: Ajustes menores (rate limits, cache TTL, etc.)
- Mes 1: Retrospectiva y optimizaciones de performance
