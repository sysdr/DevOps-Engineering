import React, { useState } from 'react';

function ActionsPanel({ onRefresh }) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleAction = async (action, data) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/${action}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
      });
      
      const result = await response.json();
      setMessage(`✅ ${action} completed successfully`);
      onRefresh();
    } catch (error) {
      setMessage(`❌ ${action} failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="actions-panel">
      <h2>Security Actions</h2>
      
      <div className="action-buttons">
        <button 
          onClick={() => handleAction('sign', {image: 'nginx', tag: 'latest'})}
          disabled={loading}
          className="action-btn sign"
        >
          🔏 Sign nginx:latest
        </button>
        
        <button 
          onClick={() => handleAction('scan', {image: 'nginx:latest'})}
          disabled={loading}
          className="action-btn scan"
        >
          🔍 Scan nginx:latest
        </button>
        
        <button 
          onClick={() => handleAction('policy/evaluate', {image: 'nginx:latest'})}
          disabled={loading}
          className="action-btn policy"
        >
          📋 Evaluate Policy
        </button>
        
        <button 
          onClick={() => handleAction('promote', {source_image: 'nginx:latest', target_env: 'production'})}
          disabled={loading}
          className="action-btn promote"
        >
          🚀 Promote to Prod
        </button>
      </div>
      
      {loading && <div className="loading">Processing...</div>}
      {message && <div className="message">{message}</div>}
    </div>
  );
}

export default ActionsPanel;
