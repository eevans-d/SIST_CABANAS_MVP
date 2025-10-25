# Plan Modular de Ingeniería Inversa (Advanced) – SIST_CABAÑAS MVP

Fecha: 2025-10-24
Alcance: Corroborar, verificar y descubrir aspectos críticos/relevantes del sistema con máxima eficiencia y precisión.
Resultado esperado: Evidencias claras (artefactos), gaps/prioridades y lista de acciones.

---

## Guía rápida (TL;DR)
- Módulo 1 – Código y Contratos (estático): Inventario, contratos, esquemas, constraints, configuración, dependencias.
- Módulo 2 – Runtime y Operación (dinámico): Arranque, routing, jobs, locks, métricas, salud, migraciones, DB/Redis.
- Módulo 3 – Integraciones y Seguridad (interfaces): Webhooks (WhatsApp/MP), iCal, correo, idempotencia, firmas, rate limits, amenazas.

Cada módulo define: objetivos, entradas, outputs (artefactos), criterios de éxito, comandos/consultas y riesgos.

---

## Módulo 1 — Código y Contratos (Análisis Estático)

Objetivos
- Corroborar estructura real del monolito (FastAPI + SQLAlchemy Async) y del frontend admin (Vite/React).
- Extraer contratos críticos: modelos ORM, esquemas, constraints anti-doble-booking, DTOs de routers, contratos NLU.
- Mapear configuración y secretos requeridos; revisar migrations.

Entradas
- Árbol del repo, `backend/app/**`, `backend/tests/**`, `frontend/admin-dashboard/**`, `fly.toml`, `docker-compose*.yml`, `pyproject.toml`, `pytest.ini`, `docs/**`.

Artefactos (outputs)
- INVENTARIO_CODIGO.csv (rutas clave y conteos)
- CONTRATOS_CORE.md (modelos/routers/DTOs resumidos)
- DB_CONSTRAINTS.md (lista de constraints, en especial EXCLUDE gist)
- CONFIG_MATRIX.md (vars entorno, secretos, defaults, orígenes)
- MIGRATIONS_MAP.md (orden y cambios por migration)

Criterios de éxito
- Constraints anti overlap confirmadas y copiadas fielmente (daterange + EXCLUDE gist + filtro por estado).
- Lista de secretos y orígenes (env/fly/secrets) completa.
- Mapeo de endpoints/routers y modelos principales.

Comandos/Consultas sugeridos
```bash
# 1. Inventario general
ls -la && tree -L 3 backend app 2>/dev/null || true

# 2. Buscar constraints anti-doble-booking
rg -n "EXCLUDE USING gist|daterange\(|btree_gist" backend/

# 3. Rutas/routers
rg -n "@router\.(get|post|put|delete)\(" backend/app/routers

# 4. Modelos y migraciones
rg -n "class .*\(Base\)|Column\(|ForeignKey\(|relationship\(" backend/app/models
ls backend/database/migrations 2>/dev/null || true

# 5. Config/secretos
rg -n "os\.environ|getenv|BaseSettings" backend/app | sed -n '1,200p'

# 6. Frontend admin
cat frontend/admin-dashboard/package.json
cat frontend/admin-dashboard/vite.config.ts
```

Riesgos/Focos
- Inconsistencias entre migraciones y modelos.
- Config duplicada o no documentada.
- Dependencias críticas con versiones conflictivas (pydantic, SQLAlchemy, aiosqlite/asyncpg).

---

## Módulo 2 — Runtime y Operación (Análisis Dinámico)

Objetivos
- Validar el comportamiento en tiempo de ejecución: arranque, health, ready, métricas, rutas, trabajos en background, locks Redis.
- Verificar release/migrations, latencias y SLOs base.
- Corroborar iCal sync y workers.

Entradas
- Scripts operacionales existentes: `pre_deploy_validation.sh`, `activation_complete.sh`, `fase_1/2/3`.
- Ambiente local/staging o Fly (app `sist-cabanas-mvp`).

Artefactos (outputs)
- RUNTIME_REPORT.md (arranque, tiempos, logs relevantes)
- ROUTES_LIST.json (rutas detectadas dinámicamente)
- JOBS_STATUS.md (workers activos, frecuencias, última ejecución)
- METRICS_SNAPSHOT.txt (subset de /metrics útil)
- HEALTH_HISTORY.csv (histórico de health/readiness durante 5–10 min)

