import React, { useState, useEffect } from 'react';
import './DriftMonitor.css';

function DriftMonitor() {
  const [driftData, setDriftData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    fetchDriftStatus();
    const interval = setInterval(fetchDriftStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchDriftStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/drift-status');
      const data = await response.json();
      setDriftData(data);
      setLastUpdate(new Date().toLocaleTimeString());
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch drift status:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading drift status...</div>;
  }

  if (!driftData) {
    return <div className="error">Failed to load drift data</div>;
  }

  const { summary, results } = driftData;

  return (
    <div className="drift-monitor">
      <div className="section-header">
        <h2>Configuration Drift Detection</h2>
        <span className="last-update">Last updated: {lastUpdate}</span>
      </div>

      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-icon">📊</div>
          <div className="card-content">
            <div className="card-value">{summary.total_resources}</div>
            <div className="card-label">Total Resources</div>
          </div>
        </div>

        <div className="summary-card drift">
          <div className="card-icon">⚠️</div>
          <div className="card-content">
            <div className="card-value">{summary.drifted_resources}</div>
            <div className="card-label">Drifted Resources</div>
          </div>
        </div>

        <div className="summary-card remediate">
          <div className="card-icon">🔄</div>
          <div className="card-content">
            <div className="card-value">{summary.auto_remediation_enabled}</div>
            <div className="card-label">Auto-Remediate Enabled</div>
          </div>
        </div>

        <div className="summary-card percentage">
          <div className="card-icon">📈</div>
          <div className="card-content">
            <div className="card-value">{summary.drift_percentage}%</div>
            <div className="card-label">Drift Percentage</div>
          </div>
        </div>
      </div>

      <div className="resources-table">
        <h3>Resource Status Details</h3>
        <table>
          <thead>
            <tr>
              <th>Resource</th>
              <th>Kind</th>
              <th>Namespace</th>
              <th>Status</th>
              <th>Drift Details</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {results.map((result, index) => (
              <tr key={index} className={result.drift_detected ? 'drifted' : ''}>
                <td>{result.resource_name}</td>
                <td><span className="kind-badge">{result.resource_kind}</span></td>
                <td>{result.namespace}</td>
                <td>
                  <span className={`status-indicator ${result.drift_detected ? 'drift' : 'synced'}`}>
                    {result.drift_detected ? '⚠️ Drifted' : '✓ Synced'}
                  </span>
                </td>
                <td className="diff-summary">
                  {result.drift_detected ? result.diff_summary : 'No drift detected'}
                </td>
                <td>
                  {result.drift_detected && (
                    <span className={`action-badge ${result.remediation_action}`}>
                      {result.remediation_action === 'auto-remediate' ? '🔄 Auto' : '👁️ Alert'}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default DriftMonitor;
