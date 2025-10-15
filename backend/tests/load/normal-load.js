/**
 * k6 Load Test: Normal Load
 *
 * FASE 2 - P106: Load Testing
 * Escenario: Carga normal del sistema
 *
 * Perfil:
 * - 50 usuarios concurrentes
 * - Duración: 10 minutos
 * - Ramp-up: 1 minuto
 *
 * SLOs a validar:
 * - P95 < 3s para endpoints de texto
 * - P95 < 15s para audio
 * - P99 < 6s para texto
 * - P99 < 30s para audio
 * - Error rate < 1%
 * - Disponibilidad > 99.5%
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const prereservationSuccess = new Counter('prereservation_success');
const prereservationFailed = new Counter('prereservation_failed');
const errorRate = new Rate('errors');

// Configuración de test
export const options = {
  stages: [
    { duration: '1m', target: 50 },   // Ramp-up a 50 usuarios
    { duration: '8m', target: 50 },   // Mantener 50 usuarios
    { duration: '1m', target: 0 },    // Ramp-down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<3000', 'p(99)<6000'],  // 95% < 3s, 99% < 6s
    'http_req_failed': ['rate<0.01'],                    // Error rate < 1%
    'errors': ['rate<0.01'],
    'checks': ['rate>0.99'],                             // 99% de checks pasando
  },
};

// Base URL (configurable vía env)
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000/api/v1';

// Test data
const accommodations = [1, 2, 3];  // IDs de alojamientos de test
const guestNames = ['Juan Pérez', 'María González', 'Carlos Rodríguez', 'Ana Martínez'];
const phonePrefix = '+5491123456';

export default function () {
  // Scenario 1: Health check (30% de requests)
  if (Math.random() < 0.3) {
    testHealthCheck();
  }

  // Scenario 2: List accommodations (30% de requests)
  else if (Math.random() < 0.6) {
    testListAccommodations();
  }

  // Scenario 3: Pre-reserva (40% de requests) - endpoint crítico
  else {
    testPreReservation();
  }

  // Think time entre requests
  sleep(randomIntBetween(1, 3));
}

function testHealthCheck() {
  const res = http.get(`${BASE_URL}/healthz`);

  const success = check(res, {
    'health check status 200': (r) => r.status === 200,
    'health check has status field': (r) => {
      try {
        return JSON.parse(r.body).status !== undefined;
      } catch (e) {
        return false;
      }
    },
    'health check response time < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(!success);
}

function testListAccommodations() {
  const res = http.get(`${BASE_URL}/reservations/accommodations`);

  const success = check(res, {
    'accommodations status 200': (r) => r.status === 200,
    'accommodations has data': (r) => {
      try {
        const data = JSON.parse(r.body);
        return Array.isArray(data) && data.length > 0;
      } catch (e) {
        return false;
      }
    },
    'accommodations response time < 1s': (r) => r.timings.duration < 1000,
  });

  errorRate.add(!success);
}

function testPreReservation() {
  const accommodationId = randomItem(accommodations);
  const checkIn = getRandomFutureDate(7, 30);
  const checkOut = addDays(checkIn, randomIntBetween(2, 5));
  const guests = randomIntBetween(1, 4);
  const guestName = randomItem(guestNames);
  const phone = `${phonePrefix}${randomIntBetween(100, 999)}`;

  const payload = {
    accommodation_id: accommodationId,
    check_in: checkIn,
    check_out: checkOut,
    guests: guests,  // Corregido: era guests_count
    contact_name: guestName,  // Corregido: era guest_name
    contact_phone: phone,  // Corregido: era guest_phone
    contact_email: `test${randomIntBetween(1000, 9999)}@example.com`,  // Corregido: era guest_email
    channel: 'load_test',  // Corregido: era channel_source
  };

  const res = http.post(
    `${BASE_URL}/reservations/pre-reserve`,
    JSON.stringify(payload),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );

  const success = check(res, {
    'prereserve status 200 or 409': (r) => r.status === 200 || r.status === 409,
    'prereserve has reservation_code': (r) => {
      if (r.status !== 200) return true;  // Conflict esperado bajo carga
      try {
        const data = JSON.parse(r.body);
        return data.code !== undefined || data.reservation_code !== undefined;
      } catch (e) {
        return false;
      }
    },
    'prereserve response time < 3s': (r) => r.timings.duration < 3000,
  });

  if (res.status === 200) {
    prereservationSuccess.add(1);
  } else if (res.status === 409) {
    // Date overlap esperado bajo carga concurrente
    prereservationSuccess.add(1);  // No es error
  } else {
    prereservationFailed.add(1);
  }

  errorRate.add(!success);
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
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'normal-load-results.json': JSON.stringify(data),
  };
}

function textSummary(data, options) {
  // Custom summary
  const { metrics } = data;

  let summary = '\n=== NORMAL LOAD TEST SUMMARY ===\n\n';

  // Request metrics
  summary += `Total Requests: ${metrics.http_reqs.values.count}\n`;
  summary += `Request Rate: ${metrics.http_reqs.values.rate.toFixed(2)} req/s\n`;
  summary += `Failed Requests: ${metrics.http_req_failed.values.rate.toFixed(4)} (${(metrics.http_req_failed.values.rate * 100).toFixed(2)}%)\n\n`;

  // Duration metrics
  summary += `Request Duration:\n`;
  summary += `  P50: ${metrics.http_req_duration.values['p(50)'].toFixed(2)}ms\n`;
  summary += `  P95: ${metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  summary += `  P99: ${metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n`;
  summary += `  Max: ${metrics.http_req_duration.values.max.toFixed(2)}ms\n\n`;

  // Custom metrics
  if (metrics.prereservation_success) {
    summary += `Pre-reservations:\n`;
    summary += `  Success: ${metrics.prereservation_success.values.count}\n`;
    summary += `  Failed: ${metrics.prereservation_failed ? metrics.prereservation_failed.values.count : 0}\n\n`;
  }

  // SLO compliance
  summary += `SLO Compliance:\n`;
  summary += `  P95 < 3s: ${metrics.http_req_duration.values['p(95)'] < 3000 ? '✓ PASS' : '✗ FAIL'}\n`;
  summary += `  P99 < 6s: ${metrics.http_req_duration.values['p(99)'] < 6000 ? '✓ PASS' : '✗ FAIL'}\n`;
  summary += `  Error rate < 1%: ${metrics.http_req_failed.values.rate < 0.01 ? '✓ PASS' : '✗ FAIL'}\n`;

  return summary;
}
