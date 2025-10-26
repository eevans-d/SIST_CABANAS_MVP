# ✅ GO/NO-GO STAGING CHECKLIST

> **Propósito:** Verificación final antes de flyctl deploy
> **Audiencia:** DevOps, PM, Tech Lead
> **Frecuencia:** Una vez antes de cada deploy

---

## 🔴 BLOQUEADORES CRÍTICOS (Must Pass)

### ✅ Git & Code Quality
- [ ] `git log -1` muestra último commit sin cambios pending
- [ ] `flyctl version` >= 0.0.x (compatible con app name)
- [ ] Archivo `fly.toml` existe y tiene app: "sist-cabanas-mvp"
- [ ] `backend/Dockerfile` tiene PORT=8080 y llamada a start-fly.sh
- [ ] `backend/start-fly.sh` valida DB_URL, REDIS_URL, corre alembic

**Command:**
```bash
git status --porcelain | wc -l  # Debe ser 0
python backend/scripts/validate_predeploy.py
```

**Resultado esperado:** `✅ 7/7 checks pass`

---

### ✅ Fly Infrastructure
- [ ] App "sist-cabanas-mvp" existe en Fly (`flyctl apps list`)
- [ ] PostgreSQL addon attached (check: `flyctl status -a sist-cabanas-mvp`)
- [ ] REDIS_URL está definida en `env/.env.fly.staging`
- [ ] Usuario autenenticado en Fly (`flyctl auth whoami`)

**Commands:**
```bash
flyctl auth whoami
flyctl apps list | grep sist-cabanas-mvp
flyctl status -a sist-cabanas-mvp
```

**Resultado esperado:**
```
Username: [tu-usuario]
sist-cabanas-mvp running
```

---

