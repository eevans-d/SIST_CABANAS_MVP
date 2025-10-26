# Playbook: Despliegue a Staging en Fly.io

> **Objetivo:** Desplegar backend MVP a staging en Fly.io con validaciones post-deploy (smoke + benchmark).
> **Audiencia:** DevOps / Ingeniero de Deploy.
> **Tiempo estimado:** 15–20 min (primero) + 5 min (redeploys).
> **Prerrequisitos:** flyctl instalado y autenticado, acceso a secretos reales.

---

## Fase 1: Preparación (5 min)

### 1.1) Verificar flyctl
```bash
# Confirmar instalación y autenticación
flyctl version
flyctl auth whoami
```

Esperado:
- `flyctl version` → v0.x.x (any recent)
- `flyctl auth whoami` → tu usuario de Fly

### 1.2) Confirmar app existe (o crear)
```bash
# Listar apps
flyctl apps list

# Si NO existe 'sist-cabanas-mvp', crear:
flyctl apps create sist-cabanas-mvp --org personal

# Confirmar región (debe ser 'eze' para Arg)
flyctl regions list -a sist-cabanas-mvp || flyctl regions add eze -a sist-cabanas-mvp
```

### 1.3) Preparar archivo de secretos
```bash
# Copia la plantilla
cp env/.env.fly.staging.template env/.env.fly.staging

# Edita con valores reales (CRÍTICO: no commitear este archivo)
# vim env/.env.fly.staging
#
# Completa (mínimo):
#   DATABASE_URL=postgresql://...  (Fly Postgres URL)
#   REDIS_URL=redis://:...         (Upstash URL)
#   JWT_SECRET=<random-secure>
#   WHATSAPP_ACCESS_TOKEN=...
#   MERCADOPAGO_ACCESS_TOKEN=...
#   ADMIN_ALLOWED_EMAILS=...
#   ICS_SALT=<hex>

# Validar sintaxis (no errores de parseo)
bash -c 'set -a; source env/.env.fly.staging; set +a; echo "✅ Env vars loaded"'
```

---

## Fase 2: Servicios gestionados (5 min, UNA SOLA VEZ)

> Si ya existe DB/Redis en Fly, saltea esta sección.

### 2.1) Crear y adjuntar Fly Postgres (si no existe)
```bash
# Crear
flyctl postgres create --org personal --name sist-cabanas-db

# Esperar ~2 min
# Adjuntar a app
flyctl postgres attach sist-cabanas-db -a sist-cabanas-mvp

# Verificar (la DATABASE_URL se auto-setea)
flyctl secrets list -a sist-cabanas-mvp | grep DATABASE_URL
```

Esperado: `DATABASE_URL` debe estar presente en secrets.

### 2.2) Provisionar Upstash Redis (externo a Fly)
1. Ir a https://console.upstash.com
2. Crear DB Redis (región closest: `us-east-1` para Arg es OK por latencia).
3. Copiar URL `redis://:password@host:port/0`
4. Guardar en `env/.env.fly.staging` como `REDIS_URL=...`

---

## Fase 3: Cargar secretos (2 min)

```bash
# Script automatizado (recomendado)
./ops/set_fly_secrets.sh sist-cabanas-mvp env/.env.fly.staging

# O manual (si prefieres ver cada secreto)
flyctl secrets set \
  DATABASE_URL="$(grep '^DATABASE_URL=' env/.env.fly.staging | cut -d= -f2-)" \
  REDIS_URL="$(grep '^REDIS_URL=' env/.env.fly.staging | cut -d= -f2-)" \
  JWT_SECRET="$(grep '^JWT_SECRET=' env/.env.fly.staging | cut -d= -f2-)" \
  WHATSAPP_ACCESS_TOKEN="..." \
  MERCADOPAGO_ACCESS_TOKEN="..." \
  ADMIN_ALLOWED_EMAILS="admin@tu-dominio.com" \
  -a sist-cabanas-mvp

# Verificar
flyctl secrets list -a sist-cabanas-mvp
```

Esperado: al menos 8 secretos visibles (sin valores).

---

## Fase 4: Deploy (3 min)

### 4.1) Desplegar código
```bash
# Desde root del repo
flyctl deploy --remote-only --strategy rolling -a sist-cabanas-mvp

# Ver progreso en vivo
flyctl logs -a sist-cabanas-mvp -f
# (Presiona Ctrl+C para salir)
```

Esperado en logs:
```
Starting app initialization...
Started instance ffd12...
Listening on 0.0.0.0:8080
✅ Health check passing
```

### 4.2) Verificar estado
```bash
flyctl status -a sist-cabanas-mvp
```

Esperado: `Instances: ... (healthy)`.

---

## Fase 5: Validaciones (Smoke) (3 min)

