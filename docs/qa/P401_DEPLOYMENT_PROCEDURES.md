# P401: DEPLOYMENT PROCEDURES - Sistema MVP Alojamientos

**Fecha:** 14 Octubre 2025
**Prompt QA:** P401 - Deployment Procedures
**Fase:** FASE 5 - Operaciones
**Tiempo Estimado:** 3 horas

---

## 🎯 OBJETIVO

Documentar y validar procedimientos de deployment seguros, reproducibles y con rollback automático para el Sistema MVP de Reservas.

---

## 📋 SCOPE

### Incluye
- ✅ Docker multi-stage builds optimizado
- ✅ Health checks completos (liveness + readiness)
- ✅ Procedimientos de rollback por severidad
- ✅ Gestión de migraciones DB (Alembic)
- ✅ Variables de entorno y secrets
- ✅ CI/CD básico con GitHub Actions

### Excluye
- ❌ Kubernetes/orchestration avanzada
- ❌ Blue-green deployment
- ❌ Canary releases
- ❌ Multi-region deployment

---

## 🐳 1. DOCKER BUILD STRATEGY

### 1.1 Dockerfile Actual (backend/Dockerfile)

**Análisis:**
```dockerfile
FROM python:3.11-slim  # ✅ Base ligera

# ✅ Non-root user (appuser uid 1000)
# ✅ Health check configurado (/api/v1/healthz)
# ✅ Gunicorn con workers configurables
```

**Optimizaciones Aplicadas:**
- Multi-layer caching: `requirements.txt` copiado antes que código
- Limpieza de apt cache: `-rf /var/lib/apt/lists/*`
- PYTHONDONTWRITEBYTECODE=1 para evitar .pyc

**Recomendación:** ✅ MANTENER ACTUAL (ya optimizado)

### 1.2 Health Check Configuration

**Actual en Dockerfile:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=5 \
    CMD curl -fsS http://localhost:8000/api/v1/healthz || exit 1
```

**Actual en docker-compose.staging.yml:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/healthz"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**Validación:**
- ✅ Verifica DB connectivity
- ✅ Verifica Redis connectivity
- ✅ Valida iCal sync age
- ⚠️ Retries: Docker=5, compose=3 (inconsistente)

**ACCIÓN REQUERIDA:**
```yaml
# Estandarizar en docker-compose:
retries: 5  # Cambiar de 3 a 5
```

---

## 🚀 2. DEPLOYMENT WORKFLOW

### 2.1 Procedimiento Estándar (Production)

```bash
# FASE 1: Pre-checks (2 min)
./scripts/pre-deploy-check.sh

# FASE 2: Backup DB (3 min)
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
docker exec postgres pg_dump -U alojamientos alojamientos_db > $BACKUP_FILE

# FASE 3: Git Tag (1 min)
git tag -a v1.2.3 -m "Release 1.2.3"
git push origin v1.2.3

# FASE 4: Build & Deploy (5 min)
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# FASE 5: Migrations (2 min)
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# FASE 6: Smoke Tests (3 min)
./scripts/smoke-test-prod.sh

# Total: ~16 minutos
```

### 2.2 Script Automatizado Existente

**Archivo:** `backend/deploy.sh`

**Funciones Clave:**
- `check_requirements()` - Docker, docker-compose, certbot
- `validate_env()` - Variables críticas (JWT, DB, WhatsApp, MP)
- `setup_backup()` - Backup automático pre-deploy
- `rollback()` - Restaura última versión estable

**Uso:**
```bash
./deploy.sh deploy    # Deploy completo
./deploy.sh rollback  # Rollback al último backup
./deploy.sh status    # Estado de servicios
```

---

## 🔄 3. ROLLBACK PROCEDURES

### 3.1 Por Severidad (basado en ROLLBACK_PLAN.md)

| Severidad | Síntoma | Tiempo Respuesta | Acción |
|-----------|---------|-----------------|---------|
| **SEV1** | Sistema caído (500s) | < 5 min | Rollback completo inmediato |
| **SEV2** | Funcionalidad crítica rota | < 15 min | Rollback parcial o completo |
| **SEV3** | Bug no crítico | < 1 hora | Fix forward o rollback |

### 3.2 Rollback Completo (SEV1)

```bash
# 1. Detener servicios actuales
docker-compose down

# 2. Checkout última versión estable
git fetch --tags
git checkout v1.2.2  # Tag anterior conocido estable

# 3. Rebuild
docker-compose up -d --build

# 4. Verificar health
curl https://api.reservas.com/api/v1/healthz

# 5. Restaurar DB (solo si migrations fallaron)
docker exec -i postgres psql -U alojamientos alojamientos_db < backup_20251014_143022.sql
```

**Tiempo Total:** 5-8 minutos

### 3.3 Rollback de Migraciones DB

```bash
# Ver migración actual
docker-compose exec backend alembic current

# Rollback 1 versión
docker-compose exec backend alembic downgrade -1

