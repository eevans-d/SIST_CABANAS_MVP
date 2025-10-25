# Checklist de Deploy a Fly.io (Staging → Prod)

> Este checklist resume pasos mínimos para desplegar el backend FastAPI en Fly.io con Postgres y Redis, más validaciones post-deploy.

## Pre-requisitos
- Cuenta Fly.io activa y `flyctl` instalado
- Token `FLY_API_TOKEN`
- App creada: `sist-cabanas-mvp` (ajusta el nombre si aplica)
- Base de datos Fly Postgres creada o adjunta
- Redis (Upstash) provisionado

## 1) Servicios gestionados
- [ ] Crear/adjuntar Fly Postgres
  - `flyctl postgres create` o `flyctl postgres attach -a sist-cabanas-mvp`
- [ ] Provisionar Upstash Redis
  - Obtener `REDIS_URL` (formato `redis://:password@host:port/0`)

## 2) Secretos y configuración
- [ ] Cargar secretos críticos (ver `ops/FLY_SECRETS_MATRIX.md`)
  - DATABASE_URL
  - REDIS_URL
  - JWT_SECRET
  - WHATSAPP_* (token, secret, phone id, verify token)
  - MERCADOPAGO_* (access token, webhook secret)
  - ADMIN_ALLOWED_EMAILS
- [ ] Ajustar CORS
  - ALLOWED_ORIGINS: dominios del dashboard/web
- [ ] Ajustar parámetros operativos (rate limit, jobs)

## 3) Deploy
- [ ] Desplegar build e iniciar release
  - CI/GitHub Actions o `flyctl deploy -a sist-cabanas-mvp --strategy rolling`
- [ ] Verificar logs en vivo
  - `flyctl logs -a sist-cabanas-mvp -f`

## 4) Validaciones post-deploy (Smoke)
- [ ] Health
  - GET `/api/v1/healthz` → 200 healthy
- [ ] Métricas Prometheus
  - GET `/metrics` → responde sin error
- [ ] Ready
  - GET `/api/v1/readyz` → 200
- [ ] Endpoint de catálogo básico (si aplica)
  - GET `/api/v1/accommodations` → 200 y lista vacía/no vacía

## 5) Benchmarks y pruebas críticas
- [ ] Ejecutar benchmark de runtime (p50/p95 y error-rate)
  - Objetivo SLO: p95 < 3s (endpoints de texto), ideal << 200ms
- [ ] Validar anti-double-booking (carrera controlada)
  - Ejecutar prueba de concurrencia (RUN_MUTATING=1)
  - Esperado: una creación falla por constraint/locking

## 6) Observabilidad y operación
- [ ] Confirmar `/metrics` en dashboards (Prometheus/Grafana)
- [ ] Ver alertas básicas (health degradado, error rate)
- [ ] Respaldos Postgres (pg_dump diario, retención 7 días)

## 7) Corte a producción
- [ ] Dominio y TLS (Fly certs) configurados
- [ ] Escalado (1–2 VM, RAM suficiente)
- [ ] Plan de rollback
  - `flyctl releases -a <app>` y `flyctl deploy --image <previous>`

---

Notas:
- Mantener consistencia de nombres de variables con el código (RATE_LIMIT_WINDOW_SECONDS, JOB_*).
- `start-fly.sh` debe correr `alembic upgrade head` para activar constraints (incluye EXCLUDE gist anti-overlap).
