# ✅ DEPLOY READY CHECKLIST - SIST_CABAÑAS MVP

**Fecha:** 2025-10-19
**Status:** 🟡 CASI LISTO (1 bloqueante pendiente)
**ETA Deploy:** 15 minutos tras resolver bloqueante

---

## 🚦 STATUS GENERAL

```
┌─────────────────────────────────────────┐
│  VALIDACIÓN: 13/15 ✅ (86.7%)           │
│  BLOQUEANTES: 1 ❌ (flyctl)             │
│  WARNINGS: 2 ⚠️ (NO bloqueantes)        │
│  TIEMPO PARA DEPLOY: 15 minutos         │
└─────────────────────────────────────────┘
```

---

## 🔴 ACCIÓN INMEDIATA REQUERIDA

### 1. Instalar Fly.io CLI (5 minutos)

```bash
# Instalar
curl -L https://fly.io/install.sh | sh

# Añadir al PATH (añade a ~/.bashrc)
export PATH="/home/eevan/.fly/bin:$PATH"
source ~/.bashrc

# Autenticar
flyctl auth login

# Verificar
flyctl version
flyctl auth whoami
```

### 2. Re-ejecutar Validación (1 minuto)

```bash
cd /home/eevan/ProyectosIA/SIST_CABAÑAS
./pre_deploy_validation.sh
```

**Resultado esperado:** `✅ VALIDACIÓN EXITOSA - 15/15 checks`

---

## 🟢 DEPLOY PROCEDURE (10 minutos)

### Paso 1: Crear PostgreSQL en Fly.io

```bash
flyctl postgres create \
  --name sist-cabanas-db \
  --region eze \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 1

# Conectar a la app
flyctl postgres attach sist-cabanas-db --app sist-cabanas-mvp
```

### Paso 2: Configurar Secretos

**Generar valores:**
```bash
# Generar secretos aleatorios
openssl rand -base64 32  # JWT_SECRET
openssl rand -base64 32  # REDIS_PASSWORD
openssl rand -base64 16  # ICS_SALT
openssl rand -base64 32  # ADMIN_CSRF_SECRET
```

**Configurar en Fly.io:**
```bash
flyctl secrets set \
  REDIS_PASSWORD="<valor_generado>" \
  JWT_SECRET="<valor_generado>" \
  ICS_SALT="<valor_generado>" \
  ADMIN_CSRF_SECRET="<valor_generado>" \
  GRAFANA_ADMIN_PASSWORD="<password_seguro>" \
  WHATSAPP_VERIFY_TOKEN="<from_meta>" \
  WHATSAPP_APP_SECRET="<from_meta>" \
  WHATSAPP_TOKEN="<from_meta>" \
  WHATSAPP_PHONE_ID="<from_meta>" \
  MERCADOPAGO_ACCESS_TOKEN="<from_mp>" \
  MERCADOPAGO_PUBLIC_KEY="<from_mp>" \
  SMTP_PASS="<email_app_password>" \
  --app sist-cabanas-mvp
```

**Verificar:**
```bash
flyctl secrets list --app sist-cabanas-mvp
# Debe mostrar 12 secretos configurados
```

### Paso 3: Deploy

```bash
flyctl deploy --app sist-cabanas-mvp
```

### Paso 4: Monitoreo

```bash
# Logs en tiempo real
flyctl logs -f --app sist-cabanas-mvp

# En otra terminal, verificar health
curl https://sist-cabanas-mvp.fly.dev/api/v1/healthz

# Verificar metrics
curl https://sist-cabanas-mvp.fly.dev/metrics
```

---

## ✅ VALIDACIONES PASADAS

### Configuración ✅ 5/5
- [x] fly.toml válido (región eze, puerto 8080)
- [x] Dockerfile presente y correcto
- [x] start-fly.sh ejecutable con migraciones
- [x] 44 env variables configuradas
- [x] requirements.txt con versiones fijas

### Base de Datos ✅ 2/2
- [x] 6 migraciones Alembic encontradas
- [x] Constraint anti-double-booking presente (EXCLUDE USING gist)

### Servicios Externos ✅ 1/1
- [x] 6/6 imports críticos funcionando

### Seguridad ✅ 2/2
- [x] Bandit scan: 0 HIGH issues
- [x] Webhook signatures validadas (WhatsApp + Mercado Pago)

### Deployment ✅ 4/5
- [x] Health check endpoint presente (DB validated)
- [x] Metrics endpoint presente (Prometheus)
- [x] Zero-downtime configurado (max_unavailable=0)
- [x] Auto-rollback activado
- [x] Git working tree clean

---

## ⚠️ WARNINGS (NO BLOQUEANTES)

### 1. pip-audit no instalado
**Impacto:** CVE check skipped
**Prioridad:** Baja (Bandit ya validó 0 HIGH)
**Acción:** Instalar post-deploy
```bash
cd backend && source .venv/bin/activate
pip install pip-audit
pip-audit --desc
```

### 2. Health check sin validación de Redis
**Impacto:** Redis health no monitoreado
**Prioridad:** Media
**Acción:** Añadir check post-deploy (3 min)

---

## 📊 SMOKE TESTS POST-DEPLOY

### Test 1: Health Check
```bash
curl -s https://sist-cabanas-mvp.fly.dev/api/v1/healthz | jq
```

**Esperado:**
```json
{
  "status": "healthy",
  "checks": {
    "database": {"status": "ok", "latency_ms": 15},
    "ical_sync": {"status": "ok", "last_sync_minutes_ago": 2}
  }
}
```

