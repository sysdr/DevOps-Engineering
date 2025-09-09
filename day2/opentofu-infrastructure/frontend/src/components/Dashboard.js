import React from 'react';

const Dashboard = ({ status }) => {
  const totalEnvs = status?.total_environments || 0;
  const healthyEnvs = status?.healthy_environments || 0;
  const unhealthyEnvs = totalEnvs - healthyEnvs;

  return (
    <div className="dashboard">
      <h2>Infrastructure Overview</h2>
      <div className="dashboard-metrics">
        <div className="metric-card">
          <div className="metric-value">{totalEnvs}</div>
          <div className="metric-label">Total Environments</div>
        </div>
        <div className="metric-card healthy">
          <div className="metric-value">{healthyEnvs}</div>
          <div className="metric-label">Healthy</div>
        </div>
        <div className="metric-card warning">
          <div className="metric-value">{unhealthyEnvs}</div>
          <div className="metric-label">Needs Attention</div>
        </div>
        <div className="metric-card info">
          <div className="metric-value">4</div>
          <div className="metric-label">Available Modules</div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
