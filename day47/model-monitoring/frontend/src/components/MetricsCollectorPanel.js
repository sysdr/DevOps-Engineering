import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Panel.css';

function MetricsCollectorPanel() {
  const [stats, setStats] = useState(null);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      const response = await axios.get('http://localhost:8000/metrics/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const sendTestPrediction = async () => {
    try {
      const payload = {
        model_id: 'fraud-detection-v1',
        prediction_id: `pred-${Date.now()}`,
        features: {
          amount: Math.random() * 1000,
          frequency: Math.floor(Math.random() * 20),
          recency: Math.random() * 30
        },
        prediction: Math.random(),
        ground_truth: Math.random() > 0.5 ? 1 : 0
      };

      const response = await axios.post('http://localhost:8000/metrics/collect', payload);
      setTestResult({ success: true, data: response.data });
      loadStats();
    } catch (error) {
      setTestResult({ success: false, error: error.message });
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>📊 Metrics Collection Status</h2>
        <button onClick={sendTestPrediction} className="action-button">
          Send Test Prediction
        </button>
      </div>

      {testResult && (
        <div className={`alert ${testResult.success ? 'success' : 'error'}`}>
          {testResult.success ? '✓ Test prediction sent successfully!' : `✗ Error: ${testResult.error}`}
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <div className="stat-label">Total Predictions</div>
            <div className="stat-value">{stats?.total_predictions || 0}</div>
          </div>
        </div>

        {stats?.by_model?.map((model, idx) => (
          <div key={idx} className="stat-card">
            <div className="stat-icon">🎯</div>
            <div className="stat-content">
              <div className="stat-label">{model.model_id}</div>
              <div className="stat-value">{model.count}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="info-section">
        <h3>System Information</h3>
        <p>The metrics collector captures all model predictions in real-time, storing features, predictions, and ground truth labels for downstream analysis.</p>
      </div>
    </div>
  );
}

export default MetricsCollectorPanel;
