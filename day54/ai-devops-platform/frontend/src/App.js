import React, { useState, useEffect, useRef } from 'react';
import CodeAnalyzer from './components/CodeAnalyzer';
import LogAnalyzer from './components/LogAnalyzer';
import IncidentManager from './components/IncidentManager';
import DocGenerator from './components/DocGenerator';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('code');
  const [systemHealth, setSystemHealth] = useState({});

  useEffect(() => {
    const checkHealth = async () => {
      const services = [
        { name: 'code-analyzer', port: 8001 },
        { name: 'log-analyzer', port: 8002 },
        { name: 'incident-manager', port: 8003 },
        { name: 'doc-generator', port: 8004 }
      ];

      const health = {};
      for (const service of services) {
        try {
          const response = await fetch(`http://localhost:${service.port}/health`);
          health[service.name] = response.ok ? 'healthy' : 'down';
        } catch {
          health[service.name] = 'down';
        }
      }
      setSystemHealth(health);
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app">
      <header className="header">
        <h1>🤖 AI-Powered DevOps Platform</h1>
        <div className="health-indicators">
          {Object.entries(systemHealth).map(([service, status]) => (
            <div key={service} className={`health-badge ${status}`}>
              <span className="dot"></span>
              {service.replace('-', ' ')}
            </div>
          ))}
        </div>
      </header>

      <nav className="tabs">
        <button
          className={activeTab === 'code' ? 'active' : ''}
          onClick={() => setActiveTab('code')}
        >
          📝 Code Analyzer
        </button>
        <button
          className={activeTab === 'logs' ? 'active' : ''}
          onClick={() => setActiveTab('logs')}
        >
          📊 Log Analyzer
        </button>
        <button
          className={activeTab === 'incidents' ? 'active' : ''}
          onClick={() => setActiveTab('incidents')}
        >
          🚨 Incident Manager
        </button>
        <button
          className={activeTab === 'docs' ? 'active' : ''}
          onClick={() => setActiveTab('docs')}
        >
          📚 Doc Generator
        </button>
      </nav>

      <main className="main-content">
        {activeTab === 'code' && <CodeAnalyzer />}
        {activeTab === 'logs' && <LogAnalyzer />}
        {activeTab === 'incidents' && <IncidentManager />}
        {activeTab === 'docs' && <DocGenerator />}
      </main>
    </div>
  );
}

export default App;