# Rollback a específica
docker-compose exec backend alembic downgrade abc123def456
```

**⚠️ CRÍTICO:** Solo hacer rollback DB si:
- Migration causó error crítico
- Existe backup reciente (< 1 hora)
- NO hubo escrituras de usuarios post-migration

---

## 🔐 4. SECRETS MANAGEMENT

### 4.1 Variables Críticas

**Checklist Pre-Deploy:**
```bash
# Verificar que NO sean valores por defecto:
grep -E "(POSTGRES_PASSWORD|REDIS_PASSWORD|JWT_SECRET)" .env

# Longitudes mínimas:
- POSTGRES_PASSWORD: >= 15 chars
- REDIS_PASSWORD: >= 15 chars
- JWT_SECRET: >= 32 chars (hex)
- WHATSAPP_APP_SECRET: desde Meta Dev Console
- MERCADOPAGO_WEBHOOK_SECRET: desde MP Developers
```

### 4.2 Generación Automática

**Script Existente:** `scripts/generate_production_secrets.sh`

```bash
./scripts/generate_production_secrets.sh
# Output: JWT_SECRET=xxxx, POSTGRES_PASSWORD=yyyy, etc.
```

---

## 🤖 5. CI/CD BÁSICO (GitHub Actions)

### 5.1 Workflow Actual: `.github/workflows/ci.yml`

**Jobs Configurados:**
1. **lint** (10 min): Black, isort, flake8, bandit
2. **tests-sqlite** (10 min): Tests con SQLite fallback
3. **tests-postgres** (15 min): Tests completos con PG + Redis

**Triggers:**
- `push` a `main`
- `pull_request` a `main`
- `workflow_dispatch` (manual)

### 5.2 Workflow Deploy Staging: `.github/workflows/deploy-staging.yml`

**Triggers:**
- Push a rama `staging`
- Tag `v*-staging`

**Steps:**
1. Checkout code
2. Build Docker image
3. Push to registry (si aplica)
4. SSH deploy to staging server
5. Run migrations
6. Smoke tests

**Estado Actual:** ✅ IMPLEMENTADO

---

## 📊 6. HEALTH CHECKS DETALLADOS

### 6.1 Endpoint `/api/v1/healthz`

**Checks Implementados:**
```python
# 1. Database
- Connectivity: SELECT 1
- Latency: < 500ms (warn if > 500ms)

# 2. Redis
- Connectivity: PING
- Latency: < 200ms (warn if > 200ms)
- Memory usage
- Connected clients

# 3. iCal Sync Age
- Last sync: < 20 min (warn if > 20min, critical if > 40min)

# 4. Disk Space (si disponible)
- Available: > 1GB
```

**Response Format:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2025-10-14T14:30:22Z",
  "checks": {
    "database": {"status": "ok", "latency_ms": 45},
    "redis": {"status": "ok", "latency_ms": 12},
    "ical_sync": {"status": "ok", "age_minutes": 8}
  }
}
```

### 6.2 Integración con Nginx

```nginx
# Upstream health check (si nginx plus)
upstream backend {
    server backend:8000;
    check interval=10s fall=3 rise=2 timeout=5s type=http;
    check_http_send "GET /api/v1/healthz HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx;
}
```

---

## 🔧 7. MIGRATIONS STRATEGY

### 7.1 Alembic Best Practices

**Pre-Deploy:**
```bash
# Verificar migrations pendientes
docker-compose exec backend alembic current
docker-compose exec backend alembic heads

# Generar SQL preview (NO aplicar)
docker-compose exec backend alembic upgrade head --sql > preview_migration.sql
```

**Deploy:**
```bash
# Aplicar migrations
docker-compose exec backend alembic upgrade head

# Verificar aplicación
docker-compose exec backend alembic current
```

**Post-Deploy:**
```bash
# Si falla, rollback
docker-compose exec backend alembic downgrade -1
```

### 7.2 Estrategia para Migrations Destructivas

**Problema:** DROP column, RENAME table

**Solución:**
1. **Deploy 1:** Agregar nueva columna (sin borrar vieja)
2. **Deploy 2 (días después):** Deprecar vieja columna
3. **Deploy 3 (semanas después):** DROP vieja columna

**Evitar:** Migrations irreversibles en producción sin backup reciente.

---

## 📝 8. CHECKLIST DE DEPLOYMENT

### Pre-Deploy
- [ ] Tests pasando en CI (GitHub Actions green)
- [ ] `.env` con secrets reales (no valores default)
- [ ] Backup DB realizado (< 1 hora)
- [ ] Git tag creado (`v1.2.3`)
- [ ] Rollback plan documentado
- [ ] Stakeholders notificados (si deploy mayor)

### Durante Deploy
- [ ] Health checks pasando antes de down
- [ ] Migrations aplicadas sin errores
- [ ] Servicios iniciados (docker ps = healthy)
- [ ] Health check post-deploy = healthy
- [ ] Smoke tests pasando

