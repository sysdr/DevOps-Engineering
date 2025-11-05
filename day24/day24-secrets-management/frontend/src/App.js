import React, { useState, useEffect } from 'react';
import './App.css';
import DriftMonitor from './components/DriftMonitor';
import SecretsMonitor from './components/SecretsMonitor';
import SealedSecretsInfo from './components/SealedSecretsInfo';

function App() {
  const [activeTab, setActiveTab] = useState('drift');
  const [healthStatus, setHealthStatus] = useState(null);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/health');
      const data = await response.json();
      setHealthStatus(data);
    } catch (error) {
      console.error('Health check failed:', error);
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🔐 Secrets Management & GitOps Dashboard</h1>
        <div className="health-status">
          {healthStatus && (
            <span className={`status-badge ${healthStatus.status}`}>
              ● {healthStatus.status.toUpperCase()}
            </span>
          )}
        </div>
      </header>

      <nav className="tab-navigation">
        <button 
          className={`tab ${activeTab === 'drift' ? 'active' : ''}`}
          onClick={() => setActiveTab('drift')}
        >
          Drift Detection
        </button>
        <button 
          className={`tab ${activeTab === 'secrets' ? 'active' : ''}`}
          onClick={() => setActiveTab('secrets')}
        >
          External Secrets
        </button>
        <button 
          className={`tab ${activeTab === 'sealed' ? 'active' : ''}`}
          onClick={() => setActiveTab('sealed')}
        >
          Sealed Secrets
        </button>
      </nav>

      <main className="dashboard-content">
        {activeTab === 'drift' && <DriftMonitor />}
        {activeTab === 'secrets' && <SecretsMonitor />}
        {activeTab === 'sealed' && <SealedSecretsInfo />}
      </main>

      <footer className="app-footer">
        <p>Day 24: Configuration Management & Secrets | GitOps Best Practices</p>
      </footer>
    </div>
  );
}

export default App;
