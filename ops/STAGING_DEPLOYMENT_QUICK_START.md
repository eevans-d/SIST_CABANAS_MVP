# 🚀 STAGING DEPLOYMENT GUIDE (Interactive)

> **Objetivo:** Desplegar MVP a staging en Fly.io con validaciones y benchmark.
> **Tiempo:** ~45 min (primero) | ~10 min (redeploys)
> **Prerequisito:** Completar Jornada 26 Oct (playbooks + validaciones)

---

## ✅ Pre-Staging Checklist

Antes de empezar:

- [ ] Verificaste que todos los cambios de Jornada 26 Oct están committeados (`git log -1`)
- [ ] Tienes acceso a Fly.io (`flyctl auth whoami`)
- [ ] Tienes credenciales de:
  - [ ] Fly Postgres (DATABASE_URL)
  - [ ] Upstash Redis (REDIS_URL)
  - [ ] WhatsApp (tokens)
  - [ ] Mercado Pago (tokens)

---

## 📋 PASO 1: Preparar Secretos (5 min)

### 1.1) Copiar plantilla
```bash
cp env/.env.fly.staging.template env/.env.fly.staging
```

### 1.2) Completar valores reales
```bash
# Editar con tu editor favorito
vim env/.env.fly.staging

# Debe tener (mínimo):
# DATABASE_URL=postgresql://...
# REDIS_URL=redis://:...
# JWT_SECRET=<random-secure>
# WHATSAPP_ACCESS_TOKEN=...
# MERCADOPAGO_ACCESS_TOKEN=...
# ADMIN_ALLOWED_EMAILS=...
```

### 1.3) Validar sintaxis
```bash
bash -c 'set -a; source env/.env.fly.staging; set +a; echo "✅ Env vars loaded"'
```

**Esperado:** `✅ Env vars loaded` sin errores

---

## 📦 PASO 2: Verificar Servicios en Fly (3 min)

### 2.1) Verificar app existe
```bash
flyctl status -a sist-cabanas-mvp
```

**Esperado:** Estado de la app (si no existe, crear: `flyctl apps create sist-cabanas-mvp --org personal`)

### 2.2) Verificar Postgres adjunto
```bash
flyctl postgres status -a sist-cabanas-db
```

**Esperado:** Status "ok"

### 2.3) Verificar Upstash Redis
- URL debe estar en `REDIS_URL` del archivo

---

## 🔐 PASO 3: Cargar Secretos a Fly (2 min)

### 3.1) Usar script automatizado
```bash
./ops/set_fly_secrets.sh sist-cabanas-mvp env/.env.fly.staging
```

**Esperado:** `✅ Secretos cargados en app: sist-cabanas-mvp`

### 3.2) Verificar
```bash
flyctl secrets list -a sist-cabanas-mvp | head -10
```

**Esperado:** Al menos 8 secretos listados (sin valores)

---

## 🚀 PASO 4: Desplegar (5 min)

### 4.1) Deploy
```bash
flyctl deploy --remote-only --strategy rolling -a sist-cabanas-mvp
```

**Esperado:** Progreso en vivo, sin errores

### 4.2) Monitorear logs
```bash
# En otra terminal, ver logs en vivo
flyctl logs -a sist-cabanas-mvp -f

# Esperar ~30 segundos hasta ver "Health check passing"
# Presionar Ctrl+C para salir
```

**Esperado en logs:**
```
Starting app initialization...
Running migrations...
Started instance ffd12...
Listening on 0.0.0.0:8080
✅ Health check passing
```

---

## 🔍 PASO 5: Validaciones (Smoke) (3 min)

### 5.1) Health Check Manual
```bash
curl -s https://sist-cabanas-mvp.fly.dev/api/v1/healthz | python -m json.tool
```

**Esperado:**
```json
{
  "status": "healthy",
  "checks": {
    "database": {"status": "ok"},
    "redis": {"status": "ok"}
  }
}
```

### 5.2) Readiness
```bash
curl -s https://sist-cabanas-mvp.fly.dev/api/v1/readyz | python -m json.tool
```

**Esperado:** `{"status": "ready", ...}`

### 5.3) Metrics
```bash
curl -s https://sist-cabanas-mvp.fly.dev/metrics | head -10
```

**Esperado:** Líneas con `# HELP` y métricas Prometheus

---

## ⚡ PASO 6: Benchmark Runtime (5 min)

