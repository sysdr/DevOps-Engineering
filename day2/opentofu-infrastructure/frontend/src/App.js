import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Components
import Dashboard from './components/Dashboard';
import EnvironmentCard from './components/EnvironmentCard';
import DriftMonitor from './components/DriftMonitor';

function App() {
  const [infrastructureStatus, setInfrastructureStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchInfrastructureStatus();
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchInfrastructureStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchInfrastructureStatus = async () => {
    try {
      const response = await axios.get('/api/infrastructure/status');
      setInfrastructureStatus(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch infrastructure status');
      console.error('Error fetching status:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading infrastructure status...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={fetchInfrastructureStatus} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="app-header">
        <h1>🏗️ OpenTofu Infrastructure Manager</h1>
        <p>Day 2: Advanced Infrastructure Patterns & State Management</p>
      </header>

      <main className="app-main">
        <Dashboard status={infrastructureStatus} />
        
        <div className="environments-section">
          <h2>Environments</h2>
          <div className="environments-grid">
            {Object.entries(infrastructureStatus?.environments || {}).map(([name, env]) => (
              <EnvironmentCard key={name} environment={env} onRefresh={fetchInfrastructureStatus} />
            ))}
            
            {/* Add default environments if none exist */}
            {Object.keys(infrastructureStatus?.environments || {}).length === 0 && (
              <>
                <EnvironmentCard 
                  environment={{
                    environment: 'dev',
                    status: 'unknown',
                    resources: [],
                    last_updated: new Date().toISOString(),
                    drift_detected: false
                  }} 
                  onRefresh={fetchInfrastructureStatus}
                />
                <EnvironmentCard 
                  environment={{
                    environment: 'staging',
                    status: 'unknown',
                    resources: [],
                    last_updated: new Date().toISOString(),
                    drift_detected: false
                  }} 
                  onRefresh={fetchInfrastructureStatus}
                />
                <EnvironmentCard 
                  environment={{
                    environment: 'prod',
                    status: 'unknown',
                    resources: [],
                    last_updated: new Date().toISOString(),
                    drift_detected: false
                  }} 
                  onRefresh={fetchInfrastructureStatus}
                />
              </>
            )}
          </div>
        </div>

        <DriftMonitor />
      </main>
    </div>
  );
}

export default App;
