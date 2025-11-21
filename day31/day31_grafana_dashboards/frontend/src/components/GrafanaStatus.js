import React, { useState, useEffect } from 'react';

function GrafanaStatus() {
  const [status, setStatus] = useState(null);
  const [dashboardCount, setDashboardCount] = useState(0);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const [statusRes, dashRes] = await Promise.all([
        fetch('http://localhost:8001/api/grafana/status'),
        fetch('http://localhost:8001/api/dashboards')
      ]);

      const statusData = await statusRes.json();
      const dashData = await dashRes.json();

      setStatus(statusData);
      setDashboardCount(dashData.count || 0);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  return (
    <div className="status-page">
      <h2>System Status</h2>
      
      <div className="status-grid">
        <div className="status-card">
          <h3>Grafana Server</h3>
          <div className={`status-indicator ${status?.database === 'ok' ? 'healthy' : 'unhealthy'}`}>
            {status?.database === 'ok' ? '✓ Healthy' : '✗ Unavailable'}
          </div>
          <p>Database: {status?.database || 'Unknown'}</p>
          <p>Version: {status?.version || 'N/A'}</p>
        </div>

        <div className="status-card">
          <h3>Dashboard Count</h3>
          <div className="big-number">{dashboardCount}</div>
          <p>Active dashboards provisioned</p>
        </div>

        <div className="status-card">
          <h3>Metrics Service</h3>
          <div className="status-indicator healthy">✓ Running</div>
          <p>Port: 8000</p>
          <p>Endpoint: /metrics</p>
        </div>

        <div className="status-card">
          <h3>Management API</h3>
          <div className="status-indicator healthy">✓ Running</div>
          <p>Port: 8001</p>
          <p>Docs: /docs</p>
        </div>
      </div>

      <div className="quick-links">
        <h3>Quick Links</h3>
        <a href="http://localhost:3000" target="_blank" rel="noopener noreferrer" className="link-btn">
          Open Grafana UI
        </a>
        <a href="http://localhost:8000/metrics" target="_blank" rel="noopener noreferrer" className="link-btn">
          View Raw Metrics
        </a>
        <a href="http://localhost:8001/docs" target="_blank" rel="noopener noreferrer" className="link-btn">
          API Documentation
        </a>
      </div>
    </div>
  );
}

export default GrafanaStatus;
