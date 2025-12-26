import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './Panel.css';

function DriftDetectionPanel() {
  const [driftStatus, setDriftStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDriftStatus();
    const interval = setInterval(loadDriftStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDriftStatus = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8001/drift/status');
      setDriftStatus(response.data);
    } catch (error) {
      console.error('Error loading drift status:', error);
    }
    setLoading(false);
  };

  const getChartData = () => {
    if (!driftStatus?.features) return [];
    return Object.entries(driftStatus.features).map(([feature, data]) => ({
      feature,
      'KS Statistic': data.ks_statistic || 0,
      'P-Value': data.p_value || 0
    }));
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>📈 Drift Detection Analysis</h2>
        <button onClick={loadDriftStatus} className="action-button" disabled={loading}>
          {loading ? 'Loading...' : 'Refresh Analysis'}
        </button>
      </div>

      {driftStatus && (
        <>
          <div className="stats-grid">
            {Object.entries(driftStatus.features || {}).map(([feature, data]) => (
              <div key={feature} className={`stat-card ${data.drift_detected ? 'alert' : ''}`}>
                <div className="stat-icon">{data.drift_detected ? '⚠️' : '✓'}</div>
                <div className="stat-content">
                  <div className="stat-label">{feature}</div>
                  <div className="stat-value">
                    {data.drift_detected ? 'Drift Detected' : 'Normal'}
                  </div>
                  <div className="stat-detail">
                    p-value: {data.p_value?.toFixed(4) || 'N/A'}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="chart-container">
            <h3>Feature Drift Scores</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getChartData()}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis dataKey="feature" stroke="#666" />
                <YAxis stroke="#666" />
                <Tooltip 
                  contentStyle={{ background: '#fff', border: '1px solid #ddd', borderRadius: '8px' }}
                />
                <Legend />
                <Bar dataKey="KS Statistic" fill="#667eea" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}

export default DriftDetectionPanel;
