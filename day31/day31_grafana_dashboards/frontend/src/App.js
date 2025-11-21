import React, { useState, useEffect } from 'react';
import DashboardList from './components/DashboardList';
import MetricsChart from './components/MetricsChart';
import GrafanaStatus from './components/GrafanaStatus';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboards');
  const [apiStatus, setApiStatus] = useState({ backend: false, grafana: false });

  useEffect(() => {
    checkServices();
    const interval = setInterval(checkServices, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkServices = async () => {
    try {
      const backendRes = await fetch('http://localhost:8001/');
      const grafanaRes = await fetch('http://localhost:8001/api/grafana/status');
      
      setApiStatus({
        backend: backendRes.ok,
        grafana: (await grafanaRes.json()).database === 'ok'
      });
    } catch (error) {
      console.error('Service check failed:', error);
    }
  };

  return (
    <div className="App">
      <header className="header">
        <h1>📊 Grafana Dashboard Manager</h1>
        <div className="status-indicators">
          <span className={`status-badge ${apiStatus.backend ? 'online' : 'offline'}`}>
            Backend: {apiStatus.backend ? 'Online' : 'Offline'}
          </span>
          <span className={`status-badge ${apiStatus.grafana ? 'online' : 'offline'}`}>
            Grafana: {apiStatus.grafana ? 'Online' : 'Offline'}
          </span>
        </div>
      </header>

      <nav className="tabs">
        <button 
          className={activeTab === 'dashboards' ? 'active' : ''}
          onClick={() => setActiveTab('dashboards')}
        >
          Dashboards
        </button>
        <button 
          className={activeTab === 'metrics' ? 'active' : ''}
          onClick={() => setActiveTab('metrics')}
        >
          Live Metrics
        </button>
        <button 
          className={activeTab === 'status' ? 'active' : ''}
          onClick={() => setActiveTab('status')}
        >
          Status
        </button>
      </nav>

      <main className="content">
        {activeTab === 'dashboards' && <DashboardList />}
        {activeTab === 'metrics' && <MetricsChart />}
        {activeTab === 'status' && <GrafanaStatus />}
      </main>
    </div>
  );
}

export default App;
