/**
 * k6 Load Test: Spike Test
 *
 * FASE 2 - P106: Load Testing
 * Escenario: Picos súbitos de tráfico
 *
 * Perfil:
 * - Baseline: 50 usuarios
 * - Spike: 200 usuarios (4x)
 * - Duración del spike: 3 minutos
 *
 * Objetivo:
 * - Validar que sistema maneja picos súbitos
 * - Error rate debe mantenerse < 5% durante spike
 * - Sistema debe recuperarse rápidamente
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const spikeErrorRate = new Rate('spike_errors');
const recoveryTime = new Trend('recovery_time');
const lockContentionRate = new Rate('lock_contention');

export const options = {
  stages: [
    { duration: '1m', target: 50 },     // Warm-up
    { duration: '30s', target: 200 },   // Spike rápido a 4x
    { duration: '3m', target: 200 },    // Mantener spike
    { duration: '30s', target: 50 },    // Bajar rápido
    { duration: '2m', target: 50 },     // Recuperación
    { duration: '30s', target: 0 },     // Ramp-down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<5000'],  // Más laxo durante spike
    'http_req_failed': ['rate<0.05'],     // Max 5% error rate
    'spike_errors': ['rate<0.05'],
    'lock_contention': ['rate<0.3'],      // Max 30% lock contention esperado
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000/api/v1';

const accommodations = [1, 2, 3];
const guestNames = ['Spike User 1', 'Spike User 2', 'Spike User 3'];
const phonePrefix = '+5491187654';

export default function () {
  // Durante spike, enfocar en operaciones críticas
  const rand = Math.random();

  if (rand < 0.6) {
    // 60% pre-reservas (operación crítica)
    testConcurrentPreReservation();
  } else if (rand < 0.9) {
    // 30% consultas de disponibilidad
    testAvailability();
  } else {
    // 10% health checks
    testHealthCheck();
  }

  // Menor think time para simular tráfico intenso
  sleep(randomIntBetween(0.5, 2));
}

function testConcurrentPreReservation() {
  // Usar mismas fechas intencionalmente para forzar lock contention
  const accommodationId = randomItem(accommodations);
  const checkIn = getPopularDate();  // Fecha "popular"
  const checkOut = addDays(checkIn, 3);

  const payload = {
    accommodation_id: accommodationId,
    check_in: checkIn,
    check_out: checkOut,
    guests_count: randomIntBetween(2, 4),
    guest_name: randomItem(guestNames),
    guest_phone: `${phonePrefix}${randomIntBetween(100, 999)}`,
    guest_email: `spike${randomIntBetween(1000, 9999)}@test.com`,
    channel_source: 'spike_test',
  };

  const res = http.post(
    `${BASE_URL}/reservations/prereserve`,
    JSON.stringify(payload),
    {
      headers: { 'Content-Type': 'application/json' },
      timeout: '10s',
    }
  );

  const success = check(res, {
    'spike prereserve not 500': (r) => r.status !== 500,
    'spike prereserve response < 10s': (r) => r.timings.duration < 10000,
  });

  // Trackear lock contention (409 = date overlap)
  if (res.status === 409) {
    lockContentionRate.add(1);
  } else if (res.status === 423) {
    // 423 Locked = lock acquisition failed
    lockContentionRate.add(1);
  } else {
    lockContentionRate.add(0);
  }

  // Errores reales (no contention)
  if (res.status >= 500 || res.status === 0) {
    spikeErrorRate.add(1);
  } else {
    spikeErrorRate.add(0);
  }
}

function testAvailability() {
  const accommodationId = randomItem(accommodations);
  const checkIn = getPopularDate();
  const checkOut = addDays(checkIn, randomIntBetween(2, 5));

  const res = http.get(
    `${BASE_URL}/reservations/availability?accommodation_id=${accommodationId}&check_in=${checkIn}&check_out=${checkOut}`,
    { timeout: '5s' }
  );

  const success = check(res, {
    'spike availability status ok': (r) => r.status === 200,
    'spike availability response < 5s': (r) => r.timings.duration < 5000,
  });

  if (!success) {
    spikeErrorRate.add(1);
  }
}

function testHealthCheck() {
  const res = http.get(`${BASE_URL}/healthz`, { timeout: '2s' });

  const success = check(res, {
    'spike health check ok': (r) => r.status === 200,
  });

  if (!success) {
    spikeErrorRate.add(1);
  }
}

// Helper: Retornar fechas "populares" para forzar contention
function getPopularDate() {
  const popularDates = [
    addDaysFromNow(14),  // 2 semanas
    addDaysFromNow(21),  // 3 semanas
    addDaysFromNow(28),  // 4 semanas
  ];

  return randomItem(popularDates);
}

function addDaysFromNow(days) {
  const today = new Date();
  today.setDate(today.getDate() + days);
  return today.toISOString().split('T')[0];
}

function addDays(dateStr, days) {
  const date = new Date(dateStr);
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
}

export function handleSummary(data) {
  const { metrics } = data;

  let summary = '\n=== SPIKE TEST SUMMARY ===\n\n';

  summary += `Total Requests: ${metrics.http_reqs.values.count}\n`;
  summary += `Peak Request Rate: ${metrics.http_reqs.values.rate.toFixed(2)} req/s\n`;
  summary += `Failed Requests: ${(metrics.http_req_failed.values.rate * 100).toFixed(2)}%\n\n`;

  summary += `Request Duration:\n`;
  summary += `  P50: ${metrics.http_req_duration.values['p(50)'].toFixed(2)}ms\n`;
  summary += `  P95: ${metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  summary += `  P99: ${metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n`;
  summary += `  Max: ${metrics.http_req_duration.values.max.toFixed(2)}ms\n\n`;

  if (metrics.lock_contention) {
    summary += `Lock Contention Rate: ${(metrics.lock_contention.values.rate * 100).toFixed(2)}%\n`;
  }

  summary += `\nSpike Resilience:\n`;
  summary += `  P95 < 5s: ${metrics.http_req_duration.values['p(95)'] < 5000 ? '✓ PASS' : '✗ FAIL'}\n`;
  summary += `  Error rate < 5%: ${metrics.http_req_failed.values.rate < 0.05 ? '✓ PASS' : '✗ FAIL'}\n`;
  summary += `  Lock contention < 30%: ${metrics.lock_contention ? (metrics.lock_contention.values.rate < 0.3 ? '✓ PASS' : '✗ FAIL') : 'N/A'}\n`;

  return {
    'stdout': summary,
    'spike-test-results.json': JSON.stringify(data),
  };
}
