# 🗺️ DEPLOYMENT DECISION MAP - Oct 26, 2025

> **Estado:** 🟢 Todos los sistemas listos para Staging
> **Próximo Paso:** Ejecutar staging interactivo
> **Tiempo Estimado:** 45 min (completo) | 10 min (redeploys)

---

## ⚡ TL;DR - Comandos Rápidos

### Si tienes prisa (automated flow):
```bash
# 1) Llenar env/.env.fly.staging manualmente
vim env/.env.fly.staging

# 2) Todo automático
./ops/staging-deploy-interactive.sh  # Selecciona opciones 2-7 secuencialmente
```

### Si quieres control total (manual flow):
```bash
# 1) Secretos
cp env/.env.fly.staging.template env/.env.fly.staging
vim env/.env.fly.staging
./ops/set_fly_secrets.sh sist-cabanas-mvp env/.env.fly.staging

# 2) Deploy
flyctl deploy --remote-only --strategy rolling -a sist-cabanas-mvp

# 3) Validar
./ops/smoke_and_benchmark.sh https://sist-cabanas-mvp.fly.dev
RUN_MUTATING=1 PYTHONPATH=backend python backend/scripts/concurrency_overlap_test.py ...
```

---

## 📊 Estado Actual (Oct 26, 03:50 UTC)

| Componente | Status | Última Acción |
|-----------|--------|--------------|
| **Backend Código** | ✅ 100% | Commit d30d11f |
| **Fly.toml** | ✅ Configurado | app: sist-cabanas-mvp, region: eze |
| **Docker** | ✅ Listo | start-fly.sh, health checks |
| **Pre-Deploy Validación** | ✅ 7/7 Pass | validate_predeploy.py |
| **Playbooks** | ✅ Completos | 4 playbooks + quick-start |
| **Scripts de Deploy** | ✅ Listos | set_fly_secrets.sh, smoke_and_benchmark.sh |
| **Secretos en Fly** | ⏳ Pendiente | Requiere filling .env.fly.staging |
| **App Desplegada** | ⏳ Pendiente | Requiere flyctl deploy |
| **Staging Validada** | ⏳ Pendiente | Health + benchmark + overlap |
| **Producción Ready** | ⏸️ After Staging | 24h estabilidad mínimo |

---

## 🎯 DECISION TREE: ¿Dónde estamos y qué hacer?

```
┌─────────────────────────────────────────────────────────────┐
│                    STAGING DEPLOYMENT                        │
│                    Oct 26, 2025 - Ready                      │
└─────────────────────────────────────────────────────────────┘
                              │
                    ¿Tienes credenciales?
                    /              \
                   YES              NO
                    │               │
                    │        1) Obtén:
                    │        - DATABASE_URL (Fly Postgres)
                    │        - REDIS_URL (Upstash)
                    │        - JWT_SECRET (generate)
                    │        - WhatsApp token
                    │        - MercadoPago token
                    │
                    ▼
        ┌─────────────────────────────┐
        │ PASO 1: Fill Secrets        │
        │ cp env/.env.fly.staging...  │
        │ vim env/.env.fly.staging    │
        └─────────────────────────────┘
                    │
        ¿Secretos válidos?
                    │
                    ▼
        ┌─────────────────────────────┐
        │ PASO 2: Validar Fly         │
        │ flyctl auth whoami          │
        │ flyctl status -a sist-ca... │
        └─────────────────────────────┘
                    │
        ¿Fly OK?
                    │
                    ▼
        ┌─────────────────────────────┐
        │ PASO 3: Cargar Secretos     │
        │ ./ops/set_fly_secrets...    │
        │ flyctl secrets list         │
        └─────────────────────────────┘
                    │
        ▼ Secretos en Fly
        ┌─────────────────────────────┐
        │ PASO 4: Deploy              │
        │ flyctl deploy --remote-only │
        │ Ver logs 30seg              │
        └─────────────────────────────┘
                    │
        Deploy OK? (Health checks passing)
           /    \
          YES    NO → Rollback/Fix (ver troubleshooting)
          │
          ▼
        ┌─────────────────────────────┐
        │ PASO 5: Smoke Tests         │
        │ curl /healthz, /readyz      │
        │ ./ops/smoke_and_benchmark   │
        └─────────────────────────────┘
                    │
        p95 < 3s? error-rate < 1%?
           /    \
          YES    NO → Debug (ver INCIDENT_RESPONSE_RUNBOOK)
          │
          ▼
        ┌─────────────────────────────┐
        │ PASO 6: Anti-Doble-Booking  │
        │ concurrency_overlap_test.py │
        │ Expect: 1 fail (constraint) │
        └─────────────────────────────┘
                    │
        1 falla por constraint?
           /    \
          YES    NO → Fix constraint (ver schema)
          │
          ▼
        ┌──────────────────────────────────┐
        │ ✅ STAGING READY                 │
        │ Documentar reporte               │
        │ Esperar 24h sin errores críticos │
        └──────────────────────────────────┘
                    │
        ▼ Después de 24h estable
        ┌──────────────────────────────────┐
        │ PROD READINESS CHECKLIST         │
        │ ops/PROD_READINESS_CHECKLIST.md │
        └──────────────────────────────────┘
```

