import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { Database, Server, HardDrive, Activity, AlertTriangle, CheckCircle } from 'lucide-react';
import './App.css';

const API_BASE = 'http://localhost:8000';

function App() {
  const [clusterMetrics, setClusterMetrics] = useState(null);
  const [storageMetrics, setStorageMetrics] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const [clusterRes, storageRes] = await Promise.all([
        axios.get(`${API_BASE}/metrics/cluster`),
        axios.get(`${API_BASE}/metrics/storage`)
      ]);

      setClusterMetrics(clusterRes.data);
      setStorageMetrics(storageRes.data);

      // Add to historical data
      const timestamp = new Date().toLocaleTimeString();
      const newDataPoint = {
        time: timestamp,
        primaryConnections: clusterRes.data.primary?.active_connections || 0,
        replicaConnections: clusterRes.data.replica?.active_connections || 0,
        replicationLag: clusterRes.data.replica?.replication_lag_seconds || 0,
        avgQueryTime: clusterRes.data.primary?.avg_query_time_ms || 0
      };

      setHistoricalData(prev => [...prev.slice(-19), newDataPoint]); // Keep last 20 points
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
      setLoading(false);
    }
  };

  const getHealthStatus = (metrics) => {
    if (!metrics) return 'unknown';
    const primaryOnline = metrics.primary?.online;
    const replicaOnline = metrics.replica?.online;
    
    if (primaryOnline && replicaOnline) return 'healthy';
    if (primaryOnline) return 'degraded';
    return 'critical';
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const testFailover = async () => {
    try {
      await axios.post(`${API_BASE}/test/failover`);
      alert('Failover test initiated. Check cluster status for results.');
    } catch (error) {
      alert('Failed to initiate failover test');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <Activity className="loading-spinner" />
        <p>Loading cluster metrics...</p>
      </div>
    );
  }

  const healthStatus = getHealthStatus(clusterMetrics);
  const storageUsageData = storageMetrics?.disk_usage ? [
    { name: 'Used', value: storageMetrics.disk_usage.used, fill: '#e74c3c' },
    { name: 'Free', value: storageMetrics.disk_usage.free, fill: '#2ecc71' }
  ] : [];

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1><Database className="header-icon" /> PostgreSQL Cluster Monitor</h1>
        <div className={`health-badge ${healthStatus}`}>
          {healthStatus === 'healthy' ? <CheckCircle /> : <AlertTriangle />}
          Cluster {healthStatus.toUpperCase()}
        </div>
      </header>

      <div className="metrics-grid">
        {/* Cluster Overview */}
        <div className="metric-card cluster-overview">
          <h3><Server className="card-icon" /> Cluster Overview</h3>
          <div className="overview-stats">
            <div className="stat-item">
              <span className="stat-label">Primary Status</span>
              <span className={`stat-value ${clusterMetrics?.primary?.online ? 'online' : 'offline'}`}>
                {clusterMetrics?.primary?.online ? 'Online' : 'Offline'}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Replica Status</span>
              <span className={`stat-value ${clusterMetrics?.replica?.online ? 'online' : 'offline'}`}>
                {clusterMetrics?.replica?.online ? 'Online' : 'Offline'}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Replication Lag</span>
              <span className="stat-value">
                {(clusterMetrics?.replica?.replication_lag_seconds || 0).toFixed(2)}s
              </span>
            </div>
          </div>
        </div>

        {/* Connection Metrics */}
        <div className="metric-card">
          <h3><Activity className="card-icon" /> Active Connections</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="primaryConnections" stroke="#3498db" name="Primary" />
              <Line type="monotone" dataKey="replicaConnections" stroke="#e74c3c" name="Replica" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Query Performance */}
        <div className="metric-card">
          <h3><Activity className="card-icon" /> Query Performance</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="avgQueryTime" stroke="#f39c12" name="Avg Query Time (ms)" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Storage Usage */}
        <div className="metric-card">
          <h3><HardDrive className="card-icon" /> Storage Usage</h3>
          <div className="storage-info">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={storageUsageData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  dataKey="value"
                >
                  {storageUsageData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatBytes(value)} />
              </PieChart>
            </ResponsiveContainer>
            <div className="storage-details">
              <p>Total: {formatBytes(storageMetrics?.disk_usage?.total)}</p>
              <p>Used: {formatBytes(storageMetrics?.disk_usage?.used)}</p>
              <p>Free: {formatBytes(storageMetrics?.disk_usage?.free)}</p>
              <p>Usage: {storageMetrics?.disk_usage?.percent?.toFixed(1)}%</p>
            </div>
          </div>
        </div>

        {/* Database Metrics */}
        <div className="metric-card database-metrics">
          <h3><Database className="card-icon" /> Database Metrics</h3>
          <div className="db-metrics-grid">
            <div className="metric-item">
              <span className="metric-label">Database Size</span>
              <span className="metric-value">
                {formatBytes(clusterMetrics?.primary?.database_size_bytes)}
              </span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Total Queries</span>
              <span className="metric-value">
                {(clusterMetrics?.primary?.total_queries || 0).toLocaleString()}
              </span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Avg Query Time</span>
              <span className="metric-value">
                {(clusterMetrics?.primary?.avg_query_time_ms || 0).toFixed(2)}ms
              </span>
            </div>
          </div>
        </div>

        {/* Persistent Volumes */}
        <div className="metric-card pv-metrics">
          <h3><HardDrive className="card-icon" /> Persistent Volumes</h3>
          <div className="pv-list">
            {storageMetrics?.persistent_volumes?.map((pv, index) => (
              <div key={index} className="pv-item">
                <div className="pv-name">{pv.name}</div>
                <div className="pv-details">
                  <span>Capacity: {pv.capacity}</span>
                  <span>Class: {pv.storage_class}</span>
                  <span className={`pv-status ${pv.phase.toLowerCase()}`}>
                    {pv.phase}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="action-panel">
        <button className="action-button danger" onClick={testFailover}>
          Test Failover
        </button>
        <button className="action-button" onClick={fetchMetrics}>
          Refresh Metrics
        </button>
      </div>
    </div>
  );
}

export default App;
