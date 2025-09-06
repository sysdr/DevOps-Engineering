import React, { useState, useEffect } from 'react';
import './App.css';
import SystemMetrics from './components/SystemMetrics';
import CostAnalysis from './components/CostAnalysis';
import InfrastructureStatus from './components/InfrastructureStatus';
import PerformanceTuning from './components/PerformanceTuning';

function App() {
  const [activeTab, setActiveTab] = useState('metrics');

  return (
    <div className="App">
      <header className="app-header">
        <h1>🚀 DevOps Foundation Dashboard</h1>
        <p>Day 1: Modern Linux Systems & Cloud Foundation</p>
      </header>
      
      <nav className="tab-navigation">
        <button 
          className={activeTab === 'metrics' ? 'active' : ''}
          onClick={() => setActiveTab('metrics')}
        >
          System Metrics
        </button>
        <button 
          className={activeTab === 'costs' ? 'active' : ''}
          onClick={() => setActiveTab('costs')}
        >
          Cost Analysis
        </button>
        <button 
          className={activeTab === 'infrastructure' ? 'active' : ''}
          onClick={() => setActiveTab('infrastructure')}
        >
          Infrastructure
        </button>
        <button 
          className={activeTab === 'performance' ? 'active' : ''}
          onClick={() => setActiveTab('performance')}
        >
          Performance
        </button>
      </nav>

      <main className="main-content">
        {activeTab === 'metrics' && <SystemMetrics />}
        {activeTab === 'costs' && <CostAnalysis />}
        {activeTab === 'infrastructure' && <InfrastructureStatus />}
        {activeTab === 'performance' && <PerformanceTuning />}
      </main>
    </div>
  );
}

export default App;
