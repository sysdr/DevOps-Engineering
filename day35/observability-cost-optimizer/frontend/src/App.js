import React, { useState, useEffect } from 'react';
import './App.css';
import CostDashboard from './components/CostDashboard';
import MetricAnalyzer from './components/MetricAnalyzer';
import TraceOptimizer from './components/TraceOptimizer';
import RetentionManager from './components/RetentionManager';
import ROICalculator from './components/ROICalculator';
import Recommendations from './components/Recommendations';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [wsConnected, setWsConnected] = useState(false);
  const [realtimeData, setRealtimeData] = useState(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
      setWsConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setRealtimeData(data);
    };
    
    ws.onerror = () => setWsConnected(false);
    ws.onclose = () => setWsConnected(false);
    
    return () => ws.close();
  }, []);

  const tabs = [
    { id: 'dashboard', label: 'Cost Dashboard', icon: '📊' },
    { id: 'metrics', label: 'Metric Analyzer', icon: '📈' },
    { id: 'traces', label: 'Trace Optimizer', icon: '🔍' },
    { id: 'retention', label: 'Retention Manager', icon: '💾' },
    { id: 'roi', label: 'ROI Calculator', icon: '💰' },
    { id: 'recommendations', label: 'Recommendations', icon: '💡' }
  ];

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎯 Observability Cost Optimizer</h1>
        <div className="connection-status">
          <span className={`status-indicator ${wsConnected ? 'connected' : 'disconnected'}`}></span>
          {wsConnected ? 'Live' : 'Disconnected'}
        </div>
      </header>

      <nav className="tab-navigation">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="app-content">
        {activeTab === 'dashboard' && <CostDashboard realtimeData={realtimeData} />}
        {activeTab === 'metrics' && <MetricAnalyzer />}
        {activeTab === 'traces' && <TraceOptimizer />}
        {activeTab === 'retention' && <RetentionManager />}
        {activeTab === 'roi' && <ROICalculator />}
        {activeTab === 'recommendations' && <Recommendations />}
      </main>
    </div>
  );
}

export default App;
