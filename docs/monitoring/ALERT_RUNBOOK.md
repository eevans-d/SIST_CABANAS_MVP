# 🚨 Alert Runbook - Sistema de Alojamientos

## 📋 Tabla de Contenidos

- [Visión General](#visión-general)
- [Severidades](#severidades)
- [Alertas de API](#alertas-de-api)
- [Alertas de Base de Datos](#alertas-de-base-de-datos)
- [Alertas de Redis](#alertas-de-redis)
- [Alertas de Infraestructura](#alertas-de-infraestructura)
- [Escalamiento](#escalamiento)
- [Postmortem](#postmortem)

---

## 🎯 Visión General

Este runbook proporciona **procedimientos paso a paso** para responder a alertas del Sistema de Alojamientos MVP.

### Principios de Respuesta

1. **PRIORIDAD**: CRITICAL > WARNING > INFO
2. **TIEMPO DE RESPUESTA**:
   - CRITICAL: Inmediato (< 5 min)
   - WARNING: < 30 min
   - INFO: < 2 horas
3. **COMUNICACIÓN**: Actualizar estado en Slack durante investigación
4. **DOCUMENTACIÓN**: Registrar acciones en postmortem si downtime > 5 min

---

## 🔴 Severidades

### CRITICAL (Rojo)

**Impacto**: Servicio caído o degradación severa que afecta a usuarios

**Acción**: Respuesta inmediata, notificación a oncall vía Slack + Email

**Canales**:
- Slack: `#critical-alerts`
- Email: `oncall@example.com`
- PagerDuty: (opcional)

---

### WARNING (Amarillo)

**Impacto**: Potencial problema que puede escalar a CRITICAL

**Acción**: Investigación prioritaria, monitoreo activo

**Canales**:
- Slack: `#alojamientos-alerts`

---

### INFO (Azul)

**Impacto**: Condición anómala pero no crítica

**Acción**: Revisión durante horario laboral

**Canales**:
- Slack: `#info-notifications`

---

## 🌐 Alertas de API

### <a name="runbook-apidown"></a>🔴 APIDown

**Alerta**: API no responde durante 1 minuto

**Severidad**: CRITICAL

**Impacto**: Usuarios no pueden usar el sistema (WhatsApp, email, reservas)

#### Diagnóstico

```bash
# 1. Verificar estado del contenedor
docker ps | grep api

# 2. Ver logs recientes
docker logs --tail 100 sist-cabanas-api

# 3. Verificar conectividad
curl -I http://localhost:8000/api/v1/healthz

# 4. Verificar recursos
docker stats sist-cabanas-api --no-stream
```

#### Posibles Causas

| Causa                     | Síntoma en Logs                          | Solución                     |
|---------------------------|------------------------------------------|------------------------------|
| **OOM Kill**              | `Killed` sin stack trace                 | Ver [Fix OOM](#fix-oom)      |
| **Crash de aplicación**   | Python exception, traceback              | Ver [Fix Crash](#fix-crash)  |
| **DB connection timeout** | `psycopg2.OperationalError`              | Ver [Fix DB](#fix-db)        |
| **Contenedor parado**     | Container `Exited` o `Restarting`        | Ver [Fix Container](#fix-container) |

#### <a name="fix-oom"></a>Solución: OOM Kill

```bash
# 1. Confirmar OOM en dmesg
sudo dmesg | grep -i "out of memory"

# 2. Reiniciar API con más memoria
docker-compose stop api
# Editar docker-compose.yml: deploy.resources.limits.memory: '2g'
docker-compose up -d api

# 3. Monitorear memoria
watch -n 2 'docker stats sist-cabanas-api --no-stream'
```

#### <a name="fix-crash"></a>Solución: Crash de Aplicación

```bash
# 1. Identificar exception en logs
docker logs sist-cabanas-api 2>&1 | grep -A 20 "Traceback"

# 2. Si es error conocido, aplicar hotfix
docker exec -it sist-cabanas-api bash
# Editar código o reiniciar

# 3. Si es nuevo, rollback a última versión estable
git log --oneline | head -5  # Identificar último commit estable
git checkout <commit-hash>
docker-compose build api
docker-compose up -d api

# 4. Abrir issue para fix permanente
```

#### <a name="fix-db"></a>Solución: DB Connection Timeout

```bash
# 1. Verificar PostgreSQL está up
docker ps | grep postgres
docker exec -it sist-cabanas-postgres pg_isready

# 2. Verificar max connections
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "SHOW max_connections; SELECT count(*) FROM pg_stat_activity;"

# 3. Si DB está lleno, matar conexiones idle
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '5 minutes';"

# 4. Reiniciar API
docker-compose restart api
```

#### <a name="fix-container"></a>Solución: Contenedor Parado

```bash
# 1. Ver razón de exit
docker inspect sist-cabanas-api | jq '.[0].State'

# 2. Reiniciar
docker-compose restart api

# 3. Si sigue fallando, recrear
docker-compose up -d --force-recreate api
```

#### Validación

```bash
# 1. API responde
curl http://localhost:8000/api/v1/healthz
# Esperado: {"status": "healthy", "db": "ok", "redis": "ok"}

# 2. Prometheus target "up"
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="alojamientos-api") | .health'
# Esperado: "up"

# 3. Alerta resolved en Alertmanager
curl http://localhost:9093/api/v1/alerts | jq '.data[] | select(.labels.alertname=="APIDown") | .status.state'
# Esperado: "resolved" o no presente
```

#### Escalamiento

Si no se resuelve en **10 minutos**: Contactar a arquitecto de sistemas

---

### 🟡 HighErrorRate

**Alerta**: Tasa de errores 5xx > 5% durante 5 minutos

**Severidad**: WARNING

**Impacto**: Algunos usuarios experimentan errores

#### Diagnóstico

```bash
# 1. Identificar endpoints con errores
docker logs sist-cabanas-api --since 10m | grep "500 Internal Server Error"

# 2. Ver errores recientes en Prometheus
curl -g 'http://localhost:9090/api/v1/query?query=topk(5,rate(http_requests_total{status=~"5.."}[5m]))' | jq

# 3. Verificar logs estructurados
docker exec -it sist-cabanas-api tail -100 /var/log/app/app.log | jq 'select(.level=="ERROR")'
```

#### Posibles Causas

- **Timeout a servicios externos** (WhatsApp API, Mercado Pago)
- **Query lenta en DB** causando timeouts
- **Bug reciente deployado**

#### Solución

```bash
# 1. Identificar patrón de errores
docker logs sist-cabanas-api --since 10m 2>&1 | grep -E "(Exception|Error)" | sort | uniq -c | sort -rn | head -10

# 2. Si es timeout externo, verificar conectividad
docker exec -it sist-cabanas-api curl -I https://graph.facebook.com/v17.0/me
docker exec -it sist-cabanas-api curl -I https://api.mercadopago.com/v1/payments

# 3. Si es query lenta, identificar en logs PostgreSQL
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# 4. Si es bug reciente, considerar rollback
git log --oneline --since="1 day ago"
# Evaluar con equipo si rollback es necesario
```

#### Validación

```bash
# Verificar error rate < 1%
curl -g 'http://localhost:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])/rate(http_requests_total[5m])*100' | jq '.data.result[0].value[1]'
# Esperado: < 1.0
```

---

### 🟡 SlowResponseTime

**Alerta**: P95 de latencia > 5 segundos durante 10 minutos

**Severidad**: WARNING

**Impacto**: Experiencia de usuario degradada

#### Diagnóstico

```bash
# 1. Ver endpoints más lentos
curl -g 'http://localhost:9090/api/v1/query?query=topk(5,histogram_quantile(0.95,rate(http_request_duration_seconds_bucket[5m])))' | jq

# 2. Verificar slow queries en PostgreSQL
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements WHERE mean_exec_time > 1000 ORDER BY mean_exec_time DESC LIMIT 10;"

# 3. Verificar cache hit ratio de Redis
docker exec -it sist-cabanas-redis redis-cli INFO stats | grep keyspace_hits
```

#### Solución

```bash
# 1. Si es query lenta, crear índice (temporal)
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "CREATE INDEX CONCURRENTLY idx_temp ON table_name(column);"

# 2. Si Redis tiene baja hit ratio, warm up cache
docker exec -it sist-cabanas-api python -c "
from app.core.cache import warm_up_cache
warm_up_cache()
"

# 3. Verificar si hay N+1 queries
# Revisar logs de SQLAlchemy con echo=True temporalmente
```

#### Validación

```bash
# P95 < 3 segundos
curl -g 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(http_request_duration_seconds_bucket[5m]))' | jq '.data.result[0].value[1]'
# Esperado: < 3.0
```

---

### 🔵 ICalSyncStale

**Alerta**: Sincronización iCal > 30 minutos sin actualizar

**Severidad**: INFO

**Impacto**: Calendario puede no reflejar últimas reservas de Airbnb/Booking

#### Diagnóstico

```bash
# 1. Verificar último sync
curl http://localhost:8000/metrics | grep ical_last_sync_timestamp

# 2. Ver logs del job de sync
docker logs sist-cabanas-api 2>&1 | grep -i "ical sync"

# 3. Verificar worker background está corriendo
docker exec -it sist-cabanas-api ps aux | grep scheduler
```

#### Solución

```bash
# 1. Trigger manual sync
curl -X POST http://localhost:8000/api/v1/admin/ical/sync/trigger

# 2. Si worker murió, reiniciar API
docker-compose restart api

# 3. Verificar URLs iCal configuradas
docker exec -it sist-cabanas-api python -c "
from app.core.config import settings
print(settings.ICAL_IMPORT_URLS)
"
```

#### Validación

```bash
# Sync age < 20 minutos
LAST_SYNC=$(curl -s http://localhost:8000/metrics | grep ical_last_sync_timestamp | awk '{print $2}')
AGE_MINUTES=$(echo "($(date +%s) - $LAST_SYNC) / 60" | bc)
echo "Age: $AGE_MINUTES minutes"
# Esperado: < 20
```

---

## 💾 Alertas de Base de Datos

### <a name="runbook-databasedown"></a>🔴 DatabaseDown

**Alerta**: PostgreSQL no responde durante 1 minuto

**Severidad**: CRITICAL

**Impacto**: Sistema completamente inoperativo

#### Diagnóstico

```bash
# 1. Verificar contenedor
docker ps | grep postgres

# 2. Verificar proceso PostgreSQL
docker exec -it sist-cabanas-postgres pg_isready

# 3. Ver logs
docker logs --tail 100 sist-cabanas-postgres

# 4. Verificar espacio en disco
df -h
docker exec -it sist-cabanas-postgres df -h /var/lib/postgresql/data
```

#### Posibles Causas

| Causa                     | Síntoma                                  | Solución                     |
|---------------------------|------------------------------------------|------------------------------|
| **Contenedor parado**     | `docker ps` no lo muestra                | `docker-compose restart postgres` |
| **Disco lleno**           | `No space left on device` en logs        | Ver [Fix Disk](#fix-disk)    |
| **Corruption de datos**   | `PANIC: could not locate a valid checkpoint` | Ver [Fix Corruption](#fix-corruption) |
| **Max connections**       | `too many connections` en logs API       | Ver [Fix Connections](#fix-connections) |

#### <a name="fix-disk"></a>Solución: Disco Lleno

```bash
# 1. Limpiar logs viejos
docker exec -it sist-cabanas-postgres find /var/log/postgresql -name "*.log" -mtime +7 -delete

# 2. Limpiar WAL files viejos (si están retenidos)
docker exec -it sist-cabanas-postgres su - postgres -c "pg_archivecleanup /var/lib/postgresql/data/pg_wal"

# 3. Vacuum full (requiere downtime)
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "VACUUM FULL VERBOSE;"

# 4. Expandir volumen si es persistente issue
# Consultar con DevOps
```

#### <a name="fix-corruption"></a>Solución: Corruption de Datos

```bash
# 1. STOP API para evitar más escrituras
docker-compose stop api

# 2. Intentar recovery
docker exec -it sist-cabanas-postgres su - postgres -c "pg_resetwal -f /var/lib/postgresql/data"

# 3. Si falla, restore desde backup
# Ver BACKUP_STRATEGY.md

# 4. START API
docker-compose start api
```

#### <a name="fix-connections"></a>Solución: Max Connections

```bash
# 1. Ver conexiones activas
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# 2. Matar conexiones idle
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '10 minutes';"

# 3. Aumentar max_connections (temporal)
docker exec -it sist-cabanas-postgres psql -U postgres \
  -c "ALTER SYSTEM SET max_connections = 200; SELECT pg_reload_conf();"

# 4. Configurar connection pooling en API (permanente)
# Editar app/core/config.py: SQLALCHEMY_POOL_SIZE = 10
```

#### Validación

```bash
# 1. DB responde
docker exec -it sist-cabanas-postgres pg_isready
# Esperado: "accepting connections"

# 2. API puede conectar
curl http://localhost:8000/api/v1/healthz | jq '.db'
# Esperado: "ok"

# 3. Prometheus target "up"
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="postgres") | .health'
# Esperado: "up"
```

---

### 🟡 HighDatabaseConnections

**Alerta**: Conexiones activas > 80% de max_connections durante 5 minutos

**Severidad**: WARNING

**Impacto**: Próximo a alcanzar límite, nuevas conexiones fallarán

#### Diagnóstico

```bash
# Ver detalle de conexiones
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos -c "
SELECT
  datname,
  state,
  count(*) as connections,
  max(now() - query_start) as max_duration
FROM pg_stat_activity
WHERE datname IS NOT NULL
GROUP BY datname, state
ORDER BY connections DESC;
"
```

#### Solución

```bash
# 1. Identificar queries long-running
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos -c "
SELECT pid, usename, query_start, state, query
FROM pg_stat_activity
WHERE state != 'idle' AND query_start < now() - interval '5 minutes'
ORDER BY query_start;
"

# 2. Matar queries problemáticas (evaluar impacto primero)
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "SELECT pg_terminate_backend(<pid>);"

# 3. Implementar connection pooling si no existe
# En app/core/database.py:
# engine = create_async_engine(
#     DATABASE_URL,
#     pool_size=10,
#     max_overflow=20,
#     pool_pre_ping=True,
#     pool_recycle=3600
# )
```

#### Validación

```bash
# Conexiones < 60%
ACTIVE=$(docker exec sist-cabanas-postgres psql -U alojamientos_user -d alojamientos -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='alojamientos';")
MAX=$(docker exec sist-cabanas-postgres psql -U postgres -t -c "SHOW max_connections;")
PERCENTAGE=$(echo "scale=2; $ACTIVE / $MAX * 100" | bc)
echo "Usage: $PERCENTAGE%"
# Esperado: < 60
```

---

## 🔴 Alertas de Redis

### <a name="runbook-redisdown"></a>🔴 RedisDown

**Alerta**: Redis no responde durante 1 minuto

**Severidad**: CRITICAL

**Impacto**: Locks no funcionan (riesgo de doble-booking), cache no disponible

#### Diagnóstico

```bash
# 1. Verificar contenedor
docker ps | grep redis

# 2. Test conexión
docker exec -it sist-cabanas-redis redis-cli PING
# Esperado: PONG

# 3. Ver logs
docker logs --tail 100 sist-cabanas-redis
```

#### Solución

```bash
# 1. Reiniciar Redis
docker-compose restart redis

# 2. Si no inicia, verificar permisos de volumen
sudo chown -R 999:999 /var/lib/docker/volumes/sist_cabanas_redis_data

# 3. Si corruption, recrear (se pierde cache, pero no crítico)
docker-compose stop redis
docker volume rm sist_cabanas_redis_data
docker-compose up -d redis

# 4. Verificar API reconecta automáticamente
docker logs sist-cabanas-api | grep -i redis
```

#### Validación

```bash
# Redis responde
docker exec -it sist-cabanas-redis redis-cli PING
# Esperado: PONG

# API puede usar Redis
curl http://localhost:8000/api/v1/healthz | jq '.redis'
# Esperado: "ok"
```

---

### 🟡 RedisHighMemory

**Alerta**: Uso de memoria > 90% durante 5 minutos

**Severidad**: WARNING

**Impacto**: Redis puede empezar a evict keys (pérdida de locks, cache)

#### Diagnóstico

```bash
# Ver stats de memoria
docker exec -it sist-cabanas-redis redis-cli INFO memory

# Ver keys por tipo
docker exec -it sist-cabanas-redis redis-cli --scan --pattern '*' | wc -l

# Ver tamaño de keys más grandes
docker exec -it sist-cabanas-redis redis-cli --bigkeys
```

#### Solución

```bash
# 1. Limpiar keys expiradas manualmente
docker exec -it sist-cabanas-redis redis-cli SAVE

# 2. Identificar locks stale (TTL expirado pero no limpiado)
docker exec -it sist-cabanas-redis redis-cli --scan --pattern 'lock:*' | while read key; do
  TTL=$(docker exec -it sist-cabanas-redis redis-cli TTL "$key")
  if [ "$TTL" -eq "-1" ]; then
    echo "Stale lock: $key"
    # docker exec -it sist-cabanas-redis redis-cli DEL "$key"  # Descomentar para limpiar
  fi
done

# 3. Aumentar maxmemory (temporal)
docker exec -it sist-cabanas-redis redis-cli CONFIG SET maxmemory 2gb

# 4. Configurar eviction policy si no existe
docker exec -it sist-cabanas-redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### Validación

```bash
# Memoria < 80%
USED=$(docker exec sist-cabanas-redis redis-cli INFO memory | grep used_memory: | cut -d: -f2 | tr -d '\r')
MAX=$(docker exec sist-cabanas-redis redis-cli INFO memory | grep maxmemory: | cut -d: -f2 | tr -d '\r')
PERCENTAGE=$(echo "scale=2; $USED / $MAX * 100" | bc)
echo "Memory usage: $PERCENTAGE%"
# Esperado: < 80
```

---

## 🖥️ Alertas de Infraestructura

### <a name="runbook-cpu"></a>🔴 CriticalCPUUsage

**Alerta**: CPU > 95% durante 5 minutos

**Severidad**: CRITICAL

**Impacto**: Sistema lento, timeouts, posible crash

#### Diagnóstico

```bash
# 1. Ver procesos con más CPU
docker stats --no-stream | sort -k3 -rh | head -5

# 2. Identificar contenedor problemático
docker exec -it <container> top -b -n 1 | head -20

# 3. Ver carga del sistema
uptime
cat /proc/loadavg
```

#### Solución

```bash
# 1. Si es API, escalar horizontalmente (si hay load balancer)
docker-compose up -d --scale api=3

# 2. Si es query intensiva, matar proceso específico
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='active' AND query ~ 'SELECT.*JOIN.*JOIN' LIMIT 1;"

# 3. Si es job background, pausar temporalmente
docker exec -it sist-cabanas-api supervisorctl stop ical_sync_worker

# 4. Reiniciar servicio problemático
docker-compose restart <service>
```

#### Validación

```bash
# CPU < 70%
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}" | grep -v CONTAINER | awk '{print $2}' | tr -d '%' | awk '{sum+=$1; count++} END {print sum/count}'
# Esperado: < 70
```

---

### <a name="runbook-memory"></a>🔴 CriticalMemoryUsage

**Alerta**: Memoria > 95% durante 5 minutos

**Severidad**: CRITICAL

**Impacto**: OOM killer puede matar procesos críticos

#### Diagnóstico

```bash
# Ver memoria por contenedor
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Ver procesos del host
free -h
ps aux --sort=-rss | head -10
```

#### Solución

```bash
# 1. Limpiar cache del sistema
sudo sync; echo 3 > /proc/sys/vm/drop_caches

# 2. Reiniciar contenedor con más memoria
docker-compose stop <container>
# Editar docker-compose.yml: deploy.resources.limits.memory: 'XGb'
docker-compose up -d <container>

# 3. Si es memory leak en API, reiniciar temporalmente
docker-compose restart api

# 4. Escalar horizontalmente si posible
docker-compose up -d --scale api=2
```

#### Validación

```bash
# Memoria < 80%
free | awk '/Mem/{printf("%.2f\n", $3/$2*100)}'
# Esperado: < 80
```

---

### <a name="runbook-disk"></a>🔴 CriticalDiskSpace

**Alerta**: Disco > 95% durante 5 minutos

**Severidad**: CRITICAL

**Impacto**: DB no puede escribir, sistema se corrompe

#### Diagnóstico

```bash
# Ver uso por filesystem
df -h

# Identificar directorios grandes
du -h / | sort -rh | head -20

# Ver logs grandes
find /var/log -type f -size +100M -exec ls -lh {} \;
```

#### Solución

```bash
# 1. Limpiar logs de Docker
docker system prune -a --volumes -f

# 2. Limpiar logs del sistema
sudo journalctl --vacuum-time=7d
sudo rm -rf /var/log/*.log.*

# 3. Limpiar Prometheus data viejo
docker exec prometheus find /prometheus -name "*.db" -mtime +30 -delete

# 4. Expandir volumen (requiere planificación)
# Contactar DevOps para resize de volumen
```

#### Validación

```bash
# Disco < 80%
df -h / | awk 'NR==2{print $5}' | tr -d '%'
# Esperado: < 80
```

---

## 📞 Escalamiento

### Nivel 1: DevOps Engineer (Tú)

**Responsabilidad**: Todas las alertas WARNING e INFO

**Tiempo de respuesta**: < 30 min (WARNING), < 2h (INFO)

**Herramientas**: Este runbook, Grafana, Prometheus, logs

---

### Nivel 2: Backend Tech Lead

**Escalamiento si**:
- Alerta CRITICAL no resuelta en 15 minutos
- Múltiples alertas CRITICAL simultáneas
- Sospecha de bug en código que requiere hotfix

**Contacto**: Slack `@tech-lead`, tel: +XX-XXXX-XXXX

---

### Nivel 3: System Architect

**Escalamiento si**:
- Downtime > 30 minutos
- Corruption de datos
- Decisión de rollback a versión anterior

**Contacto**: Slack `@architect`, tel: +XX-XXXX-XXXX

---

## 📝 Postmortem

### Cuándo Crear Postmortem

- Downtime > 5 minutos
- Pérdida de datos
- Alerta CRITICAL que requirió escalamiento

### Template

```markdown
# Postmortem: [Título del Incidente]

**Fecha**: YYYY-MM-DD
**Duración**: HH:MM
**Severidad**: CRITICAL/WARNING/INFO
**Impacto**: X usuarios afectados, Y transacciones fallidas

## Timeline

- HH:MM - Alerta disparada
- HH:MM - Investigación iniciada
- HH:MM - Causa raíz identificada
- HH:MM - Mitigación aplicada
- HH:MM - Servicio restaurado

## Causa Raíz

[Descripción técnica detallada]

## Impacto

- Usuarios afectados: X
- Transacciones perdidas: Y
- Downtime total: Z minutos

## Resolución

[Pasos aplicados para resolver]

## Acciones Preventivas

1. [Acción 1] - Responsable: [Nombre] - Deadline: [Fecha]
2. [Acción 2] - Responsable: [Nombre] - Deadline: [Fecha]
3. [Acción 3] - Responsable: [Nombre] - Deadline: [Fecha]

## Lecciones Aprendidas

- [Lección 1]
- [Lección 2]
```

### Dónde Guardar

- Repositorio: `docs/postmortems/YYYY-MM-DD-incident-name.md`
- Notificar equipo en: Slack `#postmortems`

---

## ✅ Checklist de Respuesta a Incidentes

### Durante el Incidente

- [ ] Confirmar alerta en Alertmanager
- [ ] Notificar en Slack canal apropiado
- [ ] Seguir runbook paso a paso
- [ ] Documentar acciones tomadas en thread de Slack
- [ ] Escalar si no se resuelve en tiempo esperado

### Post-Incidente

- [ ] Confirmar alerta resolved en Alertmanager
- [ ] Validar métricas volvieron a normal
- [ ] Notificar resolución en Slack
- [ ] Crear postmortem si aplica
- [ ] Revisar logs para entender causa raíz
- [ ] Proponer mejoras al runbook si faltó info

---

**📌 Referencia Rápida**:

| Alerta              | Severidad | Tiempo Respuesta | Página          |
|---------------------|-----------|------------------|-----------------|
| APIDown             | CRITICAL  | < 5 min          | [Link](#runbook-apidown) |
| DatabaseDown        | CRITICAL  | < 5 min          | [Link](#runbook-databasedown) |
| RedisDown           | CRITICAL  | < 5 min          | [Link](#runbook-redisdown) |
| CriticalCPUUsage    | CRITICAL  | < 10 min         | [Link](#runbook-cpu) |
| CriticalMemoryUsage | CRITICAL  | < 10 min         | [Link](#runbook-memory) |
| CriticalDiskSpace   | CRITICAL  | < 10 min         | [Link](#runbook-disk) |
| HighErrorRate       | WARNING   | < 30 min         | [Link](#higherrorrate) |
| SlowResponseTime    | WARNING   | < 30 min         | [Link](#slowresponsetime) |
| ICalSyncStale       | INFO      | < 2h             | [Link](#icalsyncstale) |
