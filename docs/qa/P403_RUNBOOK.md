# P403: RUNBOOK - Sistema MVP Alojamientos

**Fecha:** 14 Octubre 2025
**Prompt QA:** P403 - Incident Response & Troubleshooting
**Fase:** FASE 5 - Operaciones
**Tiempo Estimado:** 2 horas

---

## 🎯 OBJETIVO

Documentar procedimientos operacionales para incident response, troubleshooting común y escalation paths.

---

## 🚨 1. INCIDENT RESPONSE

### 1.1 Clasificación de Incidentes

| Severidad | Impacto | Ejemplos | Response Time | Escalation |
|-----------|---------|----------|---------------|------------|
| **SEV1** | Sistema caído, data loss | Backend down, DB corrupta | < 5 min | CTO inmediato |
| **SEV2** | Funcionalidad crítica rota | Pagos no procesan, webhooks caídos | < 15 min | Tech Lead |
| **SEV3** | Degradación parcial | iCal sync lento, logs creciendo | < 1 hora | DevOps |
| **SEV4** | Issue menor | UI bug, typo en email | < 24 horas | Dev Team |

### 1.2 Procedimiento General

```
1. DETECTAR
   └─> Alerta Prometheus/Grafana
   └─> Usuario reporta issue
   └─> Health check unhealthy

2. NOTIFICAR
   └─> Crear incident en sistema (GitHub Issue con label incident)
   └─> Notificar en canal #incidents (Slack/Discord)
   └─> Escalar según severidad

3. DIAGNOSTICAR
   └─> Verificar health: curl /api/v1/healthz
   └─> Revisar logs: docker logs backend --tail 100
   └─> Verificar métricas: open http://grafana:3000

4. MITIGAR
   └─> Rollback si deploy reciente (< 1 hora)
   └─> Restart servicios si necesario
   └─> Fix forward si simple

5. RESOLVER
   └─> Aplicar fix definitivo
   └─> Validar con smoke tests
   └─> Monitorear 15 min post-fix

6. DOCUMENTAR
   └─> Post-mortem en docs/incidents/YYYY-MM-DD-incident.md
   └─> Agregar a troubleshooting si recurrente
```

---

## 🔍 2. TROUBLESHOOTING COMÚN

### 2.1 Sistema No Responde (SEV1)

**Síntomas:**
- `curl https://api.reservas.com/api/v1/healthz` → Timeout
- Grafana: `up{job="backend"} = 0`
- Logs: Container restarting loop

**Diagnóstico Rápido:**
```bash
# 1. Estado containers
docker ps -a | grep backend
# Buscar: Exit code, Restart count

# 2. Logs recientes
docker logs backend --since 5m | tail -50
# Buscar: Exception, Traceback, "Error"

# 3. Health check manual
docker exec backend curl -f http://localhost:8000/api/v1/healthz
# Si falla: DB o Redis issue
```

**Solución:**

**Causa A: Database Connection Failed**
```bash
# Verificar DB
docker exec postgres pg_isready -U alojamientos
# Si FAIL:
docker restart postgres
docker logs postgres --tail 50
```

**Causa B: OOMKilled (Out of Memory)**
```bash
docker inspect backend | grep OOMKilled
# Si true:
# Aumentar límite en docker-compose.yml:
#   deploy:
#     resources:
#       limits:
#         memory: 1G  # Era 512M
docker-compose up -d backend
```

**Causa C: Code Error en Startup**
```bash
# Revisar si hay syntax error
docker logs backend | grep "SyntaxError\|ImportError"
# Solución: Rollback
git checkout v1.2.2  # Último tag estable
docker-compose up -d --build
```

### 2.2 Error Rate Alto (SEV2)

**Síntomas:**
- Grafana: Error rate > 5%
- Logs: Múltiples `500 Internal Server Error`
- Alerta: `HighErrorRate` firing

**Diagnóstico:**
```bash
# 1. Identificar endpoint con errores
docker logs backend | grep "500" | awk '{print $7}' | sort | uniq -c
# Output: 45 /api/v1/webhooks/whatsapp

# 2. Ver detalles de error
docker logs backend | grep "500" | tail -10
# Buscar: Exception type, trace

# 3. Verificar dependencias
curl http://localhost:8000/api/v1/healthz
# Si "degraded": Identificar componente unhealthy
```

**Soluciones Comunes:**

**Causa A: Redis Down**
```bash
docker restart redis
# Esperar 30s
curl http://localhost:8000/api/v1/healthz
```