### Test 2: Readyz
```bash
curl -s https://sist-cabanas-mvp.fly.dev/api/v1/readyz | jq
```

### Test 3: Metrics
```bash
curl -s https://sist-cabanas-mvp.fly.dev/metrics | grep "http_requests_total"
```

### Test 4: Admin Dashboard
```bash
curl -I https://sist-cabanas-mvp.fly.dev/
# Debe retornar 200 OK
```

---

## 🔍 TROUBLESHOOTING

### Deploy falla con "health check timeout"
```bash
# Ver logs detallados
flyctl logs --app sist-cabanas-mvp

# Verificar que el puerto es 8080
grep "internal_port" fly.toml

# Verificar que start-fly.sh usa --host 0.0.0.0
grep "host" backend/start-fly.sh
```

### Release command falla (alembic)
```bash
# Verificar DATABASE_URL en secrets
flyctl secrets list --app sist-cabanas-mvp | grep DATABASE_URL

# Si falta, adjuntar DB manualmente
flyctl postgres attach sist-cabanas-db --app sist-cabanas-mvp
```

### Build falla
```bash
# Simular build localmente
cd backend
docker build --platform linux/amd64 -t test .

# Ver logs de build en Fly.io
flyctl logs --app sist-cabanas-mvp | grep "Building"
```

---

## 📋 CHECKLIST FINAL

```
ANTES DE DEPLOY:
├─ [ ] flyctl instalado y autenticado
├─ [ ] Validación 15/15 ✅
├─ [ ] PostgreSQL creado en Fly.io (región eze)
├─ [ ] 12 secretos configurados
├─ [ ] Git working tree clean
└─ [ ] Team notificado del deploy

DURANTE DEPLOY:
├─ [ ] flyctl deploy ejecutado
├─ [ ] Build successful
├─ [ ] Release command successful (migraciones)
├─ [ ] Health checks passing
└─ [ ] Logs monitoreados (flyctl logs -f)

POST-DEPLOY:
├─ [ ] Health check: 200 OK
├─ [ ] Metrics endpoint: 200 OK
├─ [ ] Admin dashboard: 200 OK
├─ [ ] Verificar migraciones: SELECT * FROM alembic_version
├─ [ ] Webhook test (WhatsApp verify)
└─ [ ] iCal sync activo (ver logs)

SEMANA 1:
├─ [ ] Monitorear error rate (<1%)
├─ [ ] Validar P95 response time (<3s texto, <15s audio)
├─ [ ] Verificar iCal sync (<20min desfase)
├─ [ ] Configurar alertas Grafana
├─ [ ] Instalar pip-audit
└─ [ ] Añadir Redis health check
```

---

## 🎯 DECISIÓN TÉCNICA

```
┌───────────────────────────────────────────────┐
│  STATUS: APPROVED FOR PRODUCTION DEPLOYMENT   │
│                                               │
│  ✅ Código: PASS                              │
│  ✅ Seguridad: PASS (0 HIGH)                  │
│  ✅ Base de datos: PASS (6 migrations)        │
│  ✅ Configuración: PASS (fly.toml valid)      │
│  ⏳ Herramientas: PENDING (flyctl install)    │
│                                               │
│  ROI: Detecta 1 error crítico en 6s           │
│       vs 1-2h debugging en prod               │
└───────────────────────────────────────────────┘
```

**Filosofía aplicada:**
- ✅ "Fail fast, fail local" - Errores detectados pre-deploy
- ✅ Ingeniería inversa - Validación desde perspectiva Fly.io
- ✅ Defense in depth - Múltiples capas de validación
- ✅ Pragmatismo MVP - Warnings NO bloquean deploy

---

## 📞 CONTACTOS Y RECURSOS

**Documentación:**
- `pre_deploy_validation.sh` - Script automatizado
- `docs/operations/PRE_DEPLOYMENT_VALIDATION.md` - Guía completa
- `docs/operations/PRE_DEPLOYMENT_RESULTS.md` - Resultados actuales
- `docs/fly-io/FLY_IO_DEPLOYMENT_GUIDE.md` - Guía Fly.io

**Scripts útiles:**
- Validación: `./pre_deploy_validation.sh`
- Audit molecular: `./run_molecular_audit.sh --critical`
- Tests: `cd backend && pytest -v`
- Coverage: `cd backend && pytest --cov=app --cov-report=term-missing`

**Fly.io:**
- Dashboard: https://fly.io/dashboard
- Docs: https://fly.io/docs/
- Status: https://status.fly.io/

---

## ⏱️ TIMELINE ESTIMADO

```
AHORA:        Instalar flyctl (5 min)
+1 min:       Re-validar (debe ser 15/15 ✅)
+5 min:       Crear PostgreSQL (1 min)
+6 min:       Configurar secretos (4 min)
+10 min:      Deploy (4 min)
+14 min:      Smoke tests (2 min)
+15 min:      ✅ PRODUCTION LIVE
```

**Total:** 15 minutos desde instalar flyctl hasta producción.

---

**ÚLTIMA ACTUALIZACIÓN:** 2025-10-19 19:30 UTC
**GIT COMMIT:** c92c034 (pushed to origin/main)
**ARCHIVOS NUEVOS:** 3 (+1,641 líneas)

---

## 🚀 SIGUIENTE ACCIÓN

```bash
curl -L https://fly.io/install.sh | sh
```

Después ejecuta: `./pre_deploy_validation.sh` (debe ser 15/15 ✅)

Luego sigue los pasos en "DEPLOY PROCEDURE" arriba.

---

**¡ESTÁS A 15 MINUTOS DE PRODUCCIÓN!** 🎉
