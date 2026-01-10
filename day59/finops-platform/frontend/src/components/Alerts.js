import React, { useState, useEffect } from 'react';

function Alerts() {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/alerts/');
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const acknowledgeAlert = async (alertId) => {
    try {
      await fetch(`http://localhost:8000/api/v1/alerts/acknowledge/${alertId}`, {
        method: 'POST'
      });
      fetchAlerts();
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div>
      <div className="card">
        <h2>🚨 Cost Anomaly Alerts</h2>
        
        {alerts.length === 0 ? (
          <div style={{
            padding: '3rem 2rem', 
            textAlign: 'center', 
            color: '#48bb78'
          }}>
            <div style={{fontSize: '4rem', marginBottom: '1rem', lineHeight: '1'}}>✅</div>
            <p style={{
              fontSize: '1.5rem', 
              fontWeight: '600', 
              color: '#2d3748',
              marginBottom: '0.5rem'
            }}>
              No active alerts
            </p>
            <p style={{
              fontSize: '1rem',
              color: '#718096',
              margin: 0
            }}>
              All costs are within expected ranges
            </p>
          </div>
        ) : (
          <div>
            {alerts.map((alert) => (
              <div 
                key={alert.id} 
                style={{
                  padding: '1rem',
                  margin: '1rem 0',
                  background: alert.severity === 'critical' ? '#fed7d7' : '#feebc8',
                  borderLeft: `4px solid ${alert.severity === 'critical' ? '#e53e3e' : '#ed8936'}`,
                  borderRadius: '8px'
                }}
              >
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'start'}}>
                  <div style={{flex: 1}}>
                    <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                      <span className={`status-badge ${alert.severity}`}>
                        {alert.severity.toUpperCase()}
                      </span>
                      <span style={{fontWeight: '600'}}>{alert.namespace}</span>
                    </div>
                    
                    <p style={{margin: '0.5rem 0', fontWeight: '600', color: '#2d3748'}}>
                      Cost Spike Detected
                    </p>
                    
                    <div style={{color: '#4a5568', fontSize: '0.875rem'}}>
                      <p>Baseline: ${alert.baseline_cost.toFixed(2)}</p>
                      <p>Current: ${alert.current_cost.toFixed(2)}</p>
                      <p>Deviation: +{alert.deviation_percent.toFixed(1)}%</p>
                    </div>
                    
                    <p style={{marginTop: '0.5rem', color: '#718096'}}>
                      {alert.reason}
                    </p>
                    
                    <p style={{fontSize: '0.75rem', color: '#a0aec0', marginTop: '0.5rem'}}>
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                  </div>
                  
                  <button
                    onClick={() => acknowledgeAlert(alert.id)}
                    style={{
                      padding: '0.5rem 1rem',
                      background: '#667eea',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontWeight: '600'
                    }}
                  >
                    Acknowledge
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Alerts;
