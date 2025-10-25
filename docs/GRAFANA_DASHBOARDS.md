# Dashboards Grafana para Retry Logic y Circuit Breaker

Guía para crear dashboards de observabilidad para el sistema de retry y circuit breaker del MVP de reservas.

## 📊 Dashboard 1: Retry Logic Overview

### Panel 1: Rate de Reintentos por Operación
**Tipo:** Time Series
**Query:**
```promql
rate(retry_attempts_total{result="retry"}[5m])
```
**Descripción:** Muestra la tasa de reintentos por segundo para cada operación.
**Alertas sugeridas:**
- Warning: rate > 0.1 (más de 6 reintentos/minuto)
- Critical: rate > 0.5 (más de 30 reintentos/minuto)

### Panel 2: Tasa de Éxito Eventual
**Tipo:** Gauge
**Query:**
```promql
sum(rate(retry_attempts_total{result="success"}[5m])) /
sum(rate(retry_attempts_total[5m])) * 100
```
**Descripción:** Porcentaje de operaciones que eventualmente tienen éxito (incluye éxito después de retry).
**Umbrales:**
- Verde: > 95%
- Amarillo: 90-95%
- Rojo: < 90%

### Panel 3: Distribución de Número de Intentos
**Tipo:** Bar Chart
**Query:**
```promql
sum by (attempt_number) (increase(retry_attempts_total{result="success"}[1h]))
```
**Descripción:** Muestra cuántas operaciones tuvieron éxito en el intento 1, 2, 3, etc.

### Panel 4: P50/P95/P99 de Delays de Retry
**Tipo:** Time Series
**Queries:**
```promql
# P50
histogram_quantile(0.50, rate(retry_delay_seconds_bucket[5m]))

# P95
histogram_quantile(0.95, rate(retry_delay_seconds_bucket[5m]))

# P99
histogram_quantile(0.99, rate(retry_delay_seconds_bucket[5m]))
```
**Descripción:** Percentiles de delays entre reintentos. Útil para optimizar backoff.

### Panel 5: Operaciones con Retry Agotado
**Tipo:** Table
**Query:**
```promql
topk(10, increase(retry_exhausted_total[1h]))
```
**Descripción:** Top 10 operaciones que agotaron todos los intentos de retry.
**Alerta:** Si > 5 por hora → investigar

### Panel 6: Fallos Permanentes vs Transitorios
**Tipo:** Pie Chart
**Query:**
```promql
# Permanentes
sum(increase(retry_attempts_total{result="failed_permanent"}[1h]))

# Transitorios que eventualmente tuvieron éxito
sum(increase(retry_attempts_total{result="retry"}[1h]))
```
**Descripción:** Proporción de errores permanentes vs transitorios.

### Panel 7: Timeline de Eventos de Retry (por operación)
**Tipo:** Heatmap
**Query:**
```promql
sum by (operation) (rate(retry_attempts_total{result="retry"}[1m]))
```
**Descripción:** Heatmap temporal mostrando cuándo cada operación está reintentando.

---

## 🔌 Dashboard 2: Circuit Breaker Status

### Panel 1: Estado Actual de Circuit Breakers
**Tipo:** Stat
**Query:**
```promql
circuit_breaker_state
```
**Descripción:** Estado actual de cada circuit breaker (0=CLOSED, 1=OPEN, 2=HALF_OPEN).
**Colores:**
- Verde (0): Normal, requests pasan
- Rojo (1): Circuit abierto, servicio caído
- Amarillo (2): Probando recuperación

### Panel 2: Historial de Cambios de Estado
**Tipo:** Time Series (Staircase)
**Query:**
```promql
circuit_breaker_state
```
**Descripción:** Visualización temporal de transiciones de estado.

### Panel 3: Rate de Fallos por Circuit
**Tipo:** Time Series
**Query:**
```promql
rate(circuit_breaker_failures_total[5m])
```
**Descripción:** Tasa de fallos detectados por cada circuit breaker.

### Panel 4: Rate de Requests Rechazados
**Tipo:** Time Series
**Query:**
```promql
rate(circuit_breaker_rejections_total[5m])
```
**Descripción:** Requests rechazados por circuit breaker OPEN.
**Alerta:** Si > 0 → notificar DevOps

### Panel 5: Transiciones de Estado (Contador)
**Tipo:** Table
**Query:**
```promql
sum by (circuit_name, from_state, to_state) (
  increase(circuit_breaker_state_changes_total[1h])
)
```
**Descripción:** Tabla de transiciones de estado en la última hora.

