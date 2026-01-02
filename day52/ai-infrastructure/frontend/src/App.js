import React, { useState, useEffect } from 'react';
import './App.css';
import MetricsChart from './components/MetricsChart';
import PredictionPanel from './components/PredictionPanel';
import AnomalyList from './components/AnomalyList';
import IncidentPanel from './components/IncidentPanel';
import ScalingDecisions from './components/ScalingDecisions';

function App() {
  const [stats, setStats] = useState(null);
  const [metrics, setMetrics] = useState({});
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    // Fetch initial stats
    fetchStats();
    const statsInterval = setInterval(fetchStats, 10000);

    // WebSocket connection
    connectWebSocket();

    return () => {
      clearInterval(statsInterval);
    };
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/dashboard/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const connectWebSocket = () => {
    const ws = new WebSocket('ws://localhost:8000/ws/metrics');

    ws.onopen = () => {
      console.log('WebSocket connected');
      setWsConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'metrics_update') {
        setMetrics(message.data);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWsConnected(false);
      setTimeout(connectWebSocket, 5000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🤖 AI Infrastructure Management</h1>
        <div className="connection-status">
          <span className={wsConnected ? 'connected' : 'disconnected'}>
            {wsConnected ? '● Live' : '○ Connecting...'}
          </span>
        </div>
      </header>

      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Model Accuracy</h3>
            <div className="stat-value">{stats.model_accuracy.toFixed(1)}%</div>
          </div>
          <div className="stat-card">
            <h3>Anomalies (24h)</h3>
            <div className="stat-value">{stats.anomalies_24h}</div>
          </div>
          <div className="stat-card">
            <h3>Active Incidents</h3>
            <div className="stat-value">{stats.active_incidents}</div>
          </div>
          <div className="stat-card">
            <h3>Scaling Actions (24h)</h3>
            <div className="stat-value">{stats.scaling_actions_24h}</div>
          </div>
          <div className="stat-card cluster-health">
            <h3>Cluster Health</h3>
            <div className={`stat-value ${stats.cluster_health}`}>
              {stats.cluster_health}
            </div>
          </div>
        </div>
      )}

      <div className="dashboard-grid">
        <div className="panel">
          <h2>📊 Real-Time Metrics</h2>
          <MetricsChart metrics={metrics} />
        </div>

        <div className="panel">
          <h2>🔮 ML Predictions</h2>
          <PredictionPanel />
        </div>

        <div className="panel">
          <h2>🚨 Anomaly Detection</h2>
          <AnomalyList />
        </div>

        <div className="panel">
          <h2>🔍 Incident Response</h2>
          <IncidentPanel />
        </div>

        <div className="panel full-width">
          <h2>📈 Predictive Scaling Decisions</h2>
          <ScalingDecisions />
        </div>
      </div>
    </div>
  );
}

export default App;
