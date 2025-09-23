import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Define custom metrics
const errorRate = new Rate('error_rate');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up
    { duration: '5m', target: 100 }, // Sustained load
    { duration: '2m', target: 200 }, // Peak load
    { duration: '5m', target: 200 }, // Sustained peak
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500'], // 95% of requests under 500ms
    'http_req_failed': ['rate<0.05'],   // Error rate under 5%
    'error_rate': ['rate<0.05'],
  },
};

const BASE_URL = 'http://localhost:8000';

export default function() {
  // Test scenarios
  const scenarios = [
    () => testHealthEndpoint(),
    () => testRunTests(),
    () => testGetResults(),
    () => testQualityGates(),
    () => testDashboardMetrics(),
  ];
  
  // Random scenario selection
  const scenario = scenarios[Math.floor(Math.random() * scenarios.length)];
  scenario();
  
  sleep(1);
}

function testHealthEndpoint() {
  const response = http.get(`${BASE_URL}/health`);
  
  const success = check(response, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  errorRate.add(!success);
}

function testRunTests() {
  const testTypes = ['unit', 'integration', 'performance'];
  const testType = testTypes[Math.floor(Math.random() * testTypes.length)];
  
  const response = http.post(`${BASE_URL}/tests/run/${testType}`);
  
  const success = check(response, {
    'run test status is 200': (r) => r.status === 200,
    'test started successfully': (r) => r.json('status') === 'started',
  });
  
  errorRate.add(!success);
}

function testGetResults() {
  const response = http.get(`${BASE_URL}/tests/results`);
  
  const success = check(response, {
    'get results status is 200': (r) => r.status === 200,
    'results response has data': (r) => r.json('total') >= 0,
  });
  
  errorRate.add(!success);
}

function testQualityGates() {
  const response = http.get(`${BASE_URL}/quality/gates`);
  
  const success = check(response, {
    'quality gates status is 200': (r) => r.status === 200,
    'gates response has gates': (r) => Array.isArray(r.json('gates')),
  });
  
  errorRate.add(!success);
}

function testDashboardMetrics() {
  const response = http.get(`${BASE_URL}/metrics/dashboard`);
  
  const success = check(response, {
    'dashboard status is 200': (r) => r.status === 200,
    'dashboard has metrics': (r) => r.json('metrics') !== null,
  });
  
  errorRate.add(!success);
}