---

## 🎓 Rutas de Acción por Perfil

### 👨‍💼 Ejecutivo / Gestor
**Tarea:** Verificar que staging está listo

```bash
# Comando único
flyctl status -a sist-cabanas-mvp
curl -s https://sist-cabanas-mvp.fly.dev/api/v1/healthz | python -m json.tool

# Resultado esperado: status: "healthy"
# Tiempo: ~5 min
```

---

### 👨‍💻 DevOps / SRE
**Tarea:** Deploy completo + observabilidad

```bash
# 1) Setup (si es primera vez)
./ops/staging-deploy-interactive.sh
# O manual:
./ops/set_fly_secrets.sh sist-cabanas-mvp env/.env.fly.staging
flyctl deploy --remote-only -a sist-cabanas-mvp

# 2) Monitoring
flyctl logs -a sist-cabanas-mvp -f
# Ctrl+C después de 30 seg

# 3) Benchmark
./ops/smoke_and_benchmark.sh https://sist-cabanas-mvp.fly.dev

# Tiempo total: ~25 min
```

---

### 🔐 Security / QA
**Tarea:** Validación de seguridad + anti-overlap

```bash
# 1) Secretos bien cargados
flyctl secrets list -a sist-cabanas-mvp
# Verificar: JWT_SECRET, WHATSAPP_ACCESS_TOKEN, MERCADOPAGO_ACCESS_TOKEN

# 2) Anti-overlap
RUN_MUTATING=1 PYTHONPATH=backend python backend/scripts/concurrency_overlap_test.py \
    --base-url https://sist-cabanas-mvp.fly.dev \
    --accommodation-id 1 \
    --check-in 2025-11-15 \
    --check-out 2025-11-17 \
    --concurrency 5

# Resultado esperado: 4 exitosas (201), 1 falla (409 Conflict)

# Tiempo: ~10 min
```

---

## 📋 Archivos Clave Por Paso

| Paso | Archivo | Propósito |
|------|---------|----------|
| Secrets | `env/.env.fly.staging.template` | Plantilla de variables |
| Setup | `ops/set_fly_secrets.sh` | Automatizar carga a Fly |
| Deploy | `fly.toml` | Configuración Fly (ya listo) |
| Validar | `ops/smoke_and_benchmark.sh` | Health + perf checks |
| Test | `backend/scripts/concurrency_overlap_test.py` | Anti-overlap validator |
| Report | Auto-generado | Markdown report |
| Docs | `ops/STAGING_DEPLOYMENT_PLAYBOOK.md` | Documentación detallada |
| Guide | `ops/STAGING_DEPLOYMENT_QUICK_START.md` | Guía paso a paso |
| Menu | `ops/staging-deploy-interactive.sh` | Menú interactivo |

