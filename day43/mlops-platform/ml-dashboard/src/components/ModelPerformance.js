import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const ModelPerformance = () => {
  const [metrics, setMetrics] = useState(null);
  const [latencyData, setLatencyData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await axios.get('http://localhost:8002/performance/fraud_detection_demo_random_forest');
      setMetrics(response.data);
      
      // Update latency chart
      setLatencyData(prev => {
        const newData = [...prev, {
          time: new Date().toLocaleTimeString(),
          avg: response.data.avg_latency_ms,
          p95: response.data.p95_latency_ms,
          p99: response.data.p99_latency_ms
        }];
        return newData.slice(-20); // Keep last 20 points
      });
      
      setLoading(false);
    } catch (err) {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="card"><div className="loading">Loading metrics...</div></div>;
  }

  return (
    <div>
      <div className="card">
        <h2>Model Performance Metrics</h2>
        
        <div className="grid">
          <div className="metric-card">
            <div className="metric-label">Total Predictions</div>
            <div className="metric-value">{metrics?.total_predictions || 0}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Avg Latency</div>
            <div className="metric-value">{metrics?.avg_latency_ms?.toFixed(2) || 0}ms</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">P95 Latency</div>
            <div className="metric-value">{metrics?.p95_latency_ms?.toFixed(2) || 0}ms</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Error Rate</div>
            <div className="metric-value">{(metrics?.error_rate * 100 || 0).toFixed(2)}%</div>
          </div>
        </div>

        {latencyData.length > 0 && (
          <div style={{ marginTop: '2rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>Latency Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={latencyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="time" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip 
                  contentStyle={{ background: 'rgba(255, 255, 255, 0.95)', border: 'none', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                />
                <Legend />
                <Line type="monotone" dataKey="avg" stroke="#667eea" strokeWidth={2} name="Average" />
                <Line type="monotone" dataKey="p95" stroke="#f59e0b" strokeWidth={2} name="P95" />
                <Line type="monotone" dataKey="p99" stroke="#ef4444" strokeWidth={2} name="P99" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
};

export default ModelPerformance;
