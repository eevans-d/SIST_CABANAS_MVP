# 📑 SIST CABAÑAS MVP - DOCUMENTACIÓN INDEX (Canónico)

> Este índice es la única fuente de verdad para documentación vigente.
> Cualquier guía duplicada en la raíz fue reemplazada por punteros a estas referencias o marcada como ARCHIVADA (histórico).
>
> **Última actualización:** Octubre 31, 2025 - 19:00 UTC
> **Estado:** 🟢 **MVP BACKEND COMPLETE** | 🔶 **FRONTEND UX EN DESARROLLO**
> **Fase actual:** Implementando Dashboard Admin (Fase 1 UX Master Plan)

---

## 🗺️ Mapa de Navegación Rápida

### 💡 PLAN UX MASTER (NUEVO)
```
1. Lee: ops/UX_MASTER_PLAN_ADMIN_GUEST.md (Plan exhaustivo 3 fases)
2. Fase 1: Admin Dashboard (3-5 días) - EN CURSO
3. Fase 2: Guest WhatsApp UX (3-5 días)
4. Fase 3: Polish Técnico (2-3 días)
```

### 🚀 QUIERO DESPLEGAR AHORA
```
1. Lee: ops/GO_NO_GO_CHECKLIST.md (5 min)
2. Ejecuta: ./ops/staging-deploy-interactive.sh (45 min)
3. O manual: Sigue ops/STAGING_DEPLOYMENT_QUICK_START.md (30 min)
```

### 🎯 QUIERO ENTENDER TODO
```
1. ops/DEPLOYMENT_DECISION_MAP.md (visual + quick commands)
2. ops/STAGING_DEPLOYMENT_PLAYBOOK.md (detallado)
3. backend/docs/DEPLOYMENT_SUMMARY.md (status actual)
4. ops/BLUEPRINT_CHECKLIST_OPTIMIZACION_UX.md (plan post-MVP)
```

### � Contribuciones y Ramas

- Política de rama única: trabajamos sobre `main` (PRs opcionales; requeridos para cambios riesgosos).
- Guía completa: ver `CONTRIBUTING.md`.

### �🔥 ALGO FALLÓ
```
1. ops/INCIDENT_RESPONSE_RUNBOOK.md (7 escenarios comunes)
2. ops/DISASTER_RECOVERY.md (si DB está corrupta)
3. Luego: Rollback automático o manual
```

### ✅ PRODUCCIÓN LISTA
```
1. ops/PROD_READINESS_CHECKLIST.md (10 verificaciones)
2. Esperar 24h estabilidad en staging
3. Ejecutar en sist-cabanas-prod
```

---

## 📚 DOCUMENTACIÓN ORGANIZÓ POR FASE

### 🏗️ FASE 1: PRE-REQUISITOS (Antes de Deploy)

| Archivo | Propósito | Duración |
|---------|----------|----------|
| `ops/GO_NO_GO_CHECKLIST.md` | ✅ Verificación final pre-deploy | 5 min |
| `env/.env.fly.staging.template` | 🔑 Plantilla de secretos a llenar | 10 min |
| `ops/DEPLOYMENT_DECISION_MAP.md` | 🗺️ Árbol de decisiones + comandos | 3 min |
| `ops/GUIA_OBTENER_SECRETOS_PASO_A_PASO.md` | 🔐 Guía paso a paso: dónde obtener CADA secreto/API key/URL | 20 min |

**Punto de partida:** GUIA_OBTENER_SECRETOS_PASO_A_PASO.md (luego GO_NO_GO_CHECKLIST)

---

### 🚀 FASE 2: DEPLOYMENT (Deploy a Staging)

| Archivo | Propósito | Duración |
|---------|----------|----------|
| `ops/staging-deploy-interactive.sh` | 🎯 **RECOMENDADO**: Menú interactivo 11 pasos | 45 min |
| `ops/STAGING_DEPLOYMENT_QUICK_START.md` | 📋 Guía step-by-step sin herramienta | 30 min |
| `ops/STAGING_DEPLOYMENT_PLAYBOOK.md` | 📖 Manual detallado con troubleshooting | 60 min |

**Punto de partida:** Interactive script (más fácil)

---

### ✔️ FASE 3: VALIDACIÓN (Verificación Post-Deploy)

