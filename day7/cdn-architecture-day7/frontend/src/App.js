import React, { useState, useEffect } from 'react';
import './App.css';
import CDNDashboard from './components/CDNDashboard';
import RequestSimulator from './components/RequestSimulator';
import MetricsChart from './components/MetricsChart';
import SecurityPanel from './components/SecurityPanel';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('/api/cdn/metrics');
        const data = await response.json();
        setMetrics(data);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="App">
      <header className="app-header">
        <h1>🌐 CDN Architecture Dashboard</h1>
        <nav className="nav-tabs">
          <button 
            className={activeTab === 'dashboard' ? 'active' : ''}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Dashboard
          </button>
          <button 
            className={activeTab === 'simulator' ? 'active' : ''}
            onClick={() => setActiveTab('simulator')}
          >
            🎯 Request Simulator
          </button>
          <button 
            className={activeTab === 'metrics' ? 'active' : ''}
            onClick={() => setActiveTab('metrics')}
          >
            📈 Analytics
          </button>
          <button 
            className={activeTab === 'security' ? 'active' : ''}
            onClick={() => setActiveTab('security')}
          >
            🔒 Security
          </button>
        </nav>
      </header>

      <main className="app-main">
        {activeTab === 'dashboard' && <CDNDashboard metrics={metrics} />}
        {activeTab === 'simulator' && <RequestSimulator onMetricsUpdate={setMetrics} />}
        {activeTab === 'metrics' && <MetricsChart metrics={metrics} />}
        {activeTab === 'security' && <SecurityPanel />}
      </main>
    </div>
  );
}

export default App;