### Panel 6: Ratio de Éxito por Circuit
**Tipo:** Gauge (por circuit)
**Query:**
```promql
sum by (circuit_name) (rate(circuit_breaker_successes_total[5m])) /
(sum by (circuit_name) (rate(circuit_breaker_successes_total[5m])) +
 sum by (circuit_name) (rate(circuit_breaker_failures_total[5m]))) * 100
```
**Descripción:** Porcentaje de éxito de cada circuit breaker.
**Umbrales:**
- Verde: > 95%
- Amarillo: 90-95%
- Rojo: < 90%

---

## 🎯 Dashboard 3: WhatsApp & MercadoPago APIs

### Panel 1: WhatsApp API Health
**Tipo:** Time Series
**Queries:**
```promql
# Rate de éxito
rate(retry_attempts_total{operation=~"whatsapp.*", result="success"}[5m])

# Rate de retry
rate(retry_attempts_total{operation=~"whatsapp.*", result="retry"}[5m])

# Rate de fallo permanente
rate(retry_attempts_total{operation=~"whatsapp.*", result="failed_permanent"}[5m])
```
**Descripción:** Health overview de WhatsApp API.

### Panel 2: MercadoPago API Health
**Tipo:** Time Series
**Queries:**
```promql
# Rate de éxito
rate(retry_attempts_total{operation=~"mercadopago.*", result="success"}[5m])

# Rate de retry
rate(retry_attempts_total{operation=~"mercadopago.*", result="retry"}[5m])
```
**Descripción:** Health overview de MercadoPago API.

### Panel 3: Notificaciones de Pago (Retry Breakdown)
**Tipo:** Bar Chart
**Query:**
```promql
sum by (attempt_number) (
  increase(retry_attempts_total{operation="whatsapp_payment_notification"}[1h])
)
```
**Descripción:** Distribución de intentos para notificaciones de pago.

### Panel 4: Delays de Retry - WhatsApp
**Tipo:** Histogram
**Query:**
```promql
histogram_quantile(0.95,
  rate(retry_delay_seconds_bucket{operation=~"whatsapp.*"}[5m])
)
```
**Descripción:** P95 de delays en operaciones WhatsApp.

### Panel 5: Delays de Retry - MercadoPago
**Tipo:** Histogram
**Query:**
```promql
histogram_quantile(0.95,
  rate(retry_delay_seconds_bucket{operation=~"mercadopago.*"}[5m])
)
```
**Descripción:** P95 de delays en operaciones MercadoPago.

### Panel 6: Rate Limits Detectados (429s)
**Tipo:** Counter
**Query:**
```promql
increase(retry_attempts_total{result="retry"}[5m])
```
**Descripción:** Detecta cuando se están alcanzando rate limits de APIs externas.
**Alerta:** Si > 10 por 5min → posible throttling

---

## 🚨 Alertas Sugeridas (Prometheus Alerts)

### Alert 1: High Retry Rate
```yaml
- alert: HighRetryRate
  expr: rate(retry_attempts_total{result="retry"}[5m]) > 0.5
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Alta tasa de reintentos en {{ $labels.operation }}"
    description: "Operación {{ $labels.operation }} está reintentando más de 30 veces por minuto"
```

### Alert 2: Circuit Breaker Open
```yaml
- alert: CircuitBreakerOpen
  expr: circuit_breaker_state == 1
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Circuit breaker {{ $labels.circuit_name }} está ABIERTO"
    description: "El servicio {{ $labels.circuit_name }} está caído"
```

### Alert 3: Retry Exhaustion Rate High
```yaml
- alert: HighRetryExhaustion
  expr: rate(retry_exhausted_total[5m]) > 0.1
  for: 10m
  labels:
    severity: critical
  annotations:
    summary: "Alta tasa de exhaustion en {{ $labels.operation }}"
    description: "Operaciones agotando todos los intentos de retry"
```

### Alert 4: WhatsApp API Degraded
```yaml
- alert: WhatsAppAPIDegraded
  expr: |
    (sum(rate(retry_attempts_total{operation=~"whatsapp.*", result="success"}[5m])) /
     sum(rate(retry_attempts_total{operation=~"whatsapp.*"}[5m])) * 100) < 90
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "WhatsApp API con baja tasa de éxito"
    description: "Solo {{ $value }}% de éxito en últimos 5min"
```

