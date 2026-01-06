import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import BiasAnalysis from './components/BiasAnalysis';
import FairnessMonitor from './components/FairnessMonitor';
import GovernanceWorkflow from './components/GovernanceWorkflow';
import ExplainabilityDemo from './components/ExplainabilityDemo';

function App() {
  const [activeTab, setActiveTab] = useState('bias');
  const [stats, setStats] = useState({
    totalModels: 0,
    pendingReviews: 0,
    biasDetected: 0,
    approved: 0
  });
  const [loadingStats, setLoadingStats] = useState(true);

  const fetchStats = async () => {
    try {
      const response = await axios.get('http://localhost:8004/api/v1/governance/stats');
      setStats({
        totalModels: response.data.total_models || 0,
        pendingReviews: response.data.pending_reviews || 0,
        biasDetected: response.data.bias_detected || 0,
        approved: response.data.approved || 0
      });
    } catch (err) {
      console.error('Failed to fetch stats:', err);
      // Keep default values on error
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // Refresh stats every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="App">
      <header className="app-header">
        <h1>🛡️ AI Ethics & Governance Platform</h1>
        <p className="subtitle">Ensuring Fair, Transparent, and Accountable AI Systems</p>
      </header>

      <div className="stats-container">
        <div className="stat-card">
          <div className="stat-value">{loadingStats ? '...' : stats.totalModels}</div>
          <div className="stat-label">Total Models</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{loadingStats ? '...' : stats.pendingReviews}</div>
          <div className="stat-label">Pending Reviews</div>
        </div>
        <div className="stat-card alert">
          <div className="stat-value">{loadingStats ? '...' : stats.biasDetected}</div>
          <div className="stat-label">Bias Detected</div>
        </div>
        <div className="stat-card success">
          <div className="stat-value">{loadingStats ? '...' : stats.approved}</div>
          <div className="stat-label">Approved</div>
        </div>
      </div>

      <div className="tabs">
        <button 
          className={activeTab === 'bias' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('bias')}
        >
          Bias Detection
        </button>
        <button 
          className={activeTab === 'fairness' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('fairness')}
        >
          Fairness Monitoring
        </button>
        <button 
          className={activeTab === 'governance' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('governance')}
        >
          Governance Workflow
        </button>
        <button 
          className={activeTab === 'explain' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('explain')}
        >
          Explainability
        </button>
      </div>

      <div className="content">
        {activeTab === 'bias' && <BiasAnalysis />}
        {activeTab === 'fairness' && <FairnessMonitor />}
        {activeTab === 'governance' && <GovernanceWorkflow />}
        {activeTab === 'explain' && <ExplainabilityDemo />}
      </div>

      <footer className="app-footer">
        <p>Built with ❤️ for Responsible AI | Day 55: Hands-On Kubernetes Course</p>
      </footer>
    </div>
  );
}

export default App;