### 6.1) Ejecutar script
```bash
./ops/smoke_and_benchmark.sh https://sist-cabanas-mvp.fly.dev
```

**Esperado:**
```
✅ /healthz: avg 45ms, p95 120ms
✅ /readyz: avg 12ms, p95 30ms
✅ /metrics: avg 20ms, p95 50ms
✅ /accommodations: avg 35ms, p95 100ms

Error rate: 0%
```

### 6.2) SLOs Validados?
- p95 < 3s ✅
- error-rate < 1% ✅

---

## 🔄 PASO 7: Validar Anti-Doble-Booking (3 min)

### 7.1) Crear datos de prueba (si es primera vez)
```bash
# Ver si existe acomodación con ID 1
curl -s https://sist-cabanas-mvp.fly.dev/api/v1/accommodations | python -m json.tool

# Si no hay, seedear localmente (futuro: hacer vía API)
```

### 7.2) Ejecutar carrera de doble-booking
```bash
RUN_MUTATING=1 PYTHONPATH=backend python backend/scripts/concurrency_overlap_test.py \
  --base-url https://sist-cabanas-mvp.fly.dev \
  --accommodation-id 1 \
  --check-in 2025-11-15 \
  --check-out 2025-11-17 \
  --concurrency 2
```

**Esperado:**
```
Attempt 1: 201 Created (pre-reserva exitosa)
Attempt 2: 409 Conflict (overlap detectado por constraint) ✅
```

---

## 📊 PASO 8: Registrar Reporte (2 min)

```bash
# Copiar reporte de benchmark
cat > backend/docs/RUNTIME_REPORT_STAGING_$(date +%Y-%m-%d).md << 'EOF'
# Runtime Report - Staging (Fly.io)

Fecha: $(date)
Base URL: https://sist-cabanas-mvp.fly.dev
Ambiente: staging

## Resultados Benchmark

[Pega la salida de smoke_and_benchmark.sh aquí]

## SLOs

- p95 /healthz: < 200ms ✅
- p95 /accommodations: < 3s ✅
- error-rate: 0% ✅

## Anti-Doble-Booking

[Pega resultado de concurrency_overlap_test aquí]

## Status Final

✅ STAGING READY FOR PRODUCTION PROMOTION
EOF
```

---

## ✅ CHECKLIST DE CIERRE STAGING

- [ ] App desplegada en Fly
- [ ] Health checks: 200 OK
- [ ] Metrics: accesible
- [ ] Benchmark: p95 < 3s
- [ ] Error-rate: 0%
- [ ] Anti-doble-booking: ✅ (1 falla por constraint)
- [ ] Reporte guardado en `backend/docs/`
- [ ] Logs revisados (sin errores críticos)
- [ ] Git actualizado (si cambios)

---

## 🚨 Troubleshooting

### Health Check Falla
```bash
# Ver DB status
flyctl postgres status -a sist-cabanas-db

# Verificar secrets
flyctl secrets list -a sist-cabanas-mvp | grep DATABASE_URL

# Ver logs detallados
flyctl logs -a sist-cabanas-mvp --lines 200
```

### Deploy Stuck
```bash
# Restart
flyctl restart -a sist-cabanas-mvp

# O rollback
flyctl releases -a sist-cabanas-mvp
flyctl releases rollback -a sist-cabanas-mvp
```

### Benchmark Timeout
- Red lenta: esperar más
- Check DB/Redis connection en healthz
- Restart app si hangs

---

## 📞 Contactos

| Caso | Acción |
|------|--------|
| Desconocido | Rollback: `flyctl releases rollback -a sist-cabanas-mvp` |
| DB error | Ver `ops/DISASTER_RECOVERY.md` sección "Escenario A" |
| Webhook failed | Ver `ops/INCIDENT_RESPONSE_RUNBOOK.md` |

---

## ✨ Próxima Fase: Producción

Si staging está sano 24h+ sin errores:
- [ ] Usar `ops/PROD_READINESS_CHECKLIST.md`
- [ ] Completar checklist 100%
- [ ] Usar `ops/STAGING_DEPLOYMENT_PLAYBOOK.md` pero con `sist-cabanas-prod` en lugar de `sist-cabanas-mvp`
- [ ] Blue-green deploy con 2 VMs

---

**Duración estimada total:** 45 min (primero) | 10 min (redeploys)
**Status:** 🟢 LISTO PARA COMENZAR
