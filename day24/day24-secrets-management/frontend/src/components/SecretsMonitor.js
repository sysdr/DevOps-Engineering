import React, { useState, useEffect } from 'react';
import './SecretsMonitor.css';

function SecretsMonitor() {
  const [secretsData, setSecretsData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSecretsStatus();
    const interval = setInterval(fetchSecretsStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchSecretsStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/secrets-status');
      const data = await response.json();
      setSecretsData(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch secrets status:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading secrets status...</div>;
  }

  if (!secretsData) {
    return <div className="error">Failed to load secrets data</div>;
  }

  return (
    <div className="secrets-monitor">
      <div className="section-header">
        <h2>External Secrets Status</h2>
        <span className="sync-info">🔄 Auto-sync enabled</span>
      </div>

      <div className="secrets-summary">
        <div className="summary-item">
          <span className="summary-label">Total Managed Secrets</span>
          <span className="summary-value">{secretsData.total_secrets}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Sync Status</span>
          <span className="summary-value status-ok">✓ All Synced</span>
        </div>
      </div>

      <div className="secrets-grid">
        {secretsData.secrets.map((secret, index) => (
          <div key={index} className="secret-card">
            <div className="secret-header">
              <h3>{secret.name}</h3>
              <span className="sync-badge">✓ Synced</span>
            </div>
            <div className="secret-details">
              <div className="detail-row">
                <span className="detail-label">Namespace:</span>
                <span className="detail-value">{secret.namespace}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Type:</span>
                <span className="detail-value">
                  <span className="type-badge">{secret.type}</span>
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Source:</span>
                <span className="detail-value source-path">{secret.source}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Refresh Interval:</span>
                <span className="detail-value">{secret.refresh_interval}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Last Sync:</span>
                <span className="detail-value timestamp">
                  {new Date(secret.last_sync).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="info-panel">
        <h3>ℹ️ External Secrets Operator Info</h3>
        <ul>
          <li>Secrets are fetched from AWS Secrets Manager</li>
          <li>Automatic rotation every {secretsData.secrets[0]?.refresh_interval || '1h'}</li>
          <li>Kubernetes Secrets are automatically updated</li>
          <li>Applications are restarted on secret changes</li>
        </ul>
      </div>
    </div>
  );
}

export default SecretsMonitor;
