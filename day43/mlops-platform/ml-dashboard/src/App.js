import React, { useState, useEffect } from 'react';
import './App.css';
import TrainingJobs from './components/TrainingJobs';
import ModelPerformance from './components/ModelPerformance';
import DriftMonitoring from './components/DriftMonitoring';
import PredictionDemo from './components/PredictionDemo';

function App() {
  const [activeTab, setActiveTab] = useState('training');
  const [services, setServices] = useState({
    training: false,
    serving: false,
    monitoring: false
  });

  useEffect(() => {
    checkServices();
    const interval = setInterval(checkServices, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkServices = async () => {
    const checks = {
      training: await checkService('http://localhost:8000/health'),
      serving: await checkService('http://localhost:8001/health'),
      monitoring: await checkService('http://localhost:8002/health')
    };
    setServices(checks);
  };

  const checkService = async (url) => {
    try {
      const response = await fetch(url);
      return response.ok;
    } catch {
      return false;
    }
  };

  return (
    <div className="App">
      <header className="header">
        <div className="header-content">
          <h1>🚀 MLOps Platform</h1>
          <div className="service-status">
            <div className={`status-indicator ${services.training ? 'online' : 'offline'}`}>
              Training {services.training ? '●' : '○'}
            </div>
            <div className={`status-indicator ${services.serving ? 'online' : 'offline'}`}>
              Serving {services.serving ? '●' : '○'}
            </div>
            <div className={`status-indicator ${services.monitoring ? 'online' : 'offline'}`}>
              Monitoring {services.monitoring ? '●' : '○'}
            </div>
          </div>
        </div>
      </header>

      <nav className="nav-tabs">
        <button
          className={activeTab === 'training' ? 'active' : ''}
          onClick={() => setActiveTab('training')}
        >
          Training Jobs
        </button>
        <button
          className={activeTab === 'performance' ? 'active' : ''}
          onClick={() => setActiveTab('performance')}
        >
          Model Performance
        </button>
        <button
          className={activeTab === 'drift' ? 'active' : ''}
          onClick={() => setActiveTab('drift')}
        >
          Drift Monitoring
        </button>
        <button
          className={activeTab === 'predict' ? 'active' : ''}
          onClick={() => setActiveTab('predict')}
        >
          Live Predictions
        </button>
      </nav>

      <main className="content">
        {activeTab === 'training' && <TrainingJobs />}
        {activeTab === 'performance' && <ModelPerformance />}
        {activeTab === 'drift' && <DriftMonitoring />}
        {activeTab === 'predict' && <PredictionDemo />}
      </main>
    </div>
  );
}

export default App;
