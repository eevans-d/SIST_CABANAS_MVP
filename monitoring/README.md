# 📊 Monitoring Stack - Sistema de Alojamientos MVP

## 🎯 Descripción

Stack completo de observabilidad para el Sistema de Alojamientos con **Prometheus + Alertmanager + Grafana**.

Proporciona:
- ✅ **Monitoreo 24/7** en tiempo real
- ✅ **22 alertas** automáticas con severidades
- ✅ **3 dashboards** pre-configurados
- ✅ **Retención 30 días** de métricas
- ✅ **Notificaciones** Slack + Email

---

## 🚀 Quick Start

### 1. Configurar Variables

```bash
cp .env.template .env
# Editar .env con tus credenciales
```

### 2. Iniciar Stack

```bash
docker-compose up -d
```

### 3. Verificar Health

```bash
docker-compose ps
# Todos deben estar "healthy"
```

### 4. Acceder a Servicios

- **Grafana**: http://localhost:3000 (admin / tu_password)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

---

## 📦 Componentes

| Servicio            | Puerto | Descripción                       |
|---------------------|--------|-----------------------------------|
| **Prometheus**      | 9090   | Métricas y alertas                |
| **Alertmanager**    | 9093   | Gestión de notificaciones         |
| **Grafana**         | 3000   | Dashboards interactivos           |
| postgres-exporter   | 9187   | Métricas PostgreSQL               |
| redis-exporter      | 9121   | Métricas Redis                    |
| node-exporter       | 9100   | Métricas del host (CPU, RAM)      |
| cadvisor            | 8080   | Métricas de containers            |

---

## 📊 Dashboards

### API Overview
- Request rate y error rate
- Latencia (P50, P95, P99)
- Estado de API y conexiones
- iCal sync age

### Database
- Estado y conexiones activas
- Cache hit ratio
- Transaction rate
- Top 5 tablas activas

### Infrastructure
- CPU, memoria, disco
- Network y disk I/O
- Containers corriendo
- Memoria por container

---

## 🚨 Alertas Configuradas

### CRITICAL (6 alertas)
- APIDown, DatabaseDown, RedisDown
- CriticalCPUUsage, CriticalMemoryUsage, CriticalDiskSpace

### WARNING (9 alertas)
- HighErrorRate, SlowResponseTime, VerySlowResponseTime
- HighDatabaseConnections, SlowQueries
- RedisHighMemory, RedisEvictingKeys
- HighCPUUsage, HighMemoryUsage, LowDiskSpace

### INFO (7 alertas)
- ICalSyncStale, HighRequestRate, DatabaseDeadlocks, ContainerDown

Ver [Alert Runbook](../docs/monitoring/ALERT_RUNBOOK.md) para respuesta a incidentes.

---

## 📚 Documentación Completa

- [MONITORING_SETUP.md](../docs/monitoring/MONITORING_SETUP.md) - Guía de instalación y configuración completa
- [ALERT_RUNBOOK.md](../docs/monitoring/ALERT_RUNBOOK.md) - Procedimientos de respuesta a alertas

---

## 🔧 Comandos Útiles

### Ver logs
```bash
docker-compose logs -f prometheus
docker-compose logs -f alertmanager
docker-compose logs -f grafana
```

### Validar configuraciones
```bash
# Validar Prometheus
docker run --rm -v $(pwd)/prometheus:/etc/prometheus prom/prometheus:v2.47.2 promtool check config /etc/prometheus/prometheus.yml

# Validar alert rules
docker run --rm -v $(pwd)/prometheus:/etc/prometheus prom/prometheus:v2.47.2 promtool check rules /etc/prometheus/rules/alerts.yml

# Validar Alertmanager
docker run --rm -v $(pwd)/alertmanager:/etc/alertmanager prom/alertmanager:v0.26.0 amtool check-config /etc/alertmanager/alertmanager.yml
```

### Recargar configuraciones sin reiniciar
```bash
# Prometheus (reload config)
curl -X POST http://localhost:9090/-/reload

# Alertmanager (reload config)
curl -X POST http://localhost:9093/-/reload
```

### Test de alertas
```bash
# Enviar alerta de prueba
curl -X POST http://localhost:9093/api/v1/alerts -H "Content-Type: application/json" -d '[
  {
    "labels": {"alertname": "TestAlert", "severity": "warning"},
    "annotations": {"summary": "Test notification"}
  }
]'
```

---