### ✅ Secretos Completos
- [ ] `env/.env.fly.staging` existe y tiene mínimo 8 variables
- [ ] Validación: `bash -c "set -a; source env/.env.fly.staging; echo $JWT_SECRET" | wc -c` > 10
- [ ] DATABASE_URL es válido (postgresql://...)
- [ ] REDIS_URL es válido (redis://...)
- [ ] JWT_SECRET tiene >= 32 caracteres

**Validation:**
```bash
bash -c 'set -a; source env/.env.fly.staging; set +a; \
  echo "JWT_SECRET: ${#JWT_SECRET} chars"; \
  echo "DB_URL starts with: ${DATABASE_URL:0:20}"; \
  echo "REDIS: ${REDIS_URL:0:20}"'
```

**Resultado esperado:**
```
JWT_SECRET: 64 chars
DB_URL starts with: postgresql://
REDIS: redis://:
```

---

### ✅ Alembic Migrations
- [ ] Archivo `backend/alembic/env.py` existe
- [ ] Última migración en `backend/alembic/versions/` es válida Python
- [ ] No hay migraciones pendientes en git uncommitted

**Commands:**
```bash
ls -1 backend/alembic/versions/ | tail -1
grep -c "def upgrade" backend/alembic/versions/[last-file].py  # Debe ser 1
```

---

## 🟡 ADVERTENCIAS (Should Pass)

### ⚠️ Observabilidad
- [ ] `backend/app/main.py` tiene línea `prometheus_instrumentator().instrument_app(app)`
- [ ] `/metrics` endpoint documentado en docstring
- [ ] `/healthz` y `/readyz` existen en routers

**Check:**
```bash
grep -q "prometheus_instrumentator" backend/app/main.py && echo "✅" || echo "❌"
grep -q "def healthz" backend/app/routers/*.py && echo "✅" || echo "❌"
```

---

### ⚠️ Webhooks Firmados
- [ ] `WhatsApp X-Hub-Signature-256` validation en `backend/app/routers/webhooks.py`
- [ ] Mercado Pago `x-signature` validation en webhook handler
- [ ] Tests de firma fallida (403 Forbidden) existen

**Check:**
```bash
grep -q "X-Hub-Signature-256" backend/app/routers/webhooks.py && echo "✅" || echo "❌"
grep -q "verify.*signature" backend/app/services/*.py && echo "✅" || echo "❌"
```

---

### ⚠️ Anti-Doble-Booking Constraint
- [ ] Database schema tiene extensión `btree_gist`
- [ ] Tabla `reservations` tiene columna `period` GENERATED
- [ ] EXCLUDE constraint activo con `USING gist` y `WHERE status IN (pre_reserved, confirmed)`
- [ ] Script de test: `backend/scripts/concurrency_overlap_test.py` ejecuta

**Check:**
```bash
grep -q "btree_gist" backend/alembic/versions/*.py && echo "✅" || echo "❌"
python -m py_compile backend/scripts/concurrency_overlap_test.py && echo "✅" || echo "❌"
```

---

## 🟢 VERIFICACIONES PRE-DEPLOY (Final)

### 🔍 Checklist Final (60 segundos antes de `flyctl deploy`)

```bash
echo "=== PRE-DEPLOY CHECKLIST (60s) ==="
echo ""

echo "1. Git limpio?"
git status --porcelain | wc -l

echo "2. Fly authenticado?"
flyctl auth whoami

echo "3. App existe?"
flyctl apps list | grep sist-cabanas-mvp

echo "4. Secretos cargados?"
flyctl secrets list -a sist-cabanas-mvp | wc -l

echo "5. Env vars válidos?"
bash -c "set -a; source env/.env.fly.staging; set +a; echo JWT_SECRET: \${#JWT_SECRET} chars"

echo "6. Alembic OK?"
ls -1 backend/alembic/versions/ | tail -1

echo ""
echo "✅ Todos los checks pasaron? Ejecuta:"
echo "flyctl deploy --remote-only --strategy rolling -a sist-cabanas-mvp"
```

---

## 🚨 GO / NO-GO Decision Gate

### ✅ GO si:
- ✅ Todos los **BLOQUEADORES CRÍTICOS** pasaron
- ✅ Al menos 6/7 **ADVERTENCIAS** pasaron
- ✅ Git status limpio
- ✅ Secretos completos en `env/.env.fly.staging`
- ✅ PM/Tech Lead aprobó deploy

### 🛑 NO-GO si:
- ❌ Cualquier **BLOQUEADOR CRÍTICO** falló
- ❌ Git tiene cambios uncommitted en código core
- ❌ DATABASE_URL o REDIS_URL faltante
- ❌ Validación predeploy falló < 6/7
- ❌ Issues críticos en GitHub (P1/blocker)

---

## 📊 Matriz de Decisión

| Estado | Acción |
|--------|--------|
| 🟢 GO (todos green) | Ejecutar `flyctl deploy` |
| 🟡 WARNING (algunos yellow) | Revisar y decidir caso por caso |
| 🔴 NO-GO (algún red) | DETENER - fix issue, re-test |

---

## 📝 Sign-Off Template

Completar ANTES de cada deploy:

```markdown
## Staging Deploy Sign-Off
Date: 2025-10-XX
Deployed by: [nombre]
Approved by: [PM/Tech Lead]

### Pre-Deploy Checks
- [ ] Git commits 3b3cfd7, 3fc949c, d30d11f present
- [ ] All predeploy validations: 7/7 pass
- [ ] Secrets loaded to Fly: 8+ variables
- [ ] No critical GitHub issues (P1/blocker)
- [ ] Tech Lead approval obtained

### Deploy Details
- App: sist-cabanas-mvp
- Region: eze (Ezeiza, Argentina)
- Strategy: rolling (with auto-rollback)
- Estimated time: 2-5 min

### Expected Results
- Health check: 200 OK
- p95 latency: < 3s
- Error rate: 0%
- Anti-overlap: active (1 expected fail)

### Rollback Plan
If issues detected within 5 min:
- Automatic rollback by Fly (health-checks)
- Manual: `flyctl releases rollback -a sist-cabanas-mvp`

### Approval
PM: ________________  Date: _______
Tech Lead: ________________  Date: _______
```

---

## 🔄 Post-Deploy Verification (After Deploy)

### Esperar ~3 minutos, luego ejecutar:

```bash
# 1) Health check
curl -v https://sist-cabanas-mvp.fly.dev/api/v1/healthz

# 2) Log tail
flyctl logs -a sist-cabanas-mvp -f

# 3) Metrics
curl -s https://sist-cabanas-mvp.fly.dev/metrics | head -20

# 4) Error count
curl -s https://sist-cabanas-mvp.fly.dev/metrics | grep -i error
```

**Esperado:**
- ✅ Status 200 + "healthy"
- ✅ Logs muestran "Started instance" + "Health check passing"
- ✅ Métricas = Prometheus bien formado
- ✅ Error count = 0

---

## 🎯 Quick Reference Cards

### Card 1: 30-Second Go/No-Go
```bash
# Ejecutar JUSTO ANTES de flyctl deploy
bash -c '\
  echo "1. Git:" && git status --porcelain | wc -l && \
  echo "2. Fly Auth:" && flyctl auth whoami | cut -d: -f2 && \
  echo "3. App:" && flyctl status -a sist-cabanas-mvp | head -1 && \
  echo "4. Secrets:" && flyctl secrets list -a sist-cabanas-mvp | wc -l && \
  echo "✅ Ready to deploy!"
'
```

### Card 2: Post-Deploy 5-Min Validation
```bash
# Esperar 3 min después de ver "Health check passing" en logs
BASE_URL="https://sist-cabanas-mvp.fly.dev"
echo "Health:" && curl -s $BASE_URL/api/v1/healthz | jq .status
echo "Ready:" && curl -s $BASE_URL/api/v1/readyz | jq .status
echo "Metrics:" && curl -s $BASE_URL/metrics | wc -l
```

### Card 3: Troubleshooting Decision Tree
```
Deploy Falló?
├─ Logs show "Connection refused" → Redis/DB no conecta (fix secrets)
├─ Logs show "ImportError" → Falta dependency (check requirements.txt)
├─ Logs show "Alembic error" → Migration falló (rollback + fix schema)
├─ Health check returns 503 → Wait 1 min, retry (puede estar inicializando)
└─ Status shows "unhealthy" → Rollback: flyctl releases rollback -a sist-cabanas-mvp
```

---

## 📞 Emergency Contacts

| Escenario | Contacto | Acción |
|-----------|----------|--------|
| Deploy stuck 10+ min | Tech Lead | Trigger: `flyctl releases rollback` |
| DB corrupted | DBA | Refer: `ops/DISASTER_RECOVERY.md` Scenario A |
| Double-booking detected | Product | Contact: Webhook logs + incident RCA |
| Critical CVE | Security | Ref: `ops/INCIDENT_RESPONSE_RUNBOOK.md` |

---

**Status:** 🟢 READY FOR STAGING DEPLOY

Ejecuta cuando estés listo:
```bash
./ops/staging-deploy-interactive.sh
# O
flyctl deploy --remote-only -a sist-cabanas-mvp
```
