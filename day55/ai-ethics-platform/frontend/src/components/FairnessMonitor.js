import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

const FairnessMonitor = () => {
  const [modelId, setModelId] = useState('loan-model-v1');
  const [currentMetrics, setCurrentMetrics] = useState(null);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const [metricsRes, trendsRes] = await Promise.all([
        axios.get(`http://localhost:8002/api/v1/monitor/metrics/${modelId}`),
        axios.get(`http://localhost:8002/api/v1/monitor/trends/${modelId}?days=7`)
      ]);
      setCurrentMetrics(metricsRes.data);
      setTrends(trendsRes.data);
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to fetch metrics. Please try again.');
      setCurrentMetrics(null);
      setTrends(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [modelId]);

  return (
    <div>
      <h2 className="section-title">Continuous Fairness Monitoring</h2>

      <div className="card">
        <select
          value={modelId}
          onChange={(e) => setModelId(e.target.value)}
          style={{
            padding: '10px',
            fontSize: '1em',
            borderRadius: '6px',
            border: '2px solid #dee2e6',
            marginRight: '10px',
            minWidth: '200px'
          }}
        >
          <option value="loan-model-v1">Loan Model v1</option>
          <option value="hiring-model-v2">Hiring Model v2</option>
          <option value="credit-score-v3">Credit Score v3</option>
        </select>
        <button className="btn" onClick={fetchMetrics} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh Metrics'}
        </button>
      </div>

      {error && (
        <div className="error" style={{ marginTop: '20px' }}>
          {error}
        </div>
      )}

      {loading && !currentMetrics && (
        <div className="loading" style={{ marginTop: '20px' }}>
          Loading fairness metrics...
        </div>
      )}

      {currentMetrics && (
        <>
          <div className="card">
            <h3>Current Fairness Status (24h window)</h3>
            <div className="metric-row">
              <span className="metric-label">Fairness Ratio</span>
              <span className={`metric-value ${currentMetrics.fairness_ratio >= 0.80 ? 'pass' : 'fail'}`}>
                {currentMetrics.fairness_ratio.toFixed(3)}
              </span>
            </div>
            {currentMetrics.alert_triggered && (
              <div className="error" style={{ marginTop: '10px' }}>
                ⚠️ Alert: Fairness ratio below threshold! Immediate review required.
              </div>
            )}

            <h4 style={{ marginTop: '20px', marginBottom: '10px' }}>Group Performance</h4>
            {Object.keys(currentMetrics.group_metrics || {}).length > 0 ? (
              Object.entries(currentMetrics.group_metrics).map(([group, metrics]) => (
                <div key={group} style={{ marginBottom: '10px', padding: '10px', background: '#f8f9fa', borderRadius: '6px' }}>
                  <strong>{group}:</strong> Mean: {metrics.mean.toFixed(3)}, Std: {metrics.std.toFixed(3)}, Count: {metrics.count}
                </div>
              ))
            ) : (
              <div style={{ padding: '10px', color: '#6c757d', fontStyle: 'italic' }}>
                No group metrics available. Data may still be collecting.
              </div>
            )}
          </div>

          {trends && trends.trend && trends.trend.length > 0 ? (
            <div className="card">
              <h3>7-Day Fairness Trend</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trends.trend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis domain={[0, 1]} />
                  <Tooltip />
                  <Legend />
                  <ReferenceLine y={0.80} stroke="#ff6b6b" strokeDasharray="5 5" label="Threshold (0.80)" />
                  <Line type="monotone" dataKey="fairness_ratio" stroke="#667eea" strokeWidth={2} name="Fairness Ratio" />
                </LineChart>
              </ResponsiveContainer>
              <div style={{ marginTop: '10px', fontSize: '0.9em', color: '#6c757d' }}>
                <p>📊 Threshold at 0.80 indicates fairness minimum. Values below trigger alerts.</p>
              </div>
            </div>
          ) : (
            <div className="card">
              <h3>7-Day Fairness Trend</h3>
              <div style={{ padding: '20px', textAlign: 'center', color: '#6c757d' }}>
                <p>No trend data available yet. Historical data will appear here as it accumulates.</p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default FairnessMonitor;