---

## ⚙️ Variables Requeridas en `.env.fly.staging`

```bash
# Base de datos (Fly PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Cache (Upstash Redis)
REDIS_URL=redis://:pass@host:port

# Security
JWT_SECRET=<random-64-chars>
WHATSAPP_APP_SECRET=<from-meta>

# Canales
WHATSAPP_ACCESS_TOKEN=<from-meta>
WHATSAPP_BUSINESS_ACCOUNT_ID=<from-meta>
MERCADOPAGO_ACCESS_TOKEN=<from-mercadopago>

# Admin
ADMIN_ALLOWED_EMAILS=admin@example.com,ops@example.com

# Optional (defaults si no especificadas)
ENVIRONMENT=staging
LOG_LEVEL=INFO
GUNICORN_WORKERS=2
```

---

## 🚨 Señales de Alerta

| Señal | Causa Probable | Acción |
|-------|---|--------|
| Health check returns 503 | DB/Redis no conecta | Ver logs: `flyctl logs -a ...` |
| Latency p95 > 10s | DB lentitud o N+1 queries | Revisar query logs en INCIDENT_RESPONSE_RUNBOOK |
| Anti-overlap test: 0 fallas | Constraint no activo | Verificar schema: `EXCLUDE USING gist` |
| Deploy stuck 5+ min | Alembic migration lenta | Rollback: `flyctl releases rollback` |
| Secretos no aparecen en logs | Variables no interpoladas | Revisar que SECRET=env_var en Dockerfile |

---

## 🔄 Ciclo de Feedback Rápido

1. **Deploy** → 2 min
2. **Smoke tests** → 2 min
3. **Benchmark** → 1 min
4. **Report** → 1 min
5. **Análisis** → 5-10 min

**Total:** ~15 min por iteración de cambio

---

## 📞 Si Algo Falla

### Opción A: Rollback Automático
```bash
flyctl releases -a sist-cabanas-mvp
flyctl releases rollback -a sist-cabanas-mvp  # Reversa a versión anterior
```

### Opción B: Ver Detalles
```bash
# Logs completos
flyctl logs -a sist-cabanas-mvp --lines 500

# Status detallado
flyctl status -a sist-cabanas-mvp

# Métricas
curl -s https://sist-cabanas-mvp.fly.dev/metrics | grep error_rate
```

### Opción C: Usar Runbook
- `ops/INCIDENT_RESPONSE_RUNBOOK.md` → buscar escenario específico
- `ops/DISASTER_RECOVERY.md` → si DB está corrupta

---

## ✨ Éxito esperado después de 45 min

```
✅ App desplegada en https://sist-cabanas-mvp.fly.dev
✅ Health check: 200 OK
✅ p95 latency: < 3s
✅ Error rate: 0%
✅ Anti-doble-booking: Activo (1 falla por constraint)
✅ Logs: Sin errores críticos
✅ Reporte: Guardado en backend/docs/

SIGUIENTE: Esperar 24h estabilidad → Producción
```

---

## 🎯 Próximas Fases (Post-Staging)

### Fase 2: Production Promotion (Oct 27-28)
- [ ] Completar `PROD_READINESS_CHECKLIST.md` (10 items)
- [ ] Blue-green deploy con 2 VMs en Fly
- [ ] Health checks 24h antes de cutover
- [ ] Comms al equipo: "Going live at [tiempo]"

### Fase 3: Post-Production (Oct 28+)
- [ ] Monitoring 24/7 en Grafana
- [ ] Alertas en Slack/email
- [ ] Incident response drills

---

**Listo para comenzar? Ejecuta:**
```bash
./ops/staging-deploy-interactive.sh
```

O si prefieres manual:
```bash
vim env/.env.fly.staging
./ops/set_fly_secrets.sh sist-cabanas-mvp env/.env.fly.staging
flyctl deploy --remote-only -a sist-cabanas-mvp
```

🚀 **¡Vamos!**
