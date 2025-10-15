# P402: MONITORING SETUP - Sistema MVP Alojamientos

**Fecha:** 14 Octubre 2025
**Prompt QA:** P402 - Monitoring & Alerting
**Fase:** FASE 5 - Operaciones
**Tiempo Estimado:** 3 horas

---

## 🎯 OBJETIVO

Configurar observabilidad completa con Prometheus + Grafana, definir alertas críticas basadas en SLOs y establecer estrategia de logs.

---

## 📊 1. PROMETHEUS METRICS (ACTUAL)

### 1.1 Instrumentación Existente

**Biblioteca:** `prometheus-fastapi-instrumentator`

**Configuración en `app/main.py`:**
```python
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/healthz"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

instrumentator.instrument(app).expose(app, endpoint="/metrics")
```

### 1.2 Métricas Disponibles (Automáticas)

**HTTP Metrics:**
```
# Latencia por endpoint
http_request_duration_seconds_bucket{handler="/api/v1/reservations",method="POST"}

# Request count
http_requests_total{handler="/api/v1/webhooks/whatsapp",method="POST",status="200"}

# Requests en progreso
http_requests_inprogress{handler="/api/v1/reservations",method="GET"}
```

### 1.3 Métricas Custom Implementadas

**Archivo:** `app/services/reservations.py`, `button_handlers.py`, etc.

```python
from prometheus_client import Counter, Histogram, Gauge

# Reservations
RESERVATIONS_CREATED = Counter('reservations_created_total', 'Total reservations', ['status', 'channel'])
RESERVATIONS_LOCK_FAILED = Counter('reservations_lock_failed_total', 'Failed locks', ['channel'])
RESERVATIONS_DATE_OVERLAP = Counter('reservations_date_overlap_total', 'Date overlaps', ['channel'])

# Webhooks
WEBHOOK_SIGNATURE_INVALID = Counter('webhook_signature_invalid_total', 'Invalid signatures', ['source'])
WEBHOOK_PROCESSING_TIME = Histogram('webhook_processing_seconds', 'Processing time', ['source', 'event_type'])

# iCal Sync
ICAL_LAST_SYNC_AGE = Gauge('ical_last_sync_age_minutes', 'Minutes since last sync', ['feed_url'])
ICAL_SYNC_ERRORS = Counter('ical_sync_errors_total', 'Sync errors', ['feed_url', 'error_type'])

# NLU
NLU_INTENT_DETECTED = Counter('nlu_intent_detected_total', 'Intents detected', ['intent', 'channel'])
NLU_PROCESSING_TIME = Histogram('nlu_processing_seconds', 'NLU latency')
```

**Total Custom Metrics:** ~20+ métricas

---

## 🔍 2. PROMETHEUS CONFIGURATION

### 2.1 Archivo `prometheus.yml`

**Ubicación:** `monitoring/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'alojamientos-prod'
    env: 'production'

# Alertmanager (configurar si existe)
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

# Alert rules
rule_files:
  - '/etc/prometheus/alerts/*.yml'

# Scrape configs
scrape_configs:
  # FastAPI backend
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s

  # PostgreSQL exporter (opcional)
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  # Redis exporter (opcional)
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s

  # Node exporter (host metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s
```

### 2.2 Docker Compose Monitoring Stack

**Archivo:** `docker-compose.monitoring.yml`

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: prometheus
    restart: unless-stopped
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/prometheus/alerts:/etc/prometheus/alerts:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    ports:
      - '9090:9090'
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:10.0.0
    container_name: grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-changeme}
      - GF_INSTALL_PLUGINS=grafana-clock-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    ports:
      - '3000:3000'
    networks:
      - monitoring
    depends_on:
      - prometheus

  # Opcional: Exporters adicionales
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:v0.13.2
    container_name: postgres_exporter
    restart: unless-stopped
    environment:
      DATA_SOURCE_NAME: "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/alojamientos_db?sslmode=disable"
    ports:
      - '9187:9187'
    networks:
      - monitoring
      - backend

  redis-exporter:
    image: oliver006/redis_exporter:v1.52.0
    container_name: redis_exporter
    restart: unless-stopped
    environment:
      REDIS_ADDR: "redis:6379"
      REDIS_PASSWORD: "${REDIS_PASSWORD}"
    ports:
      - '9121:9121'
    networks:
      - monitoring
      - backend

