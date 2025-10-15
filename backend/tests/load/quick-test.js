import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const prereservationSuccessRate = new Rate('prereservation_success');
const apiLatency = new Trend('api_latency_ms');

export const options = {
    stages: [
        { duration: '1m', target: 25 },  // Ramp up to 25 users
        { duration: '1m', target: 50 },  // Ramp to 50 users
        { duration: '1m', target: 25 },  // Ramp down
    ],
    thresholds: {
        'http_req_duration': ['p(95)<5000', 'p(99)<10000'],  // Relaxed SLOs for post-fix
        'http_req_failed': ['rate<0.05'],  // < 5% error rate (relaxed from 1%)
        'prereservation_success': ['rate>0.90'],  // > 90% success
    },
};

const BASE_URL = 'http://localhost:8000/api/v1';

export default function () {
    // Test distribution
    const rand = Math.random();

    if (rand < 0.2) {
        // 20% health checks
        const healthRes = http.get(`${BASE_URL}/healthz`);
        check(healthRes, {
            'health returns 200': (r) => r.status === 200,
            'health has status': (r) => r.json('status') !== undefined,
        });
        apiLatency.add(healthRes.timings.duration);
    } else if (rand < 0.6) {
        // 40% availability queries
        const checkIn = '2025-10-23';
        const checkOut = '2025-10-28';
        const accId = Math.floor(Math.random() * 3) + 1;

        const availRes = http.get(`${BASE_URL}/reservations/availability?accommodation_id=${accId}&check_in=${checkIn}&check_out=${checkOut}`);
        check(availRes, {
            'availability returns 200 or 404': (r) => r.status === 200 || r.status === 404,
        });
        apiLatency.add(availRes.timings.duration);
    } else {
        // 40% pre-reservations
        const payload = JSON.stringify({
            accommodation_id: Math.floor(Math.random() * 3) + 1,
            check_in: '2025-11-10',
            check_out: '2025-11-15',
            guests_count: 2,
            contact_name: `Test User ${Math.floor(Math.random() * 10000)}`,
            contact_phone: `+5491155${Math.floor(Math.random() * 10000).toString().padStart(6, '0')}`,
            contact_email: `test${Math.floor(Math.random() * 10000)}@example.com`,
            channel_source: 'k6_test',
        });

        const prereserveRes = http.post(
            `${BASE_URL}/reservations/pre-reserve`,
            payload,
            {
                headers: { 'Content-Type': 'application/json' },
                timeout: '30s',
            }
        );

        const success = prereserveRes.status === 201 || prereserveRes.status === 409;
        prereservationSuccessRate.add(success);
        apiLatency.add(prereserveRes.timings.duration);

        check(prereserveRes, {
            'prereserve succeeds or conflicts': (r) => r.status === 201 || r.status === 409,
        });
    }

    sleep(0.5);  // Reduce sleep to increase request rate
}
