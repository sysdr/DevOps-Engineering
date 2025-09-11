import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import './App.css';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000';

function App() {
  const [clusterInfo, setClusterInfo] = useState(null);
  const [autoscalingStatus, setAutoscalingStatus] = useState(null);
  const [networkPolicies, setNetworkPolicies] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const fetchData = async () => {
    try {
      const [clusterRes, autoscalingRes, networkRes] = await Promise.all([
        axios.get(`${API_BASE}/api/cluster/info`),
        axios.get(`${API_BASE}/api/autoscaling/status`),
        axios.get(`${API_BASE}/api/network/policies`)
      ]);

      setClusterInfo(clusterRes.data);
      setAutoscalingStatus(autoscalingRes.data);
      setNetworkPolicies(networkRes.data);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300'];

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading Kubernetes Dashboard...</p>
      </div>
    );
  }

  const podStatusData = clusterInfo ? [
    { name: 'Running', value: clusterInfo.pods.running, fill: '#82ca9d' },
    { name: 'Pending', value: clusterInfo.pods.pending, fill: '#ffc658' },
    { name: 'Failed', value: clusterInfo.pods.failed, fill: '#ff7300' }
  ] : [];

  const nodeData = clusterInfo ? clusterInfo.nodes.details.map(node => ({
    name: node.name.substring(0, 12) + '...',
    cpu: parseInt(node.capacity.cpu),
    memory: Math.round(parseInt(node.capacity.memory.replace('Ki', '')) / 1024 / 1024),
    ready: node.ready ? 1 : 0
  })) : [];

  return (
    <div className="App">
      <header className="header">
        <h1>🚀 Kubernetes Production Dashboard</h1>
        <div className="last-update">
          Last updated: {lastUpdate.toLocaleTimeString()}
        </div>
      </header>

      <div className="dashboard">
        <div className="metrics-row">
          <div className="metric-card">
            <h3>Cluster Status</h3>
            <div className="metric-value">{clusterInfo?.nodes.ready}/{clusterInfo?.nodes.total}</div>
            <div className="metric-label">Nodes Ready</div>
          </div>
          <div className="metric-card">
            <h3>Pod Health</h3>
            <div className="metric-value">{clusterInfo?.pods.running}</div>
            <div className="metric-label">Pods Running</div>
          </div>
          <div className="metric-card">
            <h3>Namespaces</h3>
            <div className="metric-value">{clusterInfo?.namespaces}</div>
            <div className="metric-label">Total Namespaces</div>
          </div>
          <div className="metric-card">
            <h3>Network Policies</h3>
            <div className="metric-value">{networkPolicies?.total || 0}</div>
            <div className="metric-label">Active Policies</div>
          </div>
        </div>

        <div className="charts-row">
          <div className="chart-card">
            <h3>Pod Status Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={podStatusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {podStatusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <h3>Node Resource Capacity</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={nodeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="cpu" fill="#8884d8" name="CPU Cores" />
                <Bar dataKey="memory" fill="#82ca9d" name="Memory (GB)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="info-row">
          <div className="info-card">
            <h3>Autoscaling Status</h3>
            {autoscalingStatus?.hpas.length > 0 ? (
              <div className="hpa-list">
                {autoscalingStatus.hpas.map((hpa, index) => (
                  <div key={index} className="hpa-item">
                    <strong>{hpa.name}</strong> ({hpa.namespace})
                    <br />
                    Current: {hpa.current_replicas} | Desired: {hpa.desired_replicas}
                    <br />
                    Range: {hpa.min_replicas}-{hpa.max_replicas}
                  </div>
                ))}
              </div>
            ) : (
              <p>No HPAs configured</p>
            )}
          </div>

          <div className="info-card">
            <h3>Network Security</h3>
            {networkPolicies?.policies.length > 0 ? (
              <div className="policy-list">
                {networkPolicies.policies.slice(0, 5).map((policy, index) => (
                  <div key={index} className="policy-item">
                    <strong>{policy.name}</strong> ({policy.namespace})
                    <br />
                    Ingress: {policy.ingress_rules} | Egress: {policy.egress_rules}
                  </div>
                ))}
              </div>
            ) : (
              <p>No network policies found</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