Criterios de éxito
- Health/Ready 200; métricas expuestas; release sin errores.
- Migraciones aplicadas; tabla/índices esperados presentes.
- Locks Redis funcionan (al menos simulación/validación por logs o pruebas unitarias relevantes).

Comandos/Consultas sugeridos
```bash
# 1. Validación pre-deploy
./pre_deploy_validation.sh

# 2. Deploy y logs (si en Fly)
flyctl deploy --app sist-cabanas-mvp --strategy immediate
flyctl logs -f --app sist-cabanas-mvp | sed -n '1,200p'
flyctl status --app sist-cabanas-mvp

# 3. Health/Ready/Metrics (producción o local)
curl -s https://<host>/api/v1/healthz | jq .
curl -s https://<host>/api/v1/readyz | jq .
curl -s https://<host>/metrics | head -50

# 4. Base de datos (via SSH en Fly)
flyctl ssh console --app sist-cabanas-mvp <<'EOF'
psql "$DATABASE_URL" -c "\dt+"
psql "$DATABASE_URL" -c "\di+"
EOF
```

Riesgos/Focos
- Health verde pero background workers fallando silenciosamente.
- Latencias elevadas por cold start o librerías pesadas (Whisper).
- Métricas incompletas o sin etiquetas clave (channel, status).

---

## Módulo 3 — Integraciones y Seguridad (Interfaces)

Objetivos
- Verificar contratos de firmas y seguridad: WhatsApp (X-Hub-Signature-256), Mercado Pago (x-signature), idempotencia, rate limiting.
- Corroborar contratos NLU, audio/Whisper pipeline, iCal import/export, email.

Entradas
- `backend/app/routers/*` y `services/*` (whatsapp.py, mercadopago.py, ical.py, audio.py, nlu.py).
- Documentos en `docs/operations/*`, `docs/integrations/*`, `docs/security/*`.

Artefactos (outputs)
- WEBHOOK_SECURITY_CHECKLIST.md (firmas, normalización, ejemplos canonizados)
- IDEMPOTENCY_CASES.md (claves idempotentes, TTLs, escenarios de reintento)
- INTEGRATIONS_MATRIX.md (credenciales, secretos, endpoints, estados)

Criterios de éxito
- Validación de firmas reproducible localmente (ejemplos curl con firma correcta/incorrecta).
- Casuística de idempotencia verificada (mismo payment_id no duplica).
- iCal: export válido + import con de-duplicación; gauge `ical_last_sync_age_minutes` actualizándose.

Comandos/Consultas sugeridos
```bash
# 1. Firmas WhatsApp/MP (simulación, payload fijo)
python - <<'PY'
# Generar HMAC SHA-256 simulado para WhatsApp y ejemplo MP
PY

# 2. Rate limiting (headers/responses)
rg -n "Rate limit|429|too many" backend/app

# 3. iCal export (si deploy)
curl -I https://<host>/api/v1/ical/export?token=<export_token>
```

Riesgos/Focos
- Desalineo de headers reales (capitalización, prefijos) vs implementación.
- Idempotencia parcial (falta de locking) en casos límite concurrencia.
- Audio pipeline: errores de ffmpeg en formatos OGG/Opus.

---

## Entregables finales (por módulo)
- M1: INVENTARIO_CODIGO.csv, CONTRATOS_CORE.md, DB_CONSTRAINTS.md, CONFIG_MATRIX.md, MIGRATIONS_MAP.md
- M2: RUNTIME_REPORT.md, ROUTES_LIST.json, JOBS_STATUS.md, METRICS_SNAPSHOT.txt, HEALTH_HISTORY.csv
- M3: WEBHOOK_SECURITY_CHECKLIST.md, IDEMPOTENCY_CASES.md, INTEGRATIONS_MATRIX.md

---

## Secuencia recomendada y tiempos
1) M1 (estático): 45–60 min
2) M2 (dinámico): 45–60 min (si hay staging/Fly)
3) M3 (interfaces): 45–75 min
Total: ~2.5–3.5 h (sin bloqueos externos)

---

## Criterios de cierre del ejercicio
- Todos los artefactos generados y versionados en `docs/reverse/` o `docs/planning/`.
- Lista de hallazgos con severidad (Critical/High/Medium/Low) y quick wins.
- Riesgos residuales documentados y próximos pasos acordados.

---

## Próximos pasos (acción)
- Aprobación del plan (este documento).
- Crear carpetas `docs/reverse/` y plantillas vacías para artefactos.
- Ejecutar Módulo 1 hoy; Módulos 2–3 mañana junto al despliegue.
