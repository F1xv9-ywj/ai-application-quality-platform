import http from 'k6/http';
import { check } from 'k6';

export const options = { vus: 5, duration: '20s', thresholds: { http_req_failed: ['rate<0.01'], http_req_duration: ['p(95)<500'], checks: ['rate>0.99'] } };
export default function () {
  const response = http.post(`${__ENV.BASE_URL || 'http://localhost:8000'}/api/chat`, JSON.stringify({ question: '退款期限是多久？', top_k: 3 }), { headers: { 'Content-Type': 'application/json' } });
  check(response, { 'status 200': r => r.status === 200, 'has citations': r => JSON.parse(r.body).citations.length > 0 });
}
