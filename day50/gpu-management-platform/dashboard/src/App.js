import React, { useState, useEffect } from 'react';
import './App.css';
import GPUCluster from './components/GPUCluster';
import CostAnalytics from './components/CostAnalytics';
import SchedulerMetrics from './components/SchedulerMetrics';

const API_BASE = 'http://localhost';

function App() {
  const [gpus, setGpus] = useState([]);
  const [costAnalytics, setCostAnalytics] = useState(null);
  const [schedulerMetrics, setSchedulerMetrics] = useState(null);
  const [clusterState, setClusterState] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [gpusRes, costRes, schedulerRes, clusterRes] = await Promise.all([
        fetch(`${API_BASE}:8001/gpus`),
        fetch(`${API_BASE}:8003/analytics`),
        fetch(`${API_BASE}:8002/metrics`),
        fetch(`${API_BASE}:8002/cluster/state`)
      ]);

      if (gpusRes.ok) setGpus(await gpusRes.json());
      if (costRes.ok) setCostAnalytics(await costRes.json());
      if (schedulerRes.ok) setSchedulerMetrics(await schedulerRes.json());
      if (clusterRes.ok) setClusterState(await clusterRes.json());
    } catch (error) {
      console.error('Failed to fetch data:', error);
    }
  };

  return (
    <div className="App">
      <header className="header">
        <h1>🚀 GPU Management Platform</h1>
        <div className="header-stats">
          {clusterState && (
            <>
              <div className="stat">
                <span className="label">Total GPUs:</span>
                <span className="value">{clusterState.total_gpus}</span>
              </div>
              <div className="stat">
                <span className="label">MIG Instances:</span>
                <span className="value">{clusterState.mig_instances_total}</span>
              </div>
            </>
          )}
        </div>
      </header>

      <div className="tabs">
        <button 
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={activeTab === 'cost' ? 'active' : ''}
          onClick={() => setActiveTab('cost')}
        >
          Cost Analytics
        </button>
        <button 
          className={activeTab === 'scheduler' ? 'active' : ''}
          onClick={() => setActiveTab('scheduler')}
        >
          Scheduler
        </button>
      </div>

      <div className="content">
        {activeTab === 'overview' && (
          <GPUCluster gpus={gpus} />
        )}
        {activeTab === 'cost' && costAnalytics && (
          <CostAnalytics analytics={costAnalytics} />
        )}
        {activeTab === 'scheduler' && schedulerMetrics && (
          <SchedulerMetrics metrics={schedulerMetrics} />
        )}
      </div>
    </div>
  );
}

export default App;