| Archivo | Propósito | Duración |
|---------|----------|----------|
| `ops/smoke_and_benchmark.sh` | ⚡ Health checks + p95 latency | 5 min |
| `backend/scripts/concurrency_overlap_test.py` | 🔄 Validar anti-doble-booking | 3 min |
| `ops/STAGING_DEPLOYMENT_QUICK_START.md` (PASO 6-8) | 📊 Guía de validación integrada | 15 min |

**Punto de partida:** PASO 6 del quick-start o manual validation

---

### 📊 FASE 4: MONITOREO (Después de Deploy)

| Archivo | Propósito | Duración |
|---------|----------|----------|
| `ops/STAGING_BENCHMARK_PLAN.md` | 📈 Plan de benchmark con SLOs | 30 min |
| Prometheus `/metrics` | 📉 Métricas en vivo | Contínuo |
| `flyctl logs -a sist-cabanas-mvp -f` | 📝 Logs en tiempo real | Contínuo |

**Punto de partida:** Comando de logs

---

### 🚨 FASE 5: INCIDENTS (Si Algo Falla)

| Archivo | Propósito | Caso de Uso |
|---------|----------|----------|
| `ops/INCIDENT_RESPONSE_RUNBOOK.md` | 🔧 Diagnosis + fix para 7 escenarios | Error rate alto, latencia, DB error |
| `ops/DISASTER_RECOVERY.md` | 💾 Backup/restore procedures | DB corrupted, data loss |
| `flyctl releases rollback` | ⏮️ Rollback automático | Deploy falló, health check 503 |

**Punto de partida:** INCIDENT_RESPONSE_RUNBOOK

---

### ✅ FASE 6: PRODUCCIÓN (Después de 24h Estabilidad)

| Archivo | Propósito | Checklist |
|---------|----------|----------|
| `ops/PROD_READINESS_CHECKLIST.md` | ✅ 10 verificaciones finales | Before cutover |
| `ops/STAGING_DEPLOYMENT_PLAYBOOK.md` (adapt) | 📖 Mismo proceso pero en prod | On production app |
| Comms Plan | 📢 Notificar al equipo | Status page + Slack |

**Punto de partida:** PROD_READINESS_CHECKLIST

---

## 🔧 ARCHIVOS POR CATEGORÍA

### 🎨 FASE 7: OPTIMIZACIÓN/UX (Post-MVP)

| Archivo | Propósito | Duración |
|---------|----------|----------|
| `ops/BLUEPRINT_CHECKLIST_OPTIMIZACION_UX.md` | 🧭 Blueprint por fases (A–F) para mejoras de UX, API, obs y seguridad | 5 min lectura |
| `frontend/admin-dashboard/README.md` | 🚪 Quick Start del Admin (React + Vite + Tailwind) | 5 min |
| `frontend/admin-dashboard/DEPLOYMENT_STATUS.md` | 📌 Estado y notas de despliegue del Admin | 3 min |

**Punto de partida:** Blueprint UX + README del Admin

---

### 📋 Checklists
```
✅ ops/GO_NO_GO_CHECKLIST.md
✅ ops/PROD_READINESS_CHECKLIST.md
✅ ops/FLY_DEPLOY_CHECKLIST.md
```

### 📖 Guías Step-by-Step
```
📍 ops/STAGING_DEPLOYMENT_QUICK_START.md (RECOMENDADO FIRST)
📍 ops/STAGING_DEPLOYMENT_PLAYBOOK.md (detallado)
📍 ops/DEPLOYMENT_DECISION_MAP.md (visual tree)
📍 CONTRIBUTING.md (política de ramas y contribuciones)
```

### 🛠️ Scripts Ejecutables
```
🔧 ./ops/staging-deploy-interactive.sh (RECOMENDADO - menú interactivo)
🔧 ./ops/set_fly_secrets.sh (cargar secretos a Fly)
🔧 ./ops/smoke_and_benchmark.sh (validar health + perf)
🔧 python backend/scripts/concurrency_overlap_test.py (anti-overlap)
🔧 python backend/scripts/deployment_dashboard.py (status visual)
```

### 🗂️ Plantillas & Configuración
```
📝 env/.env.fly.staging.template (LLENAR CON TUS SECRETOS)
📝 env/.env.example (comprehensive reference)
📝 fly.toml (app config - ya existe)
📝 backend/Dockerfile (container setup - ya existe)
```

### 📊 Runbooks & Procedures
```
🚨 ops/INCIDENT_RESPONSE_RUNBOOK.md (7 escenarios de error)
💾 ops/DISASTER_RECOVERY.md (backup/restore)
📈 ops/STAGING_BENCHMARK_PLAN.md (perf validation)
```