**Causa B: DB Locks/Deadlocks**
```bash
docker exec postgres psql -U alojamientos -d alojamientos_db -c "
SELECT pid, state, query
FROM pg_stat_activity
WHERE state = 'active' AND wait_event_type = 'Lock';
"
# Si hay queries bloqueadas > 5min:
# Matar query: SELECT pg_terminate_backend(PID);
```

**Causa C: Bug en Código Reciente**
```bash
# Rollback al último tag
./backend/deploy.sh rollback
```

### 2.3 Latencia Alta (SEV2)

**Síntomas:**
- Grafana: P95 latency > 6s
- Usuarios: "Sistema lento"
- Alerta: `HighLatencyP95` firing

**Diagnóstico:**
```bash
# 1. Identificar endpoint lento
docker exec backend python3 -c "
from prometheus_client.parser import text_string_to_metric_families
import requests
metrics = requests.get('http://localhost:8000/metrics').text
for family in text_string_to_metric_families(metrics):
    if 'duration' in family.name:
        for sample in family.samples:
            if sample[2] > 5:  # >5s
                print(f'{sample[0]}: {sample[2]}s')
"

# 2. Verificar DB queries lentas
docker exec postgres psql -U alojamientos -d alojamientos_db -c "
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '2 seconds'
ORDER BY duration DESC;
"

# 3. Verificar Redis latency
docker exec redis redis-cli --latency-history
```

**Soluciones:**

**Causa A: Missing Index**
```sql
-- Ver sequential scans
SELECT schemaname, tablename, seq_scan, seq_tup_read, idx_scan
FROM pg_stat_user_tables
WHERE seq_scan > 100 AND seq_tup_read > 10000;

-- Si reservations tiene muchos seq_scan:
-- Crear índices (ver P303_DATABASE_OPTIMIZATION.md)
```

**Causa B: Cache Miss Rate Alto**
```bash
# Verificar hits Redis
docker exec redis redis-cli INFO stats | grep keyspace
# Si evicted_keys > 1000/min: Aumentar memoria Redis
```

**Causa C: Load Spike**
```bash
# Verificar request rate
docker exec backend curl http://localhost:8000/metrics | grep http_requests_total
# Si RPS > 100: Escalar horizontalmente (fuera scope MVP)
```

### 2.4 Pre-reserva No Se Crea (SEV2)

**Síntomas:**
- Usuario reporta: "No llega confirmación"
- Logs: `reservations_lock_failed_total` incrementa
- WhatsApp: Mensaje "Sistema temporalmente no disponible"

**Diagnóstico:**
```bash
# 1. Verificar locks Redis
docker exec redis redis-cli KEYS "lock:acc:*"
# Si muchos locks (>50): Posible leak

# 2. Ver TTL de locks
docker exec redis redis-cli TTL "lock:acc:5:2025-10-20:2025-10-22"
# Si TTL > 1800s: Lock huérfano

# 3. Verificar constraint violations
docker logs backend | grep "IntegrityError"
# Si hay overlap: Constraint funcionando correctamente
```

**Soluciones:**

**Causa A: Locks Huérfanos**
```bash
# Limpiar locks expirados manualmente
docker exec redis redis-cli --scan --pattern "lock:acc:*" | while read key; do
  TTL=$(docker exec redis redis-cli TTL "$key")
  if [ "$TTL" -gt 2000 ]; then
    echo "Deleting stale lock: $key"
    docker exec redis redis-cli DEL "$key"
  fi
done
```

**Causa B: Date Overlap Real**
```bash
# Ver reservas activas para alojamiento
docker exec postgres psql -U alojamientos -d alojamientos_db -c "
SELECT id, check_in, check_out, reservation_status
FROM reservations
WHERE accommodation_id = 5
AND reservation_status IN ('pre_reserved', 'confirmed')
ORDER BY check_in;
"
# Si overlap: Investigar cómo se saltó constraint
```

**Causa C: Redis Performance Degradado**
```bash
docker exec redis redis-cli --latency
# Si latency > 100ms:
docker restart redis
```

### 2.5 Webhooks No Procesan (SEV2)

**Síntomas:**
- WhatsApp: Mensajes no llegan al sistema
- Mercado Pago: Pagos no confirman reservas
- Logs: `webhook_signature_invalid_total` alto

**Diagnóstico:**
```bash
# 1. Verificar webhook signatures
docker logs backend | grep "invalid_signature"

# 2. Verificar variables de entorno
docker exec backend env | grep -E "WHATSAPP_APP_SECRET|MERCADOPAGO_WEBHOOK_SECRET"

# 3. Test webhook manual
curl -X POST http://localhost:8000/api/v1/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{"object":"whatsapp_business_account"}'
# Expect: 403 (signature invalid) = Validación funcionando
```

