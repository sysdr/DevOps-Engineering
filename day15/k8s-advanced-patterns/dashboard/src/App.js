import React, { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';
import axios from 'axios';
import './App.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, ArcElement);

function App() {
  const [metrics, setMetrics] = useState({
    webapps: [],
    totalCreated: 0,
    totalDeleted: 0,
    currentWebApps: 0,
    reconciliations: 0
  });
  const [resourceUsage, setResourceUsage] = useState({
    cpuUsage: 0,
    memoryUsage: 0,
    podCount: 0
  });

  useEffect(() => {
    fetchMetrics();
    fetchResourceUsage();
    const interval = setInterval(() => {
      fetchMetrics();
      fetchResourceUsage();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await axios.get('/api/metrics');
      setMetrics(response.data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
      // Mock data for demonstration
      setMetrics({
        webapps: [
          { name: 'demo-app', replicas: 3, status: 'Running', zone: 'us-west-2a' },
          { name: 'test-app', replicas: 2, status: 'Running', zone: 'us-west-2b' }
        ],
        totalCreated: 15,
        totalDeleted: 3,
        currentWebApps: 12,
        reconciliations: 47
      });
    }
  };

  const fetchResourceUsage = async () => {
    try {
      const response = await axios.get('/api/resources');
      setResourceUsage(response.data);
    } catch (error) {
      console.error('Error fetching resource usage:', error);
      // Mock data
      setResourceUsage({
        cpuUsage: 65,
        memoryUsage: 73,
        podCount: 24
      });
    }
  };

  const lineChartData = {
    labels: ['1m', '2m', '3m', '4m', '5m'],
    datasets: [
      {
        label: 'Reconciliations/min',
        data: [5, 8, 6, 9, 7],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4
      }
    ]
  };

  const doughnutData = {
    labels: ['Running', 'Pending', 'Failed'],
    datasets: [
      {
        data: [metrics.currentWebApps, 2, 1],
        backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
        borderWidth: 0
      }
    ]
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🚀 WebApp Operator Dashboard</h1>
        <div className="status-indicator">
          <span className="status-dot active"></span>
          Operator Active
        </div>
      </header>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-value">{metrics.currentWebApps}</div>
          <div className="metric-label">Active WebApps</div>
          <div className="metric-trend">+{metrics.totalCreated - metrics.totalDeleted} today</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value">{metrics.reconciliations}</div>
          <div className="metric-label">Reconciliations</div>
          <div className="metric-trend">Last 24h</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value">{resourceUsage.cpuUsage}%</div>
          <div className="metric-label">CPU Usage</div>
          <div className="metric-trend">Cluster average</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value">{resourceUsage.memoryUsage}%</div>
          <div className="metric-label">Memory Usage</div>
          <div className="metric-trend">Cluster average</div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-container">
          <h3>Reconciliation Activity</h3>
          <Line data={lineChartData} options={{ responsive: true, maintainAspectRatio: false }} />
        </div>
        
        <div className="chart-container">
          <h3>WebApp Status Distribution</h3>
          <Doughnut data={doughnutData} options={{ responsive: true, maintainAspectRatio: false }} />
        </div>
      </div>

      <div className="webapps-table">
        <h3>Active WebApps</h3>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Replicas</th>
              <th>Status</th>
              <th>Zone</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {metrics.webapps.map((webapp, index) => (
              <tr key={index}>
                <td>{webapp.name}</td>
                <td>{webapp.replicas}</td>
                <td><span className={`status ${webapp.status.toLowerCase()}`}>{webapp.status}</span></td>
                <td>{webapp.zone}</td>
                <td>
                  <button className="action-btn">Scale</button>
                  <button className="action-btn danger">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default App;
