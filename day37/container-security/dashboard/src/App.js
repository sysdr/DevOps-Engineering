import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [scanStats, setScanStats] = useState({ total: 0, vulnerable: 0, clean: 0 });
  const [runtimeStats, setRuntimeStats] = useState({ critical: 0, high: 0, warning: 0, info: 0 });
  const [admissionStats, setAdmissionStats] = useState({ allowed: 0, rejected: 0, total: 0 });
  const [benchmarkScore, setBenchmarkScore] = useState(0);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [recentScans, setRecentScans] = useState([]);
  const [recentDecisions, setRecentDecisions] = useState([]);
  const [ws, setWs] = useState(null);
  const [scanLoading, setScanLoading] = useState(false);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [actionStatus, setActionStatus] = useState('');

  const API_HOST = window.location.hostname || 'localhost';
  const API_PROTOCOL = window.location.protocol === 'https:' ? 'https' : 'http';
  const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const API_BASE = `${API_PROTOCOL}://${API_HOST}`;

  useEffect(() => {
    // Fetch initial data
    fetchDashboardData();

    // Setup resilient WebSocket for real-time alerts
    let websocket;
    let reconnectTimer;

    const connectWebSocket = () => {
      const wsUrl = `${WS_PROTOCOL}://${API_HOST}:8002/ws/alerts`;
      websocket = new WebSocket(wsUrl);

      websocket.onopen = () => {
        setWs(websocket);
      };
      
      websocket.onmessage = (event) => {
        const alert = JSON.parse(event.data);
        setRecentAlerts(prev => [alert, ...prev.slice(0, 9)]);
        
        // Update stats
        setRuntimeStats(prev => ({
          ...prev,
          [alert.severity.toLowerCase()]: (prev[alert.severity.toLowerCase()] || 0) + 1
        }));
      };

      websocket.onerror = () => {
        websocket.close();
      };

      websocket.onclose = () => {
        setWs(null);
        reconnectTimer = setTimeout(connectWebSocket, 2000);
      };
    };

    connectWebSocket();

    // Polling for other stats
    const interval = setInterval(fetchDashboardData, 10000);

    return () => {
      if (websocket) websocket.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
      clearInterval(interval);
    };
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch scan statistics
      const scansRes = await fetch(`${API_BASE}:8001/scans`);
      const scansData = await scansRes.json();
      const scans = scansData.scans || [];
      
      const vulnerable = scans.filter(s => s.critical > 0 || s.high > 0).length;
      setScanStats({
        total: scans.length,
        vulnerable,
        clean: scans.length - vulnerable
      });
      setRecentScans(scans.slice(0, 5));

      // Fetch runtime statistics
      const runtimeRes = await fetch(`${API_BASE}:8002/stats`);
      const runtimeData = await runtimeRes.json();
      setRuntimeStats({
        critical: runtimeData.severity_counts?.CRITICAL || 0,
        high: runtimeData.severity_counts?.HIGH || 0,
        warning: runtimeData.severity_counts?.WARNING || 0,
        info: runtimeData.severity_counts?.INFO || 0
      });

      // Fetch alerts
      const alertsRes = await fetch(`${API_BASE}:8002/alerts?limit=10`);
      const alertsData = await alertsRes.json();
      setRecentAlerts(alertsData.alerts || []);

      // Fetch admission statistics
      const admissionRes = await fetch(`${API_BASE}:8003/stats`);
      const admissionData = await admissionRes.json();
      setAdmissionStats(admissionData);

      // Fetch decisions
      const decisionsRes = await fetch(`${API_BASE}:8003/decisions?limit=5`);
      const decisionsData = await decisionsRes.json();
      setRecentDecisions(decisionsData.decisions || []);

      // Fetch benchmark score
      const benchmarkRes = await fetch(`${API_BASE}:8004/benchmark/latest`);
      const benchmarkData = await benchmarkRes.json();
      setBenchmarkScore(benchmarkData.score || 0);

    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const runScan = async () => {
    try {
      setScanLoading(true);
      setActionStatus('');
      const images = [
        'nginx:latest',
        'vulnerable-image:old',
        'python:3.11-slim'
      ];
      
      const randomImage = images[Math.floor(Math.random() * images.length)];
      
      const response = await fetch(`${API_BASE}:8001/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: randomImage, policy: 'default' })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Scan request failed');
      }

      setActionStatus(`Scan started for ${randomImage}`);
      setTimeout(fetchDashboardData, 3000);
    } catch (error) {
      console.error('Error starting scan:', error);
      setActionStatus('Failed to start scan');
    } finally {
      setScanLoading(false);
    }
  };

  const runBenchmark = async () => {
    try {
      setBenchmarkLoading(true);
      setActionStatus('');
      const res = await fetch(`${API_BASE}:8004/benchmark/run`, { method: 'POST' });
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || 'Benchmark request failed');
      }
      setActionStatus('Benchmark started');
      setTimeout(fetchDashboardData, 3000);
    } catch (error) {
      console.error('Error running benchmark:', error);
      setActionStatus('Failed to start benchmark');
    } finally {
      setBenchmarkLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      CRITICAL: '#e53e3e',
      HIGH: '#dd6b20',
      WARNING: '#d69e2e',
      MEDIUM: '#d69e2e',
      INFO: '#3182ce',
      LOW: '#38a169'
    };
    return colors[severity] || '#718096';
  };

  return (
    <div className="App">
      <header className="header">
        <div className="container">
          <h1>🛡️ Container Security Platform</h1>
          <p>Real-time monitoring, scanning, and policy enforcement</p>
        </div>
      </header>

      <div className="container">
        {/* Key Metrics */}
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-icon">🔍</div>
            <div className="metric-content">
              <div className="metric-value">{scanStats.total}</div>
              <div className="metric-label">Total Scans</div>
              <div className="metric-detail">
                <span className="metric-bad">{scanStats.vulnerable} vulnerable</span>
                <span className="metric-good">{scanStats.clean} clean</span>
              </div>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon">⚡</div>
            <div className="metric-content">
              <div className="metric-value">{runtimeStats.critical + runtimeStats.high}</div>
              <div className="metric-label">Active Alerts</div>
              <div className="metric-detail">
                <span className="metric-bad">{runtimeStats.critical} critical</span>
                <span className="metric-warning">{runtimeStats.high} high</span>
              </div>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon">🚪</div>
            <div className="metric-content">
              <div className="metric-value">{admissionStats.rejected}</div>
              <div className="metric-label">Blocked Deployments</div>
              <div className="metric-detail">
                <span>{admissionStats.total} total requests</span>
              </div>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon">✅</div>
            <div className="metric-content">
              <div className="metric-value">{benchmarkScore.toFixed(1)}%</div>
              <div className="metric-label">CIS Compliance</div>
              <div className="metric-detail">
                <span>Kubernetes Benchmark</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="actions">
          <button className="btn btn-primary" onClick={runScan} disabled={scanLoading}>
            {scanLoading ? '⏳ Starting Scan...' : '🔍 Run Image Scan'}
          </button>
          <button className="btn btn-secondary" onClick={runBenchmark} disabled={benchmarkLoading}>
            {benchmarkLoading ? '⏳ Starting Benchmark...' : '✓ Run CIS Benchmark'}
          </button>
          {actionStatus && <div className="action-status">{actionStatus}</div>}
        </div>

        {/* Two Column Layout */}
        <div className="two-column">
          {/* Left Column */}
          <div className="column">
            {/* Recent Alerts */}
            <div className="card">
              <h2>⚡ Recent Security Alerts</h2>
              <div className="alerts-list">
                {recentAlerts.length === 0 ? (
                  <div className="empty-state">No alerts yet</div>
                ) : (
                  recentAlerts.map((alert, idx) => (
                    <div key={idx} className="alert-item">
                      <div className="alert-header">
                        <span 
                          className="alert-severity" 
                          style={{ backgroundColor: getSeverityColor(alert.severity) }}
                        >
                          {alert.severity}
                        </span>
                        <span className="alert-time">
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="alert-rule">{alert.rule}</div>
                      <div className="alert-details">
                        {alert.pod_name} • {alert.namespace}
                      </div>
                      <div className="alert-message">{alert.message}</div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Recent Scans */}
            <div className="card">
              <h2>🔍 Recent Image Scans</h2>
              <div className="scans-list">
                {recentScans.length === 0 ? (
                  <div className="empty-state">No scans yet</div>
                ) : (
                  recentScans.map((scan, idx) => (
                    <div key={idx} className="scan-item">
                      <div className="scan-image">{scan.image}</div>
                      <div className="scan-stats">
                        {scan.critical > 0 && (
                          <span className="vuln-badge critical">{scan.critical} Critical</span>
                        )}
                        {scan.high > 0 && (
                          <span className="vuln-badge high">{scan.high} High</span>
                        )}
                        {scan.medium > 0 && (
                          <span className="vuln-badge medium">{scan.medium} Medium</span>
                        )}
                        {scan.low > 0 && (
                          <span className="vuln-badge low">{scan.low} Low</span>
                        )}
                        {scan.critical === 0 && scan.high === 0 && scan.medium === 0 && scan.low === 0 && (
                          <span className="vuln-badge clean">Clean</span>
                        )}
                      </div>
                      <div className="scan-time">{new Date(scan.scan_time).toLocaleString()}</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="column">
            {/* Admission Decisions */}
            <div className="card">
              <h2>🚪 Admission Controller Decisions</h2>
              <div className="decisions-list">
                {recentDecisions.length === 0 ? (
                  <div className="empty-state">No decisions yet</div>
                ) : (
                  recentDecisions.map((decision, idx) => (
                    <div key={idx} className={`decision-item ${decision.allowed ? 'allowed' : 'rejected'}`}>
                      <div className="decision-header">
                        <span className={`decision-badge ${decision.allowed ? 'allowed' : 'rejected'}`}>
                          {decision.allowed ? '✓ ALLOWED' : '✗ REJECTED'}
                        </span>
                        <span className="decision-time">
                          {new Date(decision.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="decision-pod">{decision.pod_name}</div>
                      <div className="decision-namespace">{decision.namespace}</div>
                      <div className="decision-reason">{decision.reason}</div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Runtime Statistics */}
            <div className="card">
              <h2>📊 Runtime Security Statistics</h2>
              <div className="stats-grid">
                <div className="stat-item">
                  <div className="stat-value" style={{ color: '#e53e3e' }}>
                    {runtimeStats.critical || 0}
                  </div>
                  <div className="stat-label">Critical Alerts</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value" style={{ color: '#dd6b20' }}>
                    {runtimeStats.high || 0}
                  </div>
                  <div className="stat-label">High Severity</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value" style={{ color: '#d69e2e' }}>
                    {runtimeStats.warning || 0}
                  </div>
                  <div className="stat-label">Warnings</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value" style={{ color: '#3182ce' }}>
                    {runtimeStats.info || 0}
                  </div>
                  <div className="stat-label">Info</div>
                </div>
              </div>
            </div>

            {/* Compliance Score */}
            <div className="card">
              <h2>✅ CIS Kubernetes Compliance</h2>
              <div className="compliance-score">
                <div className="score-circle">
                  <svg viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="#e2e8f0" strokeWidth="8" />
                    <circle 
                      cx="50" 
                      cy="50" 
                      r="40" 
                      fill="none" 
                      stroke="#48bb78" 
                      strokeWidth="8"
                      strokeDasharray={`${benchmarkScore * 2.51} 251`}
                      transform="rotate(-90 50 50)"
                    />
                  </svg>
                  <div className="score-text">{benchmarkScore.toFixed(0)}%</div>
                </div>
                <div className="score-label">Compliance Score</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