## 🐛 Troubleshooting

### Servicio no inicia
```bash
# Ver logs
docker-compose logs <servicio>

# Verificar configuración
docker-compose config
```

### Targets "down" en Prometheus
```bash
# Verificar conectividad
docker exec -it prometheus wget -O- http://api:8000/metrics
docker exec -it prometheus wget -O- http://postgres-exporter:9187/metrics
```

### Alertas no llegan a Slack
```bash
# Ver logs de Alertmanager
docker-compose logs alertmanager | grep -i slack

# Test webhook manualmente
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test"}' \
  $SLACK_WEBHOOK_URL
```

Ver [MONITORING_SETUP.md - Troubleshooting](../docs/monitoring/MONITORING_SETUP.md#troubleshooting) para más detalles.

---

## 🔐 Seguridad

- Grafana protegido con usuario/contraseña
- Prometheus y Alertmanager en red interna
- Exporters solo accesibles desde Prometheus
- Secrets en `.env` (no commitear)

---

## 📊 Arquitectura

```
┌─────────────────────────────────────────────┐
│         BACKEND NETWORK                     │
│  ┌─────┐  ┌──────────┐  ┌───────┐         │
│  │ API │  │PostgreSQL│  │ Redis │          │
│  └──┬──┘  └────┬─────┘  └───┬───┘         │
└─────┼─────────┼────────────┼───────────────┘
      │         │            │
┌─────┼─────────┼────────────┼───────────────┐
│     │         │            │  MONITORING   │
│     ▼         ▼            ▼               │
│  ┌───────────────────────────────┐         │
│  │      PROMETHEUS (9090)        │         │
│  │   • Scrape 7 targets          │         │
│  │   • Eval 22 alert rules       │         │
│  └──────┬──────────────┬─────────┘         │
│         │              │                    │
│         ▼              ▼                    │
│  ┌─────────────┐  ┌─────────┐             │
│  │ALERTMANAGER │  │ GRAFANA │              │
│  │   (9093)    │  │ (3000)  │              │
│  │             │  │         │              │
│  │ → Slack     │  │ 3 Dashboards           │
│  │ → Email     │  └─────────┘              │
│  └─────────────┘                           │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │ EXPORTERS (4)                         │ │
│  │ • postgres-exporter (9187)            │ │
│  │ • redis-exporter (9121)               │ │
│  │ • node-exporter (9100)                │ │
│  │ • cadvisor (8080)                     │ │
│  └───────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

## 📈 Métricas Expuestas

### API (FastAPI)
- `http_requests_total` - Requests totales por método/path/status
- `http_request_duration_seconds` - Latencia por endpoint
- `process_open_fds` - Conexiones activas
- `process_resident_memory_bytes` - Memoria usada
- `ical_last_sync_timestamp` - Última sincronización iCal

### PostgreSQL
- `pg_up` - Estado de conexión
- `pg_stat_database_*` - Stats de base de datos
- `pg_locks_count` - Locks activos
- `pg_database_size_bytes` - Tamaño de DB

### Redis
- `redis_up` - Estado de conexión
- `redis_memory_*` - Uso de memoria
- `redis_keyspace_*` - Hits/misses
- `redis_connected_clients` - Clientes conectados

### Node (Host)
- `node_cpu_seconds_total` - CPU por modo
- `node_memory_*` - Memoria del sistema
- `node_disk_*` - I/O de disco
- `node_network_*` - Tráfico de red

### Containers
- `container_memory_usage_bytes` - Memoria por container
- `container_cpu_usage_seconds_total` - CPU por container
- `container_network_*` - Network por container

---

## 🔄 Mantenimiento

### Backup de métricas
```bash
# Crear snapshot de Prometheus
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot
```

### Actualizar versión
```bash
# Actualizar en docker-compose.yml
# image: prom/prometheus:v2.XX.0

docker-compose pull
docker-compose up -d
```

### Limpiar datos viejos
```bash
# Prometheus (ajustar retention)
# --storage.tsdb.retention.time=7d en docker-compose.yml

docker-compose up -d prometheus
```

---

## 📞 Soporte

- **Issues**: Reportar en repositorio GitHub
- **Alertas**: Ver [Alert Runbook](../docs/monitoring/ALERT_RUNBOOK.md)
- **Escalamiento**: Seguir procedimiento en runbook

---

## 📝 Licencia

Parte del Sistema de Alojamientos MVP - Uso interno