### Alert 5: MercadoPago API Rate Limited
```yaml
- alert: MercadoPagoRateLimited
  expr: rate(retry_attempts_total{operation=~"mercadopago.*", result="retry"}[5m]) > 0.2
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "MercadoPago API posiblemente rate-limited"
    description: "Alta tasa de reintentos detectada"
```

---

## 📋 Variables de Template Recomendadas

Para hacer los dashboards más flexibles, definir estas variables:

```
# Variable: operation
Query: label_values(retry_attempts_total, operation)
Type: Multi-select
Refresh: On Dashboard Load

# Variable: circuit_name
Query: label_values(circuit_breaker_state, circuit_name)
Type: Multi-select
Refresh: On Dashboard Load

# Variable: time_range
Type: Interval
Options: 5m, 15m, 1h, 6h, 24h, 7d
Default: 1h

# Variable: percentile
Type: Custom
Options: 0.50, 0.95, 0.99
Default: 0.95
```

---

## 🎨 Layout Sugerido

### Dashboard 1 (Retry Overview):
```
+------------------+------------------+
|  Rate Reintentos | Tasa Éxito (%)  |
|   (time series)  |     (gauge)     |
+------------------+------------------+
| Distribución Intentos (bar chart)  |
+-------------------------------------+
|   P50/P95/P99 Delays (time series) |
+-------------------------------------+
|  Retry Agotado   | Permanentes vs  |
|      (table)     |  Transitorios   |
+------------------+------------------+
```

### Dashboard 2 (Circuit Breaker):
```
+------------------+------------------+
| Estados Actuales | Historial       |
|      (stat)      | (time series)   |
+------------------+------------------+
|  Rate Fallos     | Rate Rechazos   |
| (time series)    | (time series)   |
+------------------+------------------+
| Transiciones (table) | Ratio Éxito  |
|                      |   (gauge)    |
+----------------------+--------------+
```

### Dashboard 3 (APIs Específicas):
```
+------------------+------------------+
| WhatsApp Health  | MercadoPago     |
| (time series)    | Health          |
+------------------+------------------+
| Notif. Pago      | Delays WhatsApp |
| (bar chart)      | (histogram)     |
+------------------+------------------+
| Delays MP        | Rate Limits     |
| (histogram)      | (counter)       |
+------------------+------------------+
```

---

## 🔧 Configuración de Prometheus

Asegurar que Prometheus esté scrappeando las métricas:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'sistema_cabanas'
    scrape_interval: 15s
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

---

## 📖 Interpretación de Métricas

### Retry Attempts Total
- `result="success"`: Operación exitosa (puede ser en 1er intento o después de retry)
- `result="retry"`: Intento fallido que será reintentado
- `result="failed_permanent"`: Error permanente, no se reintenta

### Circuit Breaker State
- `0` (CLOSED): Normal, requests pasan sin restricción
- `1` (OPEN): Circuit abierto, servicio caído, requests rechazados
- `2` (HALF_OPEN): Probando recuperación, permite requests limitados

### Delays de Retry
- Buckets: [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0] segundos
- Exponential backoff esperado: 1s → 2s → 4s → 8s
- Si delays > 16s frecuentemente → considerar aumentar failure_threshold

---

## 🎯 Casos de Uso de Monitoreo

### Caso 1: WhatsApp API Rate Limited
**Síntomas:**
- `retry_attempts_total{operation="whatsapp_send_text", result="retry"}` alto
- Delays concentrados en 1-2 segundos

**Acción:**
- Aumentar base_delay en retry config
- Considerar implementar queue para mensajes

### Caso 2: MercadoPago API Intermitente
**Síntomas:**
- `circuit_breaker_state{circuit_name="mercadopago"}` oscilando entre 0 y 1
- Transiciones CLOSED → OPEN → HALF_OPEN frecuentes

**Acción:**
- Aumentar failure_threshold en circuit breaker
- Verificar conectividad de red

### Caso 3: Notificaciones de Pago Fallando
**Síntomas:**
- `retry_exhausted_total{operation="whatsapp_payment_notification"}` > 0
- Alta proporción de `failed_permanent`

**Acción:**
- Revisar logs de errores permanentes (4xx)
- Verificar formato de números de teléfono
- Validar WhatsApp access token

---

## 📚 Referencias

- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)
- [Circuit Breaker Pattern - Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html)
