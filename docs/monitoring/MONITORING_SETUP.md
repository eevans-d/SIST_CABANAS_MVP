# 📊 Guía de Configuración - Monitoring Stack

## 🎯 Tabla de Contenidos

- [Visión General](#visión-general)
- [Arquitectura](#arquitectura)
- [Componentes](#componentes)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Acceso a Servicios](#acceso-a-servicios)
- [Dashboards](#dashboards)
- [Alertas](#alertas)
- [Troubleshooting](#troubleshooting)
- [Mantenimiento](#mantenimiento)

---

## 📋 Visión General

Este sistema de monitoring proporciona **observabilidad completa 24/7** para el Sistema de Alojamientos MVP mediante:

- **Prometheus**: Recolección y almacenamiento de métricas
- **Alertmanager**: Gestión y enrutamiento de alertas
- **Grafana**: Visualización mediante dashboards interactivos
- **Exporters**: Métricas especializadas (PostgreSQL, Redis, Node, Containers)

### Características Principales

✅ **Monitoreo en tiempo real** (refresh 10s en dashboards)
✅ **22 reglas de alerta** con severidades (CRITICAL, WARNING, INFO)
✅ **3 dashboards** pre-configurados (API, Database, Infrastructure)
✅ **Retención 30 días** de métricas históricas
✅ **Integración Slack + Email** para notificaciones
✅ **Health checks** automáticos en todos los servicios

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND NETWORK                            │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌───────┐                   │
│  │ FastAPI  │    │PostgreSQL│    │ Redis │                    │
│  │   API    │    │    DB    │    │ Cache │                    │
│  └────┬─────┘    └────┬─────┘    └───┬───┘                   │
│       │               │              │                         │
└───────┼───────────────┼──────────────┼─────────────────────────┘
        │               │              │
        │    ┌──────────┼──────────────┼──────┐
        │    │          │              │      │
┌───────┼────┼──────────┼──────────────┼──────┼─────────────────┐
│       │    │          │              │      │  MONITORING      │
│       │    │          │              │      │  NETWORK         │
│       ▼    ▼          ▼              ▼      ▼                  │
│    ┌─────────────────────────────────────────────┐            │
│    │         PROMETHEUS (puerto 9090)            │            │
│    │  • Scrape interval: 15s                     │            │
│    │  • Retention: 30 días                       │            │
│    │  • Storage: prometheus_data volume          │            │
│    └────────┬─────────────────────┬──────────────┘            │
│             │                     │                            │
│             ▼                     ▼                            │
│    ┌─────────────────┐   ┌──────────────────┐                │
│    │  ALERTMANAGER   │   │     GRAFANA      │                │
│    │  (puerto 9093)  │   │  (puerto 3000)   │                │
│    │                 │   │                  │                │
│    │  • Routes       │   │  • 3 Dashboards  │                │
│    │  • Inhibitions  │   │  • Auto-refresh  │                │
│    │  • Receivers:   │   │  • Datasource    │                │
│    │    - Slack      │   │    provisioned   │                │
│    │    - Email      │   │                  │                │
│    │    - PagerDuty  │   │                  │                │
│    └─────────────────┘   └──────────────────┘                │
│                                                                │
│    ┌───────────────────────────────────────────────────────┐ │
│    │              EXPORTERS                                 │ │
│    ├───────────────────────────────────────────────────────┤ │
│    │ • postgres-exporter (9187) → PostgreSQL metrics       │ │
│    │ • redis-exporter (9121)    → Redis metrics            │ │
│    │ • node-exporter (9100)     → Host metrics (CPU/RAM)   │ │
│    │ • cadvisor (8080)          → Container metrics        │ │
│    └───────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

### Flujo de Datos

1. **Exporters** recolectan métricas de sus respectivos servicios
2. **Prometheus** scrape métricas cada 15s (API: 10s)
3. **Alert rules** evalúan condiciones y disparan alertas
4. **Alertmanager** enruta alertas según severidad
5. **Grafana** visualiza métricas en tiempo real
6. **Notificaciones** enviadas a Slack/Email cuando hay alertas

---

## 🧩 Componentes

### 1. Prometheus (v2.47.2)

**Propósito**: Base de datos de series temporales para métricas

**Configuración principal** (`prometheus.yml`):
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'alojamientos-api'
    scrape_interval: 10s
    static_configs:
      - targets: ['api:8000']

  - job_name: 'postgres'
    scrape_interval: 30s
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    scrape_interval: 30s
    static_configs:
      - targets: ['redis-exporter:9121']

  # ... más jobs (node, cadvisor, etc.)
```

**Métricas almacenadas**:
- Requests HTTP (rate, duration, status)
- Conexiones DB (activas, pool, queries)
- Redis (memoria, hits, evictions)
- Host (CPU, RAM, disk, network)
- Containers (CPU, memoria, estado)

**Retención**: 30 días (configurable con `--storage.tsdb.retention.time`)

---

### 2. Alertmanager (v0.26.0)

**Propósito**: Gestión centralizada de alertas

**Routes configurados**:

| Severidad | Receiver           | Wait    | Repeat |
|-----------|--------------------|---------|--------|
| CRITICAL  | critical-alerts    | 5s      | 4h     |
| WARNING   | slack-notifications| 30s     | 24h    |
| INFO      | info-notifications | 5m      | 48h    |
| database  | database-team      | 1m      | 12h    |
| devops    | devops-team        | 1m      | 12h    |

**Inhibition rules**:
- Alertas CRITICAL suprimen WARNING/INFO del mismo componente
- APIDown suprime todas las alertas de API
- DatabaseDown suprime alertas de queries/connections

**Receivers configurados**:
```yaml
receivers:
  - name: 'critical-alerts'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#critical-alerts'
    email_configs:
      - to: 'oncall@example.com'
        from: 'alertmanager@example.com'

  - name: 'slack-notifications'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#alojamientos-alerts'
```

---

### 3. Grafana (v10.2.0)

**Propósito**: Visualización de métricas

**Features habilitados**:
- Pie Chart Plugin (instalado automáticamente)
- Auto-provisioning de datasource Prometheus
- Auto-provisioning de 3 dashboards
- Refresh automático cada 10s

**Credenciales por defecto**:
```
Usuario: admin
Password: ${GRAFANA_ADMIN_PASSWORD} (definir en .env)
```

**Datasource Prometheus**:
- URL: `http://prometheus:9090`
- Timeout: 60s
- Query interval: 15s
- Default: Yes

---

### 4. Exporters

#### PostgreSQL Exporter (v0.15.0)
**Puerto**: 9187
**Métricas**: Conexiones, transacciones, cache hit ratio, locks, deadlocks, tamaño DB, tuple operations

**Variables requeridas**:
```env
DATA_SOURCE_NAME=postgresql://usuario:password@postgres:5432/alojamientos?sslmode=disable
```

#### Redis Exporter (v1.55.0)
**Puerto**: 9121
**Métricas**: Memoria, hits/misses, evictions, conexiones, comandos

**Variables requeridas**:
```env
REDIS_ADDR=redis:6379
REDIS_PASSWORD=tu_password
```

#### Node Exporter (v1.7.0)
**Puerto**: 9100
**Métricas**: CPU, memoria, disco, network, filesystem, load average

**Mounts requeridos**:
- `/proc:/host/proc:ro`
- `/sys:/host/sys:ro`
- `/:/rootfs:ro`

#### cAdvisor (v0.47.2)
**Puerto**: 8080
**Métricas**: CPU container, memoria container, network, filesystem

**Mounts requeridos**:
- `/:/rootfs:ro`
- `/var/run:/var/run:ro`
- `/sys:/sys:ro`
- `/var/lib/docker/:/var/lib/docker:ro`
- `/dev/disk/:/dev/disk:ro`

---

## 🚀 Instalación

### Requisitos Previos

- Docker 24+ y Docker Compose 2.x
- Sistema backend corriendo (FastAPI + PostgreSQL + Redis)
- Puertos disponibles: 3000, 9090, 9093, 9100, 9121, 9187, 8080

### Paso 1: Clonar Configuraciones

```bash
cd /ruta/a/proyecto
git pull origin main
```

Las configuraciones están en:
```
monitoring/
├── docker-compose.yml
├── prometheus/
│   ├── prometheus.yml
│   └── rules/
│       └── alerts.yml
├── alertmanager/
│   └── alertmanager.yml
└── grafana/
    ├── provisioning/
    │   ├── datasources/
    │   │   └── prometheus.yml
    │   └── dashboards/
    │       └── dashboards.yml
    └── dashboards/
        ├── api-overview.json
        ├── database.json
        └── infrastructure.json
```

### Paso 2: Configurar Variables de Entorno

Crear archivo `monitoring/.env`:

```env
# === Grafana ===
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=tu_password_seguro

# === PostgreSQL Exporter ===
POSTGRES_USER=alojamientos_user
POSTGRES_PASSWORD=tu_db_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=alojamientos

# === Redis Exporter ===
REDIS_ADDR=redis:6379
REDIS_PASSWORD=tu_redis_password

# === Alertmanager - Slack ===
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX

# === Alertmanager - Email (opcional) ===
SMTP_FROM=alertmanager@tudominio.com
SMTP_SMARTHOST=smtp.gmail.com:587
SMTP_AUTH_USERNAME=tu_email@gmail.com
SMTP_AUTH_PASSWORD=tu_app_password

# === Alertmanager - PagerDuty (opcional) ===
PAGERDUTY_SERVICE_KEY=tu_integration_key
```

### Paso 3: Validar Configuraciones

```bash
# Validar YAML de Prometheus
docker run --rm -v $(pwd)/monitoring/prometheus:/etc/prometheus \
  prom/prometheus:v2.47.2 \
  promtool check config /etc/prometheus/prometheus.yml

# Validar alert rules
docker run --rm -v $(pwd)/monitoring/prometheus:/etc/prometheus \
  prom/prometheus:v2.47.2 \
  promtool check rules /etc/prometheus/rules/alerts.yml

# Validar Alertmanager
docker run --rm -v $(pwd)/monitoring/alertmanager:/etc/alertmanager \
  prom/alertmanager:v0.26.0 \
  amtool check-config /etc/alertmanager/alertmanager.yml
```

### Paso 4: Crear Network Externa

El stack de monitoring se conecta a la red del backend:

```bash
# Verificar que exista la red backend
docker network ls | grep sist_cabanas_backend

# Si no existe, crearla (o iniciar el backend primero)
cd backend && docker-compose up -d
```

### Paso 5: Iniciar Stack de Monitoring

```bash
cd monitoring
docker-compose up -d
```

**Orden de inicio** (automático con `depends_on`):
1. Exporters (postgres, redis, node, cadvisor)
2. Prometheus
3. Alertmanager
4. Grafana

### Paso 6: Verificar Health Checks

```bash
# Ver estado de todos los servicios
docker-compose ps

# Debe mostrar todos como "healthy"
```

**Expected output**:
```
NAME                    STATUS              PORTS
prometheus              Up (healthy)        0.0.0.0:9090->9090/tcp
alertmanager            Up (healthy)        0.0.0.0:9093->9093/tcp
grafana                 Up (healthy)        0.0.0.0:3000->3000/tcp
postgres-exporter       Up (healthy)        0.0.0.0:9187->9187/tcp
redis-exporter          Up (healthy)        0.0.0.0:9121->9121/tcp
node-exporter           Up (healthy)        0.0.0.0:9100->9100/tcp
cadvisor                Up (healthy)        0.0.0.0:8080->8080/tcp
```

### Paso 7: Verificar Conectividad

```bash
# Test Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Debe mostrar todos los targets como "up"
```

---

## ⚙️ Configuración

### Ajustar Scrape Intervals

Editar `monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'alojamientos-api'
    scrape_interval: 10s  # Cambiar según necesidad (min: 5s)
    static_configs:
      - targets: ['api:8000']
```

**Recargar configuración** (sin reiniciar):
```bash
curl -X POST http://localhost:9090/-/reload
```

### Ajustar Retención de Datos

Editar `monitoring/docker-compose.yml`:

```yaml
services:
  prometheus:
    command:
      - '--storage.tsdb.retention.time=30d'  # Cambiar a 7d, 15d, 90d, etc.
```

**Aplicar cambio**:
```bash
docker-compose up -d prometheus
```

### Configurar Notificaciones Slack

1. Crear **Incoming Webhook** en Slack:
   - Ir a: https://api.slack.com/apps → Create New App
   - Activar "Incoming Webhooks"
   - Copiar Webhook URL

2. Actualizar `.env`:
```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

3. Reiniciar Alertmanager:
```bash
docker-compose restart alertmanager
```

4. **Test de notificación**:
```bash
curl -X POST http://localhost:9093/api/v1/alerts -H "Content-Type: application/json" -d '[
  {
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "Test notification from Alertmanager"
    }
  }
]'
```

### Configurar Email (SMTP)

Editar `monitoring/.env`:

```env
SMTP_FROM=alertmanager@tudominio.com
SMTP_SMARTHOST=smtp.gmail.com:587
SMTP_AUTH_USERNAME=tu_email@gmail.com
SMTP_AUTH_PASSWORD=tu_app_password  # Gmail: usar App Password
```

**Para Gmail**:
1. Habilitar verificación en 2 pasos
2. Crear App Password: https://myaccount.google.com/apppasswords
3. Usar el password generado (16 caracteres)

**Reiniciar Alertmanager**:
```bash
docker-compose restart alertmanager
```

---

## 🌐 Acceso a Servicios

### Grafana
- **URL**: http://localhost:3000
- **Usuario**: `admin`
- **Password**: Definido en `GRAFANA_ADMIN_PASSWORD`

**Dashboards disponibles** (carpeta raíz):
- API Overview - Sistema Alojamientos
- Database - Sistema Alojamientos
- Infrastructure - Sistema Alojamientos

### Prometheus
- **URL**: http://localhost:9090
- **Sin autenticación** (interno)

**Queries útiles**:
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# DB connections
pg_stat_database_numbackends{datname="alojamientos"}

# Redis memory
redis_memory_used_bytes / redis_memory_max_bytes * 100
```

### Alertmanager
- **URL**: http://localhost:9093
- **Sin autenticación** (interno)

**Páginas útiles**:
- `/` - Dashboard de alertas activas
- `/#/alerts` - Todas las alertas (activas, silenciadas)
- `/#/silences` - Gestión de silenciamientos

**Silenciar alerta temporalmente**:
```bash
# Silenciar alerta "HighCPUUsage" por 2 horas
amtool silence add alertname=HighCPUUsage --duration=2h \
  --author="admin" --comment="Maintenance window"
```

---

## 📊 Dashboards

### 1. API Overview Dashboard

**Panels incluidos**:

| Panel                  | Métrica                          | Threshold           |
|------------------------|----------------------------------|---------------------|
| Request Rate           | `rate(http_requests_total)`      | N/A                 |
| Error Rate (5xx)       | `rate(5xx) / rate(total)`        | 🟡 1%, 🔴 5%       |
| Response Time P50/P95/P99 | `histogram_quantile()`        | 🟡 3s, 🔴 5s       |
| API Status             | `up{job="alojamientos-api"}`     | 🔴 0, 🟢 1         |
| iCal Sync Age          | `(time() - ical_last_sync) / 60` | 🟡 20m, 🔴 30m     |
| Active Connections     | `process_open_fds`               | 🟡 50, 🔴 100      |
| API Memory Usage       | `process_resident_memory_bytes`  | 🟡 500MB, 🔴 1GB   |

**Variables disponibles**: Ninguna (dashboard simple)

**Refresh**: 10s

---

### 2. Database Dashboard

**Panels incluidos**:

| Panel                  | Métrica                          | Threshold           |
|------------------------|----------------------------------|---------------------|
| Database Status        | `pg_up`                          | 🔴 0, 🟢 1         |
| Active Connections     | `pg_stat_database_numbackends`   | 🟡 50, 🔴 80       |
| Cache Hit Ratio        | `blks_hit / (blks_hit + blks_read)` | 🟡 85%, 🔴 95%  |
| Deadlocks              | `pg_stat_database_deadlocks`     | 🟡 1, 🔴 10        |
| Transaction Rate       | `rate(xact_commit/rollback)`     | N/A                 |
| Tuple Operations       | `rate(tup_inserted/updated/deleted)` | N/A             |
| Database Size          | `pg_database_size_bytes`         | Info                |
| Top 5 Active Tables    | `n_tup_ins + n_tup_upd + n_tup_del` | Info            |
| Database Locks         | `pg_locks_count`                 | Info                |

**Refresh**: 10s

---

### 3. Infrastructure Dashboard

**Panels incluidos**:

| Panel                  | Métrica                          | Threshold           |
|------------------------|----------------------------------|---------------------|
| CPU Usage              | `100 - rate(cpu idle)`           | 🟡 70%, 🔴 90%     |
| Memory Usage           | `(MemTotal - MemAvailable) / MemTotal` | 🟡 75%, 🔴 90% |
| Disk Usage (Root)      | `(size - avail) / size`          | 🟡 80%, 🔴 95%     |
| Node Exporter Status   | `up{job="node"}`                 | 🔴 0, 🟢 1         |
| CPU Usage by Mode      | `rate(cpu user/system/iowait/idle)` | N/A             |
| Memory Details         | `MemUsed/Available/Cached/Buffers` | N/A              |
| Disk I/O               | `rate(disk_read/written_bytes)`  | N/A                 |
| Network I/O            | `rate(network_receive/transmit)` | N/A                 |
| Running Containers     | `count(container_last_seen)`     | Info                |
| Container Memory       | `container_memory_usage_bytes`   | Info                |

**Refresh**: 10s

---

## 🚨 Alertas

### Alertas Críticas (CRITICAL)

Requieren **acción inmediata**. Envían notificación a Slack + Email.

| Alerta                  | Condición                        | For  | Acción                  |
|-------------------------|----------------------------------|------|-------------------------|
| **APIDown**             | `up{job="api"} == 0`             | 1m   | Ver [Runbook](#runbook-apidown) |
| **DatabaseDown**        | `pg_up == 0`                     | 1m   | Ver [Runbook](#runbook-databasedown) |
| **RedisDown**           | `redis_up == 0`                  | 1m   | Ver [Runbook](#runbook-redisdown) |
| **CriticalCPUUsage**    | `CPU > 95%`                      | 5m   | Ver [Runbook](#runbook-cpu) |
| **CriticalMemoryUsage** | `Memory > 95%`                   | 5m   | Ver [Runbook](#runbook-memory) |
| **CriticalDiskSpace**   | `Disk > 95%`                     | 5m   | Ver [Runbook](#runbook-disk) |

### Alertas de Warning (WARNING)

Requieren **atención próxima**. Envían notificación solo a Slack.

| Alerta                   | Condición                        | For  |
|--------------------------|----------------------------------|------|
| **HighErrorRate**        | `Error rate > 5%`                | 5m   |
| **SlowResponseTime**     | `P95 > 5s`                       | 10m  |
| **HighDatabaseConnections** | `Connections > 80%`           | 5m   |
| **HighCPUUsage**         | `CPU > 80%`                      | 10m  |
| **HighMemoryUsage**      | `Memory > 85%`                   | 10m  |
| **LowDiskSpace**         | `Disk > 85%`                     | 10m  |

### Alertas Informativas (INFO)

**Monitoreo preventivo**. Notificaciones de baja prioridad.

| Alerta                   | Condición                        | For  |
|--------------------------|----------------------------------|------|
| **VerySlowResponseTime** | `P99 > 10s`                      | 15m  |
| **ICalSyncStale**        | `Last sync > 30 min`             | 5m   |
| **HighRequestRate**      | `Requests > umbral esperado`     | 5m   |
| **SlowQueries**          | `Query duration > threshold`     | 10m  |
| **DatabaseDeadlocks**    | `Deadlocks > 0`                  | 5m   |

---

## 🛠️ Troubleshooting

### Problema: Servicios no inician

**Síntoma**: `docker-compose ps` muestra servicios en estado `Exited` o `Restarting`

**Solución**:
```bash
# Ver logs del servicio problemático
docker-compose logs prometheus
docker-compose logs alertmanager
docker-compose logs grafana

# Errores comunes:
# 1. Error de sintaxis YAML → Validar con promtool/amtool
# 2. Permisos de volúmenes → Verificar ownership
# 3. Puertos en uso → Verificar con netstat/ss
```

**Fix de permisos**:
```bash
sudo chown -R 65534:65534 monitoring/prometheus_data
sudo chown -R 65534:65534 monitoring/alertmanager_data
sudo chown -R 472:472 monitoring/grafana_data
```

---

### Problema: Targets "down" en Prometheus

**Síntoma**: En http://localhost:9090/targets algunos aparecen en rojo

**Diagnóstico**:
```bash
# Verificar conectividad desde Prometheus
docker exec -it prometheus wget -O- http://api:8000/metrics
docker exec -it prometheus wget -O- http://postgres-exporter:9187/metrics

# Verificar que el servicio exporte métricas
curl http://localhost:8000/metrics  # API
curl http://localhost:9187/metrics  # PostgreSQL
```

**Soluciones**:
- Si API no exporta `/metrics` → Verificar instrumentación FastAPI
- Si exporter no responde → Revisar logs del exporter
- Si network error → Verificar que ambos estén en la red correcta

---

### Problema: Alertas no se envían a Slack

**Síntoma**: Alerta activa en Alertmanager pero no llega a Slack

**Diagnóstico**:
```bash
# Ver logs de Alertmanager
docker-compose logs alertmanager | grep -i slack

# Test manual de webhook
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test from Alertmanager"}' \
  $SLACK_WEBHOOK_URL
```

**Soluciones**:
- Webhook URL incorrecta → Verificar en `.env`
- Canal no existe → Crear canal en Slack workspace
- Permisos de app → Re-instalar app en workspace

---

### Problema: Dashboards no cargan métricas

**Síntoma**: Paneles vacíos o "No data"

**Diagnóstico**:
```bash
# Verificar datasource en Grafana
curl -u admin:password http://localhost:3000/api/datasources

# Test query manual en Prometheus
curl http://localhost:9090/api/v1/query?query=up

# Verificar tiempo de retención
curl http://localhost:9090/api/v1/status/config | jq '.data.yaml' | grep retention
```

**Soluciones**:
- Datasource no configurado → Re-importar desde provisioning
- Query incorrecta → Probar en Prometheus UI primero
- Datos fuera de rango temporal → Ajustar time range en dashboard

---

### Problema: Alto uso de disco por Prometheus

**Síntoma**: Volumen `prometheus_data` crece rápidamente

**Diagnóstico**:
```bash
# Ver tamaño del volumen
docker exec prometheus du -sh /prometheus

# Ver series temporales almacenadas
curl http://localhost:9090/api/v1/status/tsdb | jq '.data.numSeries'
```

**Soluciones**:
```bash
# Reducir retención (editar docker-compose.yml)
--storage.tsdb.retention.time=7d  # En lugar de 30d

# Limpiar datos viejos manualmente
docker exec prometheus rm -rf /prometheus/data/old_blocks

# Reiniciar Prometheus
docker-compose restart prometheus
```

---

## 🔧 Mantenimiento

### Backup de Métricas

**Prometheus** (snapshots):
```bash
# Crear snapshot
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot

# Copiar snapshot
SNAPSHOT=$(curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot | jq -r '.data.name')
docker cp prometheus:/prometheus/snapshots/$SNAPSHOT ./backups/prometheus-$(date +%Y%m%d).tar.gz
```

**Grafana** (dashboards):
```bash
# Exportar dashboards vía API
for uid in api-overview database infrastructure; do
  curl -u admin:password "http://localhost:3000/api/dashboards/uid/$uid" | \
    jq '.dashboard' > backups/dashboard-$uid-$(date +%Y%m%d).json
done
```

---

### Actualizar Versiones

**Prometheus**:
```yaml
# En docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:v2.48.0  # Actualizar versión
```

```bash
docker-compose pull prometheus
docker-compose up -d prometheus
```

**Grafana**:
```yaml
services:
  grafana:
    image: grafana/grafana:10.3.0  # Actualizar versión
```

```bash
docker-compose pull grafana
docker-compose up -d grafana
```

---

### Limpieza de Datos

**Limpiar alertas resueltas**:
```bash
# Desde Alertmanager UI
# o vía API:
curl -X DELETE http://localhost:9093/api/v1/alerts
```

**Limpiar volúmenes no usados**:
```bash
docker volume prune
```

---

## 📚 Referencias

- **Prometheus**: https://prometheus.io/docs/
- **Alertmanager**: https://prometheus.io/docs/alerting/latest/alertmanager/
- **Grafana**: https://grafana.com/docs/grafana/latest/
- **PostgreSQL Exporter**: https://github.com/prometheus-community/postgres_exporter
- **Redis Exporter**: https://github.com/oliver006/redis_exporter
- **Node Exporter**: https://github.com/prometheus/node_exporter
- **cAdvisor**: https://github.com/google/cadvisor

---

## ✅ Checklist de Instalación

- [ ] Variables de entorno configuradas en `.env`
- [ ] Network `sist_cabanas_backend` creada
- [ ] Configuraciones YAML validadas con promtool/amtool
- [ ] Stack iniciado con `docker-compose up -d`
- [ ] Todos los servicios en estado `healthy`
- [ ] Targets "up" en Prometheus (http://localhost:9090/targets)
- [ ] Dashboards cargando en Grafana (http://localhost:3000)
- [ ] Test de alerta enviado a Slack exitosamente
- [ ] Documentación de runbooks revisada

---

**📌 Próximos Pasos**: Configurar [Alert Runbooks](ALERT_RUNBOOK.md) para respuesta a incidentes
