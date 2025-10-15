/**
 * k6 Load Test: Soak Test (Endurance Test)
 *
 * FASE 2 - P106: Load Testing
 * Escenario: Carga sostenida durante período extendido
 *
 * Perfil:
 * - 30 usuarios concurrentes
 * - Duración: 2 horas
 *
 * Objetivo:
 * - Detectar memory leaks
 * - Detectar degradación gradual de performance
 * - Validar estabilidad de conexiones (DB, Redis)
 * - Verificar cleanup de recursos
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend, Gauge } from 'k6/metrics';
import { randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const memoryUsage = new Gauge('memory_usage_mb');
const activeConnections = new Gauge('active_db_connections');
const cacheHitRate = new Rate('cache_hit_rate');
const performanceDegradation = new Trend('performance_degradation');

let baselineP95 = null;  // Se establece en primeros 10 minutos

export const options = {
  stages: [
    { duration: '2m', target: 30 },      // Ramp-up
    { duration: '116m', target: 30 },    // Soak: 1h56m
    { duration: '2m', target: 0 },       // Ramp-down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<3500'],          // Permite 15% degradación vs normal
    'http_req_failed': ['rate<0.01'],             // Error rate < 1%
    'performance_degradation': ['p(95)<1.15'],    // Max 15% degradación
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000/api/v1';

const accommodations = [1, 2, 3];
const guestNames = ['Soak User A', 'Soak User B', 'Soak User C', 'Soak User D'];
const phonePrefix = '+5491176543';

export default function () {
  const iterationStart = Date.now();

  // Mix realista de operaciones
  const rand = Math.random();

  if (rand < 0.4) {
    testAvailability();
  } else if (rand < 0.7) {
    testPreReservation();
  } else if (rand < 0.85) {
    testReservationsList();
  } else if (rand < 0.95) {
    testWhatsAppWebhook();
  } else {
    testHealthCheck();
  }

  // Think time realista
  sleep(randomIntBetween(2, 8));

  // Cada 100 iteraciones, hacer health check extensivo
  if (__ITER % 100 === 0) {
    checkSystemHealth();
  }
}

function testAvailability() {
  const accommodationId = randomItem(accommodations);
  const checkIn = getRandomFutureDate(7, 90);  // Hasta 3 meses
  const checkOut = addDays(checkIn, randomIntBetween(2, 7));

  const res = http.get(
    `${BASE_URL}/reservations/availability?accommodation_id=${accommodationId}&check_in=${checkIn}&check_out=${checkOut}`
  );

  check(res, {
    'soak availability ok': (r) => r.status === 200,
    'soak availability stable': (r) => r.timings.duration < 3000,
  });

  trackPerformanceDegradation(res.timings.duration);
}

function testPreReservation() {
  const accommodationId = randomItem(accommodations);
  const checkIn = getRandomFutureDate(7, 60);
  const checkOut = addDays(checkIn, randomIntBetween(2, 5));

  const payload = {
    accommodation_id: accommodationId,
    check_in: checkIn,
    check_out: checkOut,
    guests_count: randomIntBetween(1, 4),
    guest_name: randomItem(guestNames),
    guest_phone: `${phonePrefix}${randomIntBetween(100, 999)}`,
    guest_email: `soak${Date.now()}${randomIntBetween(100, 999)}@test.com`,
    channel_source: 'soak_test',
  };

  const res = http.post(
    `${BASE_URL}/reservations/prereserve`,
    JSON.stringify(payload),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );

  check(res, {
    'soak prereserve success': (r) => r.status === 200 || r.status === 409,
    'soak prereserve stable': (r) => r.timings.duration < 4000,
  });

  trackPerformanceDegradation(res.timings.duration);
}

function testReservationsList() {
  // Listar reservas (simula dashboard admin)
  const res = http.get(
    `${BASE_URL}/admin/reservations?limit=20&offset=0`,
    {
      headers: {
        'Authorization': 'Bearer fake_token',  // Mock auth
      },
    }
  );

  check(res, {
    'soak list stable': (r) => r.timings.duration < 2000,
  });

  trackPerformanceDegradation(res.timings.duration);
}

function testWhatsAppWebhook() {
  const messages = [
    'Hola, consulto disponibilidad',
    'Quiero reservar para el finde',
    '¿Cuánto sale la cabaña?',
    'Gracias!',
  ];

  const payload = {
    object: 'whatsapp_business_account',
    entry: [{
      id: 'soak_test',
      changes: [{
        value: {
          messaging_product: 'whatsapp',
          messages: [{
            from: `${phonePrefix}${randomIntBetween(100, 999)}`,
            id: `soak_${Date.now()}_${randomIntBetween(1000, 9999)}`,
            timestamp: Math.floor(Date.now() / 1000).toString(),
            type: 'text',
            text: {
              body: randomItem(messages),
            },
          }],
        },
      }],
    }],
  };

  const res = http.post(
    `${BASE_URL}/webhooks/whatsapp`,
    JSON.stringify(payload),
    {
      headers: {
        'Content-Type': 'application/json',
        'X-Hub-Signature-256': 'sha256=fake',
      },
    }
  );

  check(res, {
    'soak webhook stable': (r) => r.timings.duration < 5000,
  });
}

function testHealthCheck() {
  const res = http.get(`${BASE_URL}/healthz`);

  check(res, {
    'soak health ok': (r) => r.status === 200,
    'soak health fast': (r) => r.timings.duration < 500,
  });
}

function checkSystemHealth() {
  // Health check extensivo cada 100 iteraciones
  const res = http.get(`${BASE_URL}/healthz`);

  if (res.status === 200) {
    const health = JSON.parse(res.body);

    // Extraer métricas si están disponibles
    if (health.checks && health.checks.database) {
      const dbLatency = health.checks.database.latency_ms || 0;
      activeConnections.add(health.checks.database.pool_size || 0);
    }

    if (health.checks && health.checks.redis) {
      const redisMemory = health.checks.redis.used_memory_mb || 0;
      memoryUsage.add(redisMemory);

      // Cache hit rate si está disponible
      const hitRate = health.checks.redis.hit_rate || 0;
      cacheHitRate.add(hitRate > 0 ? 1 : 0);
    }
  }
}

function trackPerformanceDegradation(duration) {
  // Establecer baseline en primeros 10 minutos
  if (__VU === 1 && __ITER === 50 && !baselineP95) {
    baselineP95 = duration;
  }

  // Trackear degradación relativa al baseline
  if (baselineP95 && baselineP95 > 0) {
    const degradation = duration / baselineP95;
    performanceDegradation.add(degradation);
  }
}

// Helper functions
function getRandomFutureDate(minDays, maxDays) {
  const today = new Date();
  const futureDate = new Date(today);
  futureDate.setDate(today.getDate() + randomIntBetween(minDays, maxDays));
  return futureDate.toISOString().split('T')[0];
}

function addDays(dateStr, days) {
  const date = new Date(dateStr);
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
}

export function handleSummary(data) {
  const { metrics } = data;

  let summary = '\n=== SOAK TEST SUMMARY (2 HOURS) ===\n\n';

  summary += `Total Requests: ${metrics.http_reqs.values.count}\n`;
  summary += `Average Request Rate: ${metrics.http_reqs.values.rate.toFixed(2)} req/s\n`;
  summary += `Failed Requests: ${(metrics.http_req_failed.values.rate * 100).toFixed(2)}%\n\n`;

  summary += `Request Duration:\n`;
  summary += `  P50: ${metrics.http_req_duration.values['p(50)'].toFixed(2)}ms\n`;
  summary += `  P95: ${metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  summary += `  P99: ${metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n`;
  summary += `  Max: ${metrics.http_req_duration.values.max.toFixed(2)}ms\n\n`;

  // Performance degradation analysis
  if (metrics.performance_degradation) {
    const degradation = metrics.performance_degradation.values['p(95)'];
    const degradationPct = ((degradation - 1) * 100).toFixed(2);

    summary += `Performance Degradation:\n`;
    summary += `  P95 Degradation: ${degradationPct}% vs baseline\n`;
    summary += `  Status: ${Math.abs(degradation - 1) < 0.15 ? '✓ STABLE' : '✗ DEGRADED'}\n\n`;
  }

  // Resource metrics
  if (metrics.memory_usage_mb) {
    summary += `Resource Utilization:\n`;
    summary += `  Avg Memory (Redis): ${metrics.memory_usage_mb.values.avg.toFixed(2)} MB\n`;
    summary += `  Max Memory (Redis): ${metrics.memory_usage_mb.values.max.toFixed(2)} MB\n`;
  }

  if (metrics.active_db_connections) {
    summary += `  Avg DB Connections: ${metrics.active_db_connections.values.avg.toFixed(0)}\n`;
    summary += `  Max DB Connections: ${metrics.active_db_connections.values.max.toFixed(0)}\n\n`;
  }

  // Soak test pass criteria
  summary += `Soak Test Criteria:\n`;
  summary += `  P95 < 3.5s: ${metrics.http_req_duration.values['p(95)'] < 3500 ? '✓ PASS' : '✗ FAIL'}\n`;
  summary += `  Error rate < 1%: ${metrics.http_req_failed.values.rate < 0.01 ? '✓ PASS' : '✗ FAIL'}\n`;

  if (metrics.performance_degradation) {
    const degradation = metrics.performance_degradation.values['p(95)'];
    summary += `  Degradation < 15%: ${degradation < 1.15 ? '✓ PASS' : '✗ FAIL'}\n`;
  }

  summary += `\n⚠️  Note: Revisa logs del servidor para memory leaks o connection leaks\n`;
  summary += `    Comando: docker-compose logs backend | grep -i "memory\\|leak\\|connection"\n`;

  return {
    'stdout': summary,
    'soak-test-results.json': JSON.stringify(data),
  };
}
