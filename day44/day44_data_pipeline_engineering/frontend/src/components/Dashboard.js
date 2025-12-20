import React from 'react';
import './Dashboard.css';

function Dashboard({ data }) {
  if (!data) {
    return <div className="dashboard">Loading...</div>;
  }
  
  const { 
    ingestion = { total_records: 0 }, 
    validation = { score: 0, passed_checks: 0, total_checks: 0 }, 
    versioning = { latest_version: 'N/A', total_versions: 0 }, 
    streaming = { status: 'unknown', kafka_topics: [] } 
  } = data;
  
  return (
    <div className="dashboard">
      <div className="stats-grid">
        <div className="stat-card primary">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <h3>Total Records</h3>
            <p className="stat-value">{(ingestion.total_records || 0).toLocaleString()}</p>
            <span className="stat-label">Processed</span>
          </div>
        </div>
        
        <div className="stat-card success">
          <div className="stat-icon">✓</div>
          <div className="stat-content">
            <h3>Validation Score</h3>
            <p className="stat-value">{(validation.score || 0).toFixed(1)}%</p>
            <span className="stat-label">{(validation.passed_checks || 0)}/{(validation.total_checks || 0)} Checks</span>
          </div>
        </div>
        
        <div className="stat-card info">
          <div className="stat-icon">📦</div>
          <div className="stat-content">
            <h3>Dataset Version</h3>
            <p className="stat-value">{versioning.latest_version || 'N/A'}</p>
            <span className="stat-label">{(versioning.total_versions || 0)} Versions Total</span>
          </div>
        </div>
        
        <div className="stat-card warning">
          <div className="stat-icon">⚡</div>
          <div className="stat-content">
            <h3>Streaming</h3>
            <p className="stat-value">{streaming.status || 'unknown'}</p>
            <span className="stat-label">{(streaming.kafka_topics || []).length} Topics Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
