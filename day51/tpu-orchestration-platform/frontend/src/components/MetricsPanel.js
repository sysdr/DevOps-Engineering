import React from 'react';

function MetricsPanel({ metrics }) {
  const cluster = metrics.cluster || {};
  
  return (
    <div className="panel">
      <h2>Cluster Metrics</h2>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Total Utilization</div>
          <div className="metric-value">
            {cluster.total_utilization?.toFixed(1) || 0}%
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-label">Avg MXU Utilization</div>
          <div className="metric-value">
            {cluster.average_mxu?.toFixed(1) || 0}%
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-label">Total FLOPS</div>
          <div className="metric-value">
            {(cluster.total_flops / 1e12)?.toFixed(2) || 0} T
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-label">Active Jobs</div>
          <div className="metric-value">
            {metrics.jobs?.length || 0}
          </div>
        </div>
      </div>

      <div className="tpu-resources">
        <h3>TPU Resources</h3>
        <div className="resource-item">
          <span>v4-8 Pods:</span>
          <span>2 Available</span>
        </div>
        <div className="resource-item">
          <span>v4-32 Pods:</span>
          <span>2 Available</span>
        </div>
      </div>
    </div>
  );
}

export default MetricsPanel;