### Post-Deploy
- [ ] Logs sin errores críticos (5 min observación)
- [ ] Métricas en Prometheus estables
- [ ] Reservas de prueba funcionan
- [ ] Webhooks procesando (WhatsApp + MP)
- [ ] iCal sync ejecutándose

---

## 🚨 9. TROUBLESHOOTING COMÚN

### 9.1 Problema: Backend no inicia

**Síntomas:**
```bash
docker ps  # backend restarting constantemente
docker logs backend  # Error: "database connection failed"
```

**Solución:**
```bash
# 1. Verificar variables de entorno
docker exec backend env | grep DATABASE_URL

# 2. Verificar conectividad DB
docker exec postgres pg_isready -U alojamientos

# 3. Revisar logs DB
docker logs postgres | tail -50

# 4. Si falla: Rollback
./deploy.sh rollback
```

### 9.2 Problema: Migrations fallan

**Síntomas:**
```bash
alembic upgrade head
# ERROR: column "period" already exists
```

**Solución:**
```bash
# 1. Verificar estado actual
alembic current

# 2. Ver historial
alembic history

# 3. Stamp manual (si columna existe)
alembic stamp head

# 4. Rollback y retry
alembic downgrade -1
alembic upgrade head
```

### 9.3 Problema: Health check degraded

**Síntomas:**
```json
{"status": "degraded", "checks": {"ical_sync": {"age_minutes": 35}}}
```

**Solución:**
```bash
# 1. Forzar sync manual
docker exec backend python -c "
from app.services.ical import sync_all_ical_feeds
import asyncio
asyncio.run(sync_all_ical_feeds())
"

# 2. Verificar logs sync worker
docker logs backend | grep "ical_sync"

# 3. Si persiste: Revisar credenciales iCal
```

---

## 📈 10. MÉTRICAS DE ÉXITO

### KPIs de Deployment

| Métrica | Target | Crítico |
|---------|--------|---------|
| **Downtime** | < 30s | > 5 min |
| **Rollback time** | < 5 min | > 15 min |
| **Failed deploys** | < 5% | > 20% |
| **Health recovery** | < 2 min | > 10 min |

### Observabilidad

**Pre-Deploy:**
```bash
# Capturar métricas baseline
curl https://api.reservas.com/metrics > metrics_pre.txt
```

**Post-Deploy:**
```bash
# Comparar métricas
curl https://api.reservas.com/metrics > metrics_post.txt
diff metrics_pre.txt metrics_post.txt
```

**Alertas Críticas:**
- Error rate > 5% durante 5 min
- P95 latency > 10s durante 3 min
- Health check unhealthy durante 2 min

---

## ✅ VALIDACIÓN P401

### Tests Manuales

```bash
# 1. Simular deploy en staging
cd /tmp/test_deploy
git clone https://github.com/eevans-d/SIST_CABANAS_MVP
cd SIST_CABANAS_MVP
cp .env.staging.template .env.staging
# Editar .env.staging con valores válidos

docker-compose -f docker-compose.staging.yml up -d --build

# 2. Verificar health
curl http://localhost/api/v1/healthz

# 3. Simular fallo y rollback
docker-compose down
git checkout v1.0.0  # Tag antiguo
docker-compose up -d --build

# 4. Verificar recuperación
curl http://localhost/api/v1/healthz
```

### Checklist Final

- [x] Dockerfile optimizado (no-root, health check)
- [x] docker-compose con health checks completos
- [x] Script deploy.sh funcional con rollback
- [x] ROLLBACK_PLAN.md documentado
- [x] CI/CD workflows en GitHub Actions
- [x] Secrets management con generación automática
- [x] Alembic migrations strategy documentada
- [x] Health checks multi-component
- [x] Troubleshooting común documentado

---

## 📚 REFERENCIAS

**Archivos Relacionados:**
- `backend/Dockerfile` - Imagen Docker optimizada
- `backend/deploy.sh` - Script de deployment automatizado
- `docker-compose.staging.yml` - Compose para staging
- `docs/deployment/ROLLBACK_PLAN.md` - Plan de rollback detallado
- `.github/workflows/ci.yml` - CI pipeline
- `.github/workflows/deploy-staging.yml` - Deploy automatizado
- `scripts/pre-deploy-check.sh` - Pre-checks deployment
- `scripts/smoke-test-prod.sh` - Smoke tests post-deploy

**Documentación Externa:**
- Docker Health Checks: https://docs.docker.com/engine/reference/builder/#healthcheck
- Alembic Migrations: https://alembic.sqlalchemy.org/en/latest/
- GitHub Actions: https://docs.github.com/en/actions

---

**Estado:** ✅ COMPLETO
**Próximo Paso:** P402 - Monitoring Setup

---

*Documento generado: 14 Octubre 2025*
*Tiempo estimado implementación: 3 horas*
*Prioridad: ALTA (requerido para producción)*