### 📚 Matriz de Secretos
```
🔐 ops/FLY_SECRETS_MATRIX.md (qué secreto va dónde)
```

### 📈 Reportes
```
📄 backend/docs/DEPLOYMENT_SUMMARY.md (auto-generado)
📄 JORNADA_26OCT_RESUMEN_FINAL.md (summary hoy)
🎨 ops/BLUEPRINT_CHECKLIST_OPTIMIZACION_UX.md (plan UX post-MVP)
```

---

## 🚀 FLUJO RECOMENDADO (Primeras Veces)

```
┌──────────────────────────────────────────────────────────┐
│  1. LEE: GO_NO_GO_CHECKLIST.md (5 min - verificar)       │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│  2. LLENA: env/.env.fly.staging (10 min - manual)        │
│     Copia plantilla + añade credenciales reales          │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│  3. EJECUTA: ./ops/staging-deploy-interactive.sh (45min) │
│     Menu interactivo que guía cada paso                  │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│  4. VALIDA: Health checks, benchmark, anti-overlap (10m) │
│     Menu step 6-8 del script interactivo                 │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│  5. MONITOREA: Logs 24h sin errores críticos             │
│     flyctl logs -a sist-cabanas-mvp -f                   │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│  6. PROMOCIONA: PROD_READINESS_CHECKLIST + go live       │
│     Cuando todo OK y 24h estable                         │
└──────────────────────────────────────────────────────────┘

Total tiempo: ~2h (incluye monitor inicial)
```

---

## 📞 ATAJOS POR PERFIL

### 👨‍💼 PM / Ejecutivo
```
Quiero saber: ¿Cuándo estamos en producción?
Lee: ops/DEPLOYMENT_DECISION_MAP.md (2 min)
Verifica: python backend/scripts/deployment_dashboard.py (1 min)
Resultado: Status 🟢 READY → puedes programar go-live
```

### 👨‍💻 DevOps / Técnico Líder
```
Quiero desplegar e iterar rápido
Ejecuta: ./ops/staging-deploy-interactive.sh
Monitorea: flyctl logs -a sist-cabanas-mvp -f
Valida: ./ops/smoke_and_benchmark.sh [URL]
```

### 🔐 Security / QA Lead
```
Quiero validar seguridad y anti-overlap
Lee: ops/GO_NO_GO_CHECKLIST.md (Secretos section)
Ejecuta: RUN_MUTATING=1 python backend/scripts/concurrency_overlap_test.py
Revisa: ops/INCIDENT_RESPONSE_RUNBOOK.md (para contingencies)
```

### 📊 Operations / SRE
```
Quiero monitoreo y runbooks
Guarda: ops/INCIDENT_RESPONSE_RUNBOOK.md (bookmark)
Acceso: Prometheus /metrics endpoint
Checks: Daily + post-deploy + on-call
```

---

## ❓ PREGUNTAS FRECUENTES

### "¿Por dónde empiezo?"
→ Ejecuta: `python backend/scripts/deployment_dashboard.py`
→ Luego: `./ops/staging-deploy-interactive.sh`

### "¿Qué debo llenar antes?"
→ Lee: `ops/GO_NO_GO_CHECKLIST.md` (BLOQUEADORES CRÍTICOS section)
→ Llena: `env/.env.fly.staging` (copy template + valores reales)

### "¿Cuánto tiempo toma?"
→ Primera vez: ~45 min (deploy + validaciones)
→ Re-deploys: ~10 min (si solo cambios de código)

### "¿Qué pasa si falla?"
→ Rollback automático si health checks fallan
→ Manual: `flyctl releases rollback -a sist-cabanas-mvp`
→ Detalle: `ops/INCIDENT_RESPONSE_RUNBOOK.md`

### "¿Cuándo paso a producción?"
→ Después: 24h estabilidad en staging
→ Verifica: `ops/PROD_READINESS_CHECKLIST.md` (100% complete)
→ Ejecuta: mismo proceso pero en `sist-cabanas-prod` app

### "¿Cómo valido anti-doble-booking?"
→ Script: `python backend/scripts/concurrency_overlap_test.py`
→ Esperado: 1 falla (409 Conflict por constraint) + N éxitos

### "¿Dónde están los metrics?"
→ Vivo: `https://sist-cabanas-mvp.fly.dev/metrics`
→ Dashboard: Prometheus (si está configurado)

