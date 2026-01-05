import React, { useState, useEffect } from 'react';

function IncidentManager() {
  const [incidents, setIncidents] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    fetchIncidents();
    // Auto-generate demo incidents if none exist
    const timer = setTimeout(async () => {
      try {
        const response = await fetch('http://localhost:8003/incidents');
        const data = await response.json();
        if (data.length === 0) {
          generateSampleAlerts();
        }
      } catch (error) {
        console.error('Failed to check incidents:', error);
      }
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  const fetchIncidents = async () => {
    try {
      const response = await fetch('http://localhost:8003/incidents');
      const data = await response.json();
      setIncidents(data);
    } catch (error) {
      console.error('Failed to fetch incidents:', error);
    }
  };

  const generateSampleAlerts = async () => {
    setIsGenerating(true);
    
    const alertSets = [
      {
        alerts: [
          { severity: 'CRITICAL', source: 'api-server', message: 'High CPU usage: 95%' },
          { severity: 'HIGH', source: 'api-server', message: 'Memory pressure detected' },
          { severity: 'MEDIUM', source: 'monitor', message: 'Increased latency: 850ms' }
        ]
      },
      {
        alerts: [
          { severity: 'HIGH', source: 'database', message: 'Connection pool exhausted' },
          { severity: 'HIGH', source: 'database', message: 'Query timeout: 30s exceeded' },
          { severity: 'MEDIUM', source: 'cache', message: 'Cache miss rate: 75%' }
        ]
      }
    ];

    for (const set of alertSets) {
      for (const alertData of set.alerts) {
        const alert = {
          id: Math.random().toString(36).substr(2, 9),
          timestamp: new Date().toISOString(),
          ...alertData,
          metadata: {}
        };

        try {
          await fetch('http://localhost:8003/alert', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(alert)
          });
          await new Promise(resolve => setTimeout(resolve, 500));
        } catch (error) {
          console.error('Failed to send alert:', error);
        }
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    setTimeout(() => {
      fetchIncidents();
      setIsGenerating(false);
    }, 2000);
  };

  return (
    <div className="panel">
      <h2>🚨 AI Incident Manager</h2>
      <p style={{ color: '#718096', marginBottom: '1rem' }}>
        Intelligent alert correlation and root cause analysis
      </p>

      <button
        className="primary"
        onClick={generateSampleAlerts}
        disabled={isGenerating}
      >
        {isGenerating ? 'Generating Incidents...' : 'Generate Sample Incidents'}
      </button>

      {incidents.length === 0 ? (
        <div style={{
          marginTop: '2rem',
          padding: '2rem',
          textAlign: 'center',
          background: '#f7fafc',
          borderRadius: '8px'
        }}>
          <p style={{ color: '#718096' }}>
            No active incidents. Click the button above to generate sample incidents.
          </p>
        </div>
      ) : (
        <div style={{ marginTop: '2rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>
            Active Incidents ({incidents.length})
          </h3>
          {incidents.map((incident) => (
            <div key={incident.id} className="incident-card">
              <div className="incident-header">
                <div>
                  <span className="incident-id">#{incident.id}</span>
                  <p style={{ color: '#718096', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                    Created: {new Date(incident.created_at).toLocaleString()}
                  </p>
                </div>
                <span className="status-badge">{incident.status.toUpperCase()}</span>
              </div>

              {incident.root_cause && (
                <div style={{
                  padding: '1rem',
                  background: '#fff5f5',
                  borderRadius: '6px',
                  marginBottom: '1rem'
                }}>
                  <strong style={{ color: '#fc8181' }}>🎯 Root Cause:</strong>
                  <p style={{ marginTop: '0.5rem', color: '#2d3748' }}>
                    {incident.root_cause}
                  </p>
                </div>
              )}

              <div style={{
                padding: '1rem',
                background: '#f0fff4',
                borderRadius: '6px',
                marginBottom: '1rem'
              }}>
                <strong style={{ color: '#38a169' }}>💡 Suggested Resolution:</strong>
                <p style={{ marginTop: '0.5rem', color: '#2d3748' }}>
                  {incident.suggested_resolution}
                </p>
                <p style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#718096' }}>
                  Confidence: {(incident.confidence * 100).toFixed(0)}%
                </p>
              </div>

              <div>
                <strong>Correlated Alerts ({incident.alerts.length}):</strong>
                <div className="alert-list">
                  {incident.alerts.map((alert, idx) => (
                    <div key={idx} className="alert-item">
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                        <span style={{ fontWeight: '600' }}>{alert.source}</span>
                        <span className={`severity-badge ${alert.severity}`}>
                          {alert.severity}
                        </span>
                      </div>
                      <p style={{ fontSize: '0.9rem', color: '#4a5568' }}>
                        {alert.message}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default IncidentManager;