**Soluciones:**

**Causa A: Secret Incorrecto**
```bash
# Verificar secret en Meta/MP dashboard
# Actualizar .env:
WHATSAPP_APP_SECRET=nuevo_secret_desde_meta
docker-compose restart backend
```

**Causa B: Webhook URL No Configurada**
```bash
# Verificar en Meta Business Suite:
# Settings → WhatsApp → Webhooks
# Callback URL debe ser: https://api.reservas.com/api/v1/webhooks/whatsapp
# Verify Token: debe coincidir con WHATSAPP_VERIFY_TOKEN
```

**Causa C: Rate Limit Excedido**
```bash
docker logs backend | grep "rate_limit"
# Si muchos: Revisar config rate limiting
# Temporal: Bypass para webhook de prueba
```

### 2.6 iCal Sync Stale (SEV3)

**Síntomas:**
- Alerta: `ICalSyncStale` (>40 min)
- Grafana: `ical_last_sync_age_minutes` alto
- Reservas Airbnb no aparecen en sistema

**Diagnóstico:**
```bash
# 1. Ver último sync
docker logs backend | grep "ical_sync" | tail -10

# 2. Verificar worker background
docker exec backend ps aux | grep "ical"

# 3. Test sync manual
docker exec backend python3 -c "
import asyncio
from app.services.ical import sync_all_ical_feeds
asyncio.run(sync_all_ical_feeds())
"
```

**Soluciones:**

**Causa A: Worker No Corriendo**
```bash
# Restart backend para reiniciar workers
docker restart backend
```

**Causa B: Feed URL Inválida**
```bash
# Verificar URLs en DB
docker exec postgres psql -U alojamientos -d alojamientos_db -c "
SELECT id, name, ical_feed_url
FROM accommodations
WHERE ical_feed_url IS NOT NULL;
"
# Test URL manualmente:
curl -I "https://www.airbnb.com/calendar/ical/12345.ics"
# Si 404: Actualizar URL en DB
```

**Causa C: Credential Expired (si auth)**
```bash
# Re-generar iCal export token
docker exec backend python3 -c "
from app.services.ical import regenerate_ical_token
regenerate_ical_token(accommodation_id=5)
"
```

---

## 📞 3. ESCALATION PATHS

### 3.1 Contactos

```
SEV1 (Sistema Caído)
├─> On-Call Engineer (responde en 5 min)
│   └─> Si no resuelve en 15 min → CTO
└─> Notificar: #incidents-critical channel

SEV2 (Funcionalidad Crítica)
├─> Tech Lead (responde en 15 min)
│   └─> Si no resuelve en 1 hora → CTO
└─> Notificar: #incidents channel

SEV3 (Degradación)
├─> DevOps Engineer (responde en 1 hora)
└─> Notificar: #monitoring channel

SEV4 (Menor)
├─> Developer asignado (responde en 24 horas)
└─> GitHub Issue
```

### 3.2 Comunicación

**Durante Incidente:**
- ✅ Crear incident thread en Slack/Discord
- ✅ Updates cada 15 min (SEV1), 30 min (SEV2)
- ✅ Notificar a stakeholders si downtime > 30 min
- ✅ Status page update (si existe)

**Post-Incidente:**
- ✅ Post-mortem en 48 horas
- ✅ Identificar root cause
- ✅ Action items para prevenir recurrencia

---

## 🛠️ 4. COMANDOS ÚTILES

### 4.1 Logs y Debugging

```bash
# Logs en tiempo real
docker logs -f backend

# Últimos 100 logs con timestamp
docker logs backend --tail 100 --timestamps

# Filtrar por error
docker logs backend | grep -i "error\|exception\|traceback"

# Logs de todos los servicios
docker-compose logs -f

# Logs específicos de período
docker logs backend --since 2025-10-14T14:00:00 --until 2025-10-14T15:00:00
```

### 4.2 Estado del Sistema

```bash
# Containers corriendo
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Health checks
docker inspect backend | grep -A 10 Health

# Recursos usados
docker stats --no-stream

# Espacio en disco
df -h
docker system df
```

### 4.3 Database

```bash
# Conexión psql
docker exec -it postgres psql -U alojamientos -d alojamientos_db

# Queries activas
SELECT pid, state, query FROM pg_stat_activity WHERE state = 'active';

# Tamaño DB
SELECT pg_size_pretty(pg_database_size('alojamientos_db'));

# Locks actuales
SELECT * FROM pg_locks WHERE NOT granted;

# Backup rápido
docker exec postgres pg_dump -U alojamientos alojamientos_db > backup.sql
```