---

## 📊 ESTADO ACTUAL

```
✅ Backend MVP: 100% complete
✅ Operaciones: 4 playbooks ready
✅ Automation: 6+ scripts tested
✅ Pre-Deploy: 7/7 validations pass
✅ Git: Clean, all commits pushed
⏳ Staging: Ready to deploy
⏳ Production: After 24h staging OK
```

---

## 🎯 MILESTONES

| Fecha | Hito | Status |
|-------|------|--------|
| Oct 26 (Hoy) | ✅ Prep complete | **DONE** |
| Oct 26-27 | Deploy staging | **PENDING** |
| Oct 27-28 | Validate (24h+) | **PENDING** |
| Oct 28 | Production go-live | **PENDING** |

---

## 🆘 HELP!

| Problema | Solución |
|----------|----------|
| No sé por dónde empezar | → `python backend/scripts/deployment_dashboard.py` |
| Deploy falló | → `ops/INCIDENT_RESPONSE_RUNBOOK.md` Scenario 1 |
| DB no conecta | → `ops/INCIDENT_RESPONSE_RUNBOOK.md` Scenario 3 |
| Anti-overlap no funciona | → `ops/INCIDENT_RESPONSE_RUNBOOK.md` Scenario 7 |
| Quiero rollback | → `flyctl releases rollback -a sist-cabanas-mvp` |
| Necesito desastres recovery | → `ops/DISASTER_RECOVERY.md` |

---

## 🔗 QUICK LINKS

**Start Here:**
- [Guía Obtener Secretos (PRIMERO)](./ops/GUIA_OBTENER_SECRETOS_PASO_A_PASO.md)
- [GO/NO-GO Checklist](./ops/GO_NO_GO_CHECKLIST.md)
- [Interactive Deployment Script](./ops/staging-deploy-interactive.sh)

**Deploy Docs:**
- [Quick Start (30 min)](./ops/STAGING_DEPLOYMENT_QUICK_START.md)
- [Full Playbook (60 min)](./ops/STAGING_DEPLOYMENT_PLAYBOOK.md)
- [Decision Tree](./ops/DEPLOYMENT_DECISION_MAP.md)
- [Plan Completo Fly.io + UX Admin](./ops/PLAN_COMPLETO_FLYIO_UX_ADMIN.md)
 - [Blueprint-Checklist 100% (paso a paso)](./ops/BLUEPRINT_CHECKLIST_100_PORCIENTO.md)

**Operations:**
- [Incident Response](./ops/INCIDENT_RESPONSE_RUNBOOK.md)
- [Disaster Recovery](./ops/DISASTER_RECOVERY.md)
- [Production Readiness](./ops/PROD_READINESS_CHECKLIST.md)

**Tools:**
- [Status Dashboard](./backend/scripts/deployment_dashboard.py)
- [Smoke & Benchmark](./ops/smoke_and_benchmark.sh)
- [Overlap Test](./backend/scripts/concurrency_overlap_test.py)

**Frontend Admin:**
- [Admin Dashboard README](./frontend/admin-dashboard/README.md)
- [Blueprint UX/Optimización](./ops/BLUEPRINT_CHECKLIST_OPTIMIZACION_UX.md)

**QA & Testing (Minimax M2 Integration):**
- [Testing Report Oct 29](./docs/qa/MINIMAX_TESTING_REPORT_2025-10-29.md) - E2E, Performance, Security
- [Integrations Analysis](./docs/integrations/integrations_analysis.md) - Mercado Pago, WhatsApp
- [TODO Metadata](../.memory/todo_meta.json) - Progress tracking Fase 2A

**Repository Status:**
- [Sync Status Report](./REPO_SYNC_STATUS.md) - main vs master consolidation (Oct 30)

---

**Estado Final:** 🟢 **READY FOR STAGING** | 📋 **Repository Consolidated (Oct 30)**

Ejecuta: `./ops/staging-deploy-interactive.sh` o lee `ops/STAGING_DEPLOYMENT_QUICK_START.md`

---

*Generated: Oct 30, 2025 - 07:45 UTC*
*Git: integration/minimax-work (consolidating branches)*
*Latest: Minimax testing reports integrated*

---

### 🧭 Docs footer

- Contribuciones y política de ramas: `CONTRIBUTING.md`
- Guardas de despliegue (costos): `ops/deploy-check.sh` y `ops/STAGING_DEPLOYMENT_QUICK_START.md`
