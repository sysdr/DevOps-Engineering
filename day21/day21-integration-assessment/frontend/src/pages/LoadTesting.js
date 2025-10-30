import React, { useState } from 'react';

const LoadTesting = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState('');

  const runLoadTest = async () => {
    setIsRunning(true);
    setError('');
    setMetrics(null);
    try {
      const apiBase = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
      const res = await fetch(`${apiBase}/api/load-tests/run`, {
        method: 'POST',
        headers: { 'Accept': 'application/json' }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMetrics(data.metrics || null);
    } catch (e) {
      setError(`Failed to run load test: ${e.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="load-testing">
      <h1>Load Testing Dashboard</h1>
      <p>Performance testing with realistic traffic patterns</p>

      <button className={`run-tests-btn ${isRunning ? 'running' : ''}`} onClick={runLoadTest} disabled={isRunning}>
        {isRunning ? 'Running...' : 'Run Load Test'}
      </button>

      {error && <p style={{ color: 'red', marginTop: 12 }}>{error}</p>}

      {metrics && (
        <div className="summary-card" style={{ marginTop: 16 }}>
          <h3>Results</h3>
          <ul>
            <li>Total Requests: {metrics.total_requests}</li>
            <li>Successful: {metrics.successful_requests}</li>
            <li>Failed: {metrics.failed_requests}</li>
            <li>Avg Response Time: {metrics.average_response_time} ms</li>
            <li>P95: {metrics.p95_response_time} ms</li>
            <li>P99: {metrics.p99_response_time} ms</li>
            <li>RPS: {metrics.requests_per_second}</li>
            <li>Error Rate: {metrics.error_rate}</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default LoadTesting;