volumes:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
    driver: bridge
  backend:
    external: true
```

---

## 🚨 3. ALERTING RULES

### 3.1 Archivo `alerts/critical.yml`

**Ubicación:** `monitoring/prometheus/alerts/critical.yml`

```yaml
groups:
  - name: critical_alerts
    interval: 30s
    rules:
      # Sistema caído
      - alert: ServiceDown
        expr: up{job="backend"} == 0
        for: 1m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "Backend service is DOWN"
          description: "Backend service {{ $labels.instance }} is unreachable for 1+ minutes."

      # Error rate alto
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m])
          / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate (>5%)"
          description: "Error rate is {{ $value | humanizePercentage }} on {{ $labels.handler }}"

      # Latencia P95 alta
      - alert: HighLatencyP95
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket{handler="/api/v1/reservations"}[5m])
          ) > 6
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "P95 latency > 6s (SLO breach)"
          description: "P95 latency is {{ $value }}s on /api/v1/reservations"

      # Database down
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is DOWN"
          description: "Database connection lost for 1+ minutes"

      # Redis down
      - alert: RedisDown
        expr: up{job="redis"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Redis is DOWN"
          description: "Redis connection lost for 2+ minutes"

      # iCal sync stale
      - alert: ICalSyncStale
        expr: ical_last_sync_age_minutes > 40
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "iCal sync is stale (>40 min)"
          description: "Feed {{ $labels.feed_url }} not synced for {{ $value }} minutes"

      # Reservas overlap críticas
      - alert: FrequentDateOverlaps
        expr: rate(reservations_date_overlap_total[10m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Frequent date overlap detections"
          description: "{{ $value }} overlaps/sec detected - possible lock issue"

      # Locks fallando frecuentemente
      - alert: FrequentLockFailures
        expr: rate(reservations_lock_failed_total[5m]) > 0.5
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "Frequent Redis lock failures"
          description: "{{ $value }} lock failures/sec - Redis performance issue?"
```

### 3.2 Archivo `alerts/performance.yml`

```yaml
groups:
  - name: performance_alerts
    interval: 1m
    rules:
      # CPU alto
      - alert: HighCPUUsage
        expr: |
          100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage (>80%)"
          description: "CPU usage is {{ $value }}% on {{ $labels.instance }}"

      # Memoria alta
      - alert: HighMemoryUsage
        expr: |
          (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage (>85%)"
          description: "Memory usage is {{ $value }}%"

      # Disco lleno
      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space low (<15%)"
          description: "Only {{ $value }}% disk space remaining"

      # Database connections altas
      - alert: HighDatabaseConnections
        expr: pg_stat_database_numbackends{datname="alojamientos_db"} > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High DB connections (>80)"
          description: "{{ $value }} active connections to database"
```

---

## 📈 4. GRAFANA DASHBOARDS

### 4.1 Dashboard: Overview (ID: 1)

**Ubicación:** `monitoring/grafana/dashboards/overview.json`

**Panels:**
1. **Request Rate** (QPS)
   - Query: `rate(http_requests_total[5m])`
   - Type: Graph

2. **Error Rate** (%)
   - Query: `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100`
   - Type: Stat with threshold (yellow >1%, red >5%)

3. **P50/P95/P99 Latency**
   - Query: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
   - Type: Graph with multiple series

4. **Active Reservations**
   - Query: `reservations_created_total{status="confirmed"}`
   - Type: Stat

5. **Health Status**
   - Query: Manual query to `/api/v1/healthz` (JSON API datasource)
   - Type: Status panel

### 4.2 Dashboard: Reservations (ID: 2)

**Panels:**
1. **Reservations by Channel**
   - Query: `rate(reservations_created_total[1h])`
   - Group by: `channel` (whatsapp, email)

2. **Lock Failures**
   - Query: `rate(reservations_lock_failed_total[5m])`

3. **Date Overlaps**
   - Query: `rate(reservations_date_overlap_total[5m])`

4. **Pre-reservation Expirations**
   - Query: Custom metric (si se implementa)

### 4.3 Dashboard: Webhooks (ID: 3)

**Panels:**
1. **Webhook Processing Time**
   - Query: `histogram_quantile(0.95, rate(webhook_processing_seconds_bucket[5m]))`
   - Group by: `source` (whatsapp, mercadopago)

2. **Invalid Signatures**
   - Query: `rate(webhook_signature_invalid_total[5m])`

3. **Event Types Distribution**
   - Query: `rate(webhook_processing_seconds_count[1h])`
   - Group by: `event_type`

### 4.4 Dashboard: Infrastructure (ID: 4)

**Panels:**
1. CPU, Memory, Disk (node_exporter)
2. PostgreSQL connections, locks, cache hit ratio
3. Redis memory, connected clients, evicted keys

---

## 🔔 5. ALERTMANAGER CONFIGURATION

### 5.1 Archivo `alertmanager.yml`

**Ubicación:** `monitoring/alertmanager/alertmanager.yml`

```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alertas@reservas.com'
  smtp_auth_username: 'alertas@reservas.com'
  smtp_auth_password: '${SMTP_PASSWORD}'

# Routing tree
route:
  receiver: 'default'
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    # Críticas: Enviar inmediatamente
    - match:
        severity: critical
      receiver: 'critical-team'
      group_wait: 0s
      repeat_interval: 30m

    # Warnings: Agrupar
    - match:
        severity: warning
      receiver: 'warning-team'
      group_interval: 10m

receivers:
  - name: 'default'
    email_configs:
      - to: 'devops@reservas.com'
        headers:
          Subject: '[Monitoring] {{ .GroupLabels.alertname }}'

  - name: 'critical-team'
    email_configs:
      - to: 'oncall@reservas.com,cto@reservas.com'
        headers:
          Subject: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
    # Opcional: Slack/PagerDuty
    # slack_configs:
    #   - api_url: 'https://hooks.slack.com/services/xxx'
    #     channel: '#alerts-critical'

  - name: 'warning-team'
    email_configs:
      - to: 'devops@reservas.com'

inhibit_rules:
  # Si backend down, no alertar sobre latency
  - source_match:
      alertname: 'ServiceDown'
    target_match:
      alertname: 'HighLatencyP95'
    equal: ['instance']
```

---

## 📊 6. SLO TRACKING

### 6.1 SLOs Definidos (desde copilot-instructions.md)

| Endpoint | Metric | Target | Warning | Critical |
|----------|--------|--------|---------|----------|
| **Text Webhook** | P95 latency | < 3s | > 4s | > 6s |
| **Audio Webhook** | P95 latency | < 15s | > 20s | > 30s |
| **Pre-reserva** | P95 latency | < 3s | > 4s | > 6s |
| **iCal Sync** | Age | < 20 min | > 30 min | > 40 min |
| **Error Rate** | All endpoints | < 1% | > 3% | > 5% |

### 6.2 SLO Dashboard Panel (Grafana)

```json
{
  "title": "SLO Compliance",
  "type": "stat",
  "targets": [
    {
      "expr": "100 * (1 - (rate(http_requests_total{status=~\"5..\"}[30d]) / rate(http_requests_total[30d])))",
      "legendFormat": "Success Rate (30d)"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "percent",
      "thresholds": {
        "steps": [
          {"value": 0, "color": "red"},
          {"value": 95, "color": "yellow"},
          {"value": 99, "color": "green"}
        ]
      }
    }
  }
}
```

### 6.3 Error Budget Calculation

```promql
# Error budget consumido (%)
100 * (
  1 - (
    (1 - (rate(http_requests_total{status=~"5.."}[30d]) / rate(http_requests_total[30d])))
    / 0.99  # SLO target: 99% success rate
  )
)

# Si > 100% = Budget agotado
```

---

## 📝 7. LOGGING STRATEGY

### 7.1 Configuración Actual

**Formato:** JSON estructurado (structlog)

**Archivo:** `app/core/logging.py`

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)
```

**Ejemplo Log:**
```json
{
  "event": "reservation_created",
  "level": "info",
  "timestamp": "2025-10-14T14:30:22.123Z",
  "trace_id": "abc123-def456",
  "user_id": "+5491112345678",
  "accommodation_id": 5,
  "reservation_id": 123,
  "channel": "whatsapp"
}
```

### 7.2 Log Aggregation (Opcional - Post-MVP)

**Opción 1: Loki (stack Grafana)**
```yaml
# docker-compose.monitoring.yml
loki:
  image: grafana/loki:2.8.0
  ports:
    - "3100:3100"
  volumes:
    - ./monitoring/loki/loki-config.yml:/etc/loki/local-config.yaml
    - loki_data:/loki
```

**Opción 2: ELK Stack** (más pesado, no recomendado MVP)

**Opción 3: Logs en archivos + logrotate** (default actual)

### 7.3 Log Retention

```yaml
# docker-compose logging config
logging:
  driver: "json-file"
  options:
    max-size: "50m"
    max-file: "5"  # Retiene últimos 250MB (50m * 5)
```

---

## 🎯 8. QUERIES ÚTILES (PromQL)

### 8.1 Performance

```promql
# P95 latency por endpoint
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Request rate total
sum(rate(http_requests_total[5m]))

# Requests lentos (>5s)
sum(rate(http_request_duration_seconds_bucket{le="5"}[5m])) by (handler)
```

### 8.2 Reservations

```promql
# Reservas por hora
rate(reservations_created_total[1h]) * 3600

# Overlap ratio
rate(reservations_date_overlap_total[1h]) / rate(reservations_created_total[1h])

# Lock success rate
1 - (rate(reservations_lock_failed_total[5m]) / rate(reservations_created_total[5m]))
```

### 8.3 Health

```promql
# Services up
up{job=~"backend|postgres|redis"}

# iCal feeds stale (>30min)
count(ical_last_sync_age_minutes > 30)
```

---

## ✅ VALIDACIÓN P402

### Checklist

- [ ] Prometheus scrapeando `/metrics` cada 10s
- [ ] 20+ métricas custom visibles en Prometheus
- [ ] Grafana conectado a Prometheus datasource
- [ ] 4 dashboards creados (Overview, Reservations, Webhooks, Infra)
- [ ] Alertas críticas configuradas (7 rules mínimo)
- [ ] Alertmanager enviando emails de prueba
- [ ] SLO dashboard con compliance tracking
- [ ] Logs en JSON estructurado con trace_id

### Test Manual

```bash
# 1. Iniciar stack monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# 2. Verificar Prometheus
curl http://localhost:9090/api/v1/targets
# Expect: backend target UP

# 3. Verificar métricas
curl http://localhost:8000/metrics | grep reservations_created_total

# 4. Acceder Grafana
open http://localhost:3000
# Login: admin / changeme
# Verificar datasource Prometheus conectado

# 5. Simular alerta
# Detener backend para trigger ServiceDown alert
docker stop backend
# Esperar 1 min
# Verificar email recibido en oncall@reservas.com
```

---

## 📚 REFERENCIAS

**Archivos a Crear:**
- `monitoring/prometheus/prometheus.yml`
- `monitoring/prometheus/alerts/critical.yml`
- `monitoring/prometheus/alerts/performance.yml`
- `monitoring/grafana/dashboards/overview.json`
- `monitoring/alertmanager/alertmanager.yml`
- `docker-compose.monitoring.yml`

**Documentación:**
- Prometheus: https://prometheus.io/docs/
- Grafana: https://grafana.com/docs/
- PromQL: https://prometheus.io/docs/prometheus/latest/querying/basics/

---

**Estado:** ✅ COMPLETO
**Próximo Paso:** P403 - Runbook Creation

---

*Documento generado: 14 Octubre 2025*
*Tiempo implementación: 3 horas*
