import React, { useState, useEffect } from 'react';
import './App.css';
import Dashboard from './components/Dashboard';
import PipelineStatus from './components/PipelineStatus';
import ValidationMetrics from './components/ValidationMetrics';

function App() {
  const [pipelineData, setPipelineData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    // Fetch initial data
    fetchPipelineStatus();
    
    // Set up polling for updates
    const interval = setInterval(fetchPipelineStatus, 3000);
    
    return () => clearInterval(interval);
  }, []);
  
  const fetchPipelineStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/pipeline/status');
      const data = await response.json();
      setPipelineData(data);
      setIsConnected(true);
    } catch (error) {
      console.error('Error fetching pipeline status:', error);
      setIsConnected(false);
    }
  };
  
  return (
    <div className="App">
      <header className="app-header">
        <h1>🔄 Data Pipeline Monitor</h1>
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '● Connected' : '○ Disconnected'}
        </div>
      </header>
      
      <div className="app-container">
        {pipelineData ? (
          <>
            <Dashboard data={pipelineData} />
            <div className="metrics-grid">
              <PipelineStatus data={pipelineData} />
              <ValidationMetrics data={pipelineData} />
            </div>
          </>
        ) : (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading pipeline data...</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
