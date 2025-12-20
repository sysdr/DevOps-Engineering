import React from 'react';
import './PipelineStatus.css';

function PipelineStatus({ data }) {
  if (!data) {
    return <div className="pipeline-status-card">Loading...</div>;
  }
  
  const { 
    ingestion = { 
      status: 'idle', 
      total_users: 0, 
      total_purchases: 0, 
      avg_amount: 0, 
      last_run: 'N/A' 
    }, 
    streaming = { 
      status: 'unknown', 
      kafka_topics: [] 
    } 
  } = data;
  
  const formatDate = (dateStr) => {
    if (!dateStr || dateStr === 'N/A') return 'N/A';
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };
  
  return (
    <div className="pipeline-status-card">
      <h2>Pipeline Status</h2>
      
      <div className="pipeline-section">
        <h3>📥 Data Ingestion</h3>
        <div className="status-details">
          <div className="status-row">
            <span>Status:</span>
            <span className={`badge ${ingestion.status || 'idle'}`}>{ingestion.status || 'idle'}</span>
          </div>
          <div className="status-row">
            <span>Total Users:</span>
            <strong>{(ingestion.total_users || 0).toLocaleString()}</strong>
          </div>
          <div className="status-row">
            <span>Total Purchases:</span>
            <strong>{(ingestion.total_purchases || 0).toLocaleString()}</strong>
          </div>
          <div className="status-row">
            <span>Avg Amount:</span>
            <strong>${(ingestion.avg_amount || 0).toFixed(2)}</strong>
          </div>
          <div className="status-row">
            <span>Last Run:</span>
            <small>{formatDate(ingestion.last_run)}</small>
          </div>
        </div>
      </div>
      
      <div className="pipeline-section">
        <h3>⚡ Stream Processing</h3>
        <div className="status-details">
          <div className="status-row">
            <span>Status:</span>
            <span className={`badge ${streaming.status || 'unknown'}`}>{streaming.status || 'unknown'}</span>
          </div>
          <div className="kafka-topics">
            <span>Kafka Topics:</span>
            <ul>
              {(streaming.kafka_topics || []).map((topic, idx) => (
                <li key={idx}>{topic}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PipelineStatus;
