import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const SystemMetrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/system/metrics');
        const data = await response.json();
        setMetrics(data);
        
        // Update history for charts
        setHistory(prev => {
          const newHistory = [...prev, {
            time: new Date().toLocaleTimeString(),
            cpu: data.cpu.usage_percent,
            memory: data.memory.percent,
            disk: data.disk.percent
          }];
          return newHistory.slice(-20); // Keep last 20 points
        });
      } catch (error) {
        console.error('Error fetching metrics:', error);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!metrics) return <div className="loading">Loading system metrics...</div>;

  return (
    <div className="metrics-container">
      <div className="metrics-grid">
        <div className="metric-card">
          <h3>CPU Usage</h3>
          <div className="metric-value">{metrics.cpu.usage_percent.toFixed(1)}%</div>
          <div className="metric-detail">Cores: {metrics.cpu.count}</div>
        </div>
        
        <div className="metric-card">
          <h3>Memory Usage</h3>
          <div className="metric-value">{metrics.memory.percent.toFixed(1)}%</div>
          <div className="metric-detail">
            {(metrics.memory.used / 1024 / 1024 / 1024).toFixed(1)}GB / 
            {(metrics.memory.total / 1024 / 1024 / 1024).toFixed(1)}GB
          </div>
        </div>
        
        <div className="metric-card">
          <h3>Disk Usage</h3>
          <div className="metric-value">{metrics.disk.percent.toFixed(1)}%</div>
          <div className="metric-detail">
            {(metrics.disk.used / 1024 / 1024 / 1024).toFixed(1)}GB / 
            {(metrics.disk.total / 1024 / 1024 / 1024).toFixed(1)}GB
          </div>
        </div>
        
        <div className="metric-card">
          <h3>Network I/O</h3>
          <div className="metric-value">
            ↑{(metrics.network.bytes_sent / 1024 / 1024).toFixed(1)}MB
          </div>
          <div className="metric-detail">
            ↓{(metrics.network.bytes_recv / 1024 / 1024).toFixed(1)}MB
          </div>
        </div>
      </div>
      
      <div className="chart-container">
        <h3>Resource Usage Trends</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={history}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Line type="monotone" dataKey="cpu" stroke="#ff6b6b" name="CPU %" />
            <Line type="monotone" dataKey="memory" stroke="#4ecdc4" name="Memory %" />
            <Line type="monotone" dataKey="disk" stroke="#45b7d1" name="Disk %" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default SystemMetrics;
