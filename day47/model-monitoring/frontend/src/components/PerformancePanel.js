import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './Panel.css';

function PerformancePanel() {
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPerformance();
    const interval = setInterval(loadPerformance, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadPerformance = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8002/performance/current');
      setPerformance(response.data);
    } catch (error) {
      console.error('Error loading performance:', error);
    }
    setLoading(false);
  };

  const getMetricsData = () => {
    if (!performance?.metrics) return [];
    return Object.entries(performance.metrics).map(([window, metrics]) => ({
      window,
      Accuracy: (metrics.accuracy * 100).toFixed(2),
      Precision: (metrics.precision * 100).toFixed(2),
      Recall: (metrics.recall * 100).toFixed(2),
      'F1 Score': (metrics.f1 * 100).toFixed(2),
      'AUC-ROC': (metrics.auc_roc * 100).toFixed(2)
    }));
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🎯 Performance Tracking</h2>
        <button onClick={loadPerformance} className="action-button" disabled={loading}>
          {loading ? 'Loading...' : 'Refresh Metrics'}
        </button>
      </div>

      {performance?.metrics && (
        <>
          <div className="stats-grid">
            {Object.entries(performance.metrics).map(([window, metrics]) => (
              <div key={window} className="stat-card large">
                <div className="stat-header">
                  <div className="stat-icon">⏱️</div>
                  <div className="stat-label">{window} Window</div>
                </div>
                <div className="metrics-grid">
                  <div className="metric">
                    <span>Accuracy</span>
                    <strong>{(metrics.accuracy * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="metric">
                    <span>Precision</span>
                    <strong>{(metrics.precision * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="metric">
                    <span>Recall</span>
                    <strong>{(metrics.recall * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="metric">
                    <span>F1 Score</span>
                    <strong>{(metrics.f1 * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="metric">
                    <span>AUC-ROC</span>
                    <strong>{(metrics.auc_roc * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="metric">
                    <span>Samples</span>
                    <strong>{metrics.sample_count}</strong>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default PerformancePanel;
