import React, { useState, useEffect } from 'react';
import './App.css';
import MetricsCollectorPanel from './components/MetricsCollectorPanel';
import DriftDetectionPanel from './components/DriftDetectionPanel';
import PerformancePanel from './components/PerformancePanel';
import ExplainabilityPanel from './components/ExplainabilityPanel';
import FairnessPanel from './components/FairnessPanel';

function App() {
  const [activeTab, setActiveTab] = useState('metrics');
  const [systemStatus, setSystemStatus] = useState('healthy');

  useEffect(() => {
    const interval = setInterval(() => {
      fetch('http://localhost:8000/metrics/stats')
        .then(res => res.json())
        .then(data => {
          if (data.total_predictions > 0) {
            setSystemStatus('healthy');
          }
        })
        .catch(() => setSystemStatus('degraded'));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <h1>🎯 Model Monitoring & Observability Platform</h1>
          <div className="system-status">
            <span className={`status-indicator ${systemStatus}`}></span>
            <span>System {systemStatus}</span>
          </div>
        </div>
        <nav className="nav-tabs">
          <button 
            className={activeTab === 'metrics' ? 'active' : ''}
            onClick={() => setActiveTab('metrics')}
          >
            📊 Metrics Collection
          </button>
          <button 
            className={activeTab === 'drift' ? 'active' : ''}
            onClick={() => setActiveTab('drift')}
          >
            📈 Drift Detection
          </button>
          <button 
            className={activeTab === 'performance' ? 'active' : ''}
            onClick={() => setActiveTab('performance')}
          >
            🎯 Performance Tracking
          </button>
          <button 
            className={activeTab === 'explainability' ? 'active' : ''}
            onClick={() => setActiveTab('explainability')}
          >
            🔍 Explainability
          </button>
          <button 
            className={activeTab === 'fairness' ? 'active' : ''}
            onClick={() => setActiveTab('fairness')}
          >
            ⚖️ Fairness Monitoring
          </button>
        </nav>
      </header>

      <main className="app-main">
        {activeTab === 'metrics' && <MetricsCollectorPanel />}
        {activeTab === 'drift' && <DriftDetectionPanel />}
        {activeTab === 'performance' && <PerformancePanel />}
        {activeTab === 'explainability' && <ExplainabilityPanel />}
        {activeTab === 'fairness' && <FairnessPanel />}
      </main>
    </div>
  );
}

export default App;