### 4.4 Redis

```bash
# Conexión redis-cli
docker exec -it redis redis-cli -a $REDIS_PASSWORD

# Info
INFO
INFO memory
INFO stats

# Keys actuales
KEYS *
DBSIZE

# Flush (⚠️ PELIGROSO)
FLUSHALL
```

---

## 📊 5. HEALTH CHECK INTERPRETATION

### 5.1 Response Analysis

```json
// HEALTHY
{
  "status": "healthy",
  "checks": {
    "database": {"status": "ok", "latency_ms": 45},
    "redis": {"status": "ok", "latency_ms": 12},
    "ical_sync": {"status": "ok", "age_minutes": 8}
  }
}
→ Acción: NINGUNA

// DEGRADED
{
  "status": "degraded",
  "checks": {
    "database": {"status": "slow", "latency_ms": 650},
    "redis": {"status": "ok"},
    "ical_sync": {"status": "ok"}
  }
}
→ Acción: Investigar DB performance, ver queries lentas

// UNHEALTHY
{
  "status": "unhealthy",
  "checks": {
    "database": {"status": "error", "error": "connection refused"},
    "redis": {"status": "ok"}
  }
}
→ Acción: SEV1 - Restart DB inmediatamente
```

---

## 📋 6. MAINTENANCE PROCEDURES

### 6.1 Backup Rutinario

```bash
# Script: /opt/backups/daily_backup.sh
#!/bin/bash
BACKUP_DIR="/opt/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Database
docker exec postgres pg_dump -U alojamientos alojamientos_db | gzip > $BACKUP_DIR/db.sql.gz

# .env file
cp backend/.env $BACKUP_DIR/.env.backup

# Retention: 30 días
find /opt/backups -type d -mtime +30 -exec rm -rf {} \;
```

**Cron:**
```cron
0 2 * * * /opt/backups/daily_backup.sh
```

### 6.2 Update Procedure (Rutinario)

```bash
# 1. Pre-checks
./scripts/pre-deploy-check.sh

# 2. Backup
./backend/deploy.sh backup

# 3. Pull cambios
git fetch origin
git checkout v1.3.0  # Nuevo tag

# 4. Deploy
docker-compose down
docker-compose up -d --build

# 5. Migrations
docker-compose exec backend alembic upgrade head

# 6. Smoke test
./scripts/smoke-test-prod.sh
```

### 6.3 Certificate Renewal (Let's Encrypt)

```bash
# Renovar certificados (automático vía certbot)
docker exec certbot certbot renew

# Si falla, manual:
certbot certonly --webroot -w /var/www/html -d api.reservas.com

# Reload nginx
docker exec nginx nginx -s reload
```

---

## ✅ VALIDACIÓN P403

### Checklist

- [x] Incident classification documentada (SEV1-4)
- [x] Troubleshooting para 6 escenarios comunes
- [x] Escalation paths definidos
- [x] Comandos útiles por categoría (logs, DB, Redis)
- [x] Health check interpretation guide
- [x] Maintenance procedures (backup, update, certs)
- [x] Contact list y communication protocol

### Simulacro de Incidente (Test)

```bash
# 1. Simular SEV1 (backend down)
docker stop backend

# 2. Detectar (debe alertar en < 1 min)
# Verificar: Email recibido, Grafana alert firing

# 3. Seguir runbook SEV1
# Ejecutar comandos de diagnóstico
# Aplicar solución (restart)

# 4. Verificar resolución
curl http://localhost/api/v1/healthz
# Expect: {"status": "healthy"}

# 5. Documentar
# Crear post-mortem en docs/incidents/
```

---

## 📚 REFERENCIAS

**Documentos Relacionados:**
- `P401_DEPLOYMENT_PROCEDURES.md` - Para rollback procedures
- `P402_MONITORING_SETUP.md` - Para interpretar alertas
- `docs/TROUBLESHOOTING.md` - Troubleshooting extendido
- `docs/deployment/ROLLBACK_PLAN.md` - Rollback detallado

**Herramientas:**
- Grafana Dashboards: http://localhost:3000
- Prometheus Alerts: http://localhost:9090/alerts
- Logs: `docker logs backend`

---

**Estado:** ✅ COMPLETO
**FASE 5 Finalizada:** 3/3 prompts ejecutados

---

*Documento generado: 14 Octubre 2025*
*Tiempo estimado: 2 horas*