### 5.1) Health checks manuales
```bash
BASE_URL="https://sist-cabanas-mvp.fly.dev"

# Health
curl -s "$BASE_URL/api/v1/healthz" | python -m json.tool

# Readiness
curl -s "$BASE_URL/api/v1/readyz" | python -m json.tool

# Metrics (primeras 5 líneas)
curl -s "$BASE_URL/metrics" | head -n 5
```

Esperado:
- `/healthz` → `{"status": "healthy", "checks": {...}}`
- `/readyz` → `{"status": "ready", ...}`
- `/metrics` → líneas con `# HELP` y métricas Prometheus

### 5.2) Smoke automático con script
```bash
./ops/smoke_and_benchmark.sh "$BASE_URL"
```

Esto:
- Llama a `/healthz`, `/readyz`, `/metrics`
- Ejecuta runtime_benchmark (concurrencia 10, 100 requests por endpoint)
- Reporte con p50/p95 y error-rate

---

## Fase 6: Validación Anti-Doble-Booking (5 min)

> Depende de que Alembic haya corrido (start-fly.sh ejecuta `alembic upgrade head`).

### 6.1) Preparar datos
```bash
# Crear una acomodación de prueba (si no existe)
# Opción A: crear manualmente vía API
# POST /api/v1/admin/accommodations
#
# Opción B: seedear localmente y copiar ID
# backend/scripts/seed_data.py → obtener accommodation_id

ACCOMMODATION_ID=1
CHECK_IN="2025-11-15"
CHECK_OUT="2025-11-17"
```

### 6.2) Ejecutar carrera de doble-booking
```bash
# Simular 2 solicitudes concurrentes en el mismo rango de fechas
# Esperado: UNA falla por constraint EXCLUDE gist o lock Redis (409 Conflict)

RUN_MUTATING=1 PYTHONPATH=backend python backend/scripts/concurrency_overlap_test.py \
  --base-url "$BASE_URL" \
  --accommodation-id "$ACCOMMODATION_ID" \
  --check-in "$CHECK_IN" \
  --check-out "$CHECK_OUT" \
  --concurrency 2
```

Esperado en logs:
```
Attempt 1: 201 Created (success)
Attempt 2: 409 Conflict (overlap detected) ✅
```

---

## Fase 7: Registrar Benchmark (2 min)

Después de ejecutar el script de smoke+benchmark, copia el reporte:

```bash
# Copiar salida a archivo de reporte
cat > backend/docs/reverse_engineering/RUNTIME_REPORT_STAGING_$(date +%Y-%m-%d).md << 'EOF'
# Runtime Report - Staging (Fly.io)

Fecha: $(date)
Base URL: $BASE_URL
Región: eze (Buenos Aires)
Ambiente: staging

## Resultados

[Pega la salida del script aquí]

## SLOs

- p95 /healthz: < 3s ✅/❌
- p95 /readyz: < 3s ✅/❌
- error-rate: < 1% ✅/❌

## Anti-Doble-Booking

[Pega resultado de concurrency_overlap_test aquí]

## Observaciones

- ...
EOF
```

---

## Fase 8: Troubleshooting (si aplica)

### App no arranca
```bash
# Ver logs completos
flyctl logs -a sist-cabanas-mvp --lines 200

# Buscar errores
flyctl logs -a sist-cabanas-mvp | grep -i error

# Reintentar (si es fallo temporal)
flyctl restart -a sist-cabanas-mvp
```

### Health check falla
```bash
# Verificar DB
curl -s "https://sist-cabanas-mvp.fly.dev/api/v1/healthz" | python -m json.tool | grep -A5 database

# Verificar Redis
curl -s "https://sist-cabanas-mvp.fly.dev/api/v1/healthz" | python -m json.tool | grep -A5 redis

# Si falla DB: verificar DATABASE_URL
flyctl secrets list -a sist-cabanas-mvp | grep DATABASE_URL
```

### Rollback rápido
```bash
# Ver releases anteriores
flyctl releases -a sist-cabanas-mvp

# Volver a release anterior
flyctl releases rollback -a sist-cabanas-mvp
```

---

## Checklist de Cierre

- [ ] `flyctl status` → healthy
- [ ] `/healthz` → 200, "healthy"
- [ ] `/readyz` → 200
- [ ] `/metrics` → 200
- [ ] Runtime p95 < 3s
- [ ] Error-rate < 1%
- [ ] Anti-doble-booking: 1 de N falla ✅
- [ ] Reporte guardado en `backend/docs/reverse_engineering/`
- [ ] Logs revisados, sin errors críticos

---

## Próximas fases

- **Prod:** Repetir playbook en producción (region: eze, escalado: 2 VMs shared-cpu-1x).
- **Monitoreo:** Activar alertas en Prometheus/Grafana.
- **Backups:** Verificar pg_dump diario y retención 7 días.
