import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Panel.css';

function FairnessPanel() {
  const [fairness, setFairness] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadFairness();
    loadAlerts();
    const interval = setInterval(() => {
      loadFairness();
      loadAlerts();
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadFairness = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8004/fairness/current');
      setFairness(response.data);
    } catch (error) {
      console.error('Error loading fairness:', error);
    }
    setLoading(false);
  };

  const loadAlerts = async () => {
    try {
      const response = await axios.get('http://localhost:8004/fairness/alerts');
      setAlerts(response.data);
    } catch (error) {
      console.error('Error loading alerts:', error);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>⚖️ Fairness Monitoring</h2>
        <button onClick={() => { loadFairness(); loadAlerts(); }} className="action-button" disabled={loading}>
          {loading ? 'Loading...' : 'Refresh Analysis'}
        </button>
      </div>

      {alerts.length > 0 && (
        <div className="alert error">
          ⚠️ {alerts.length} fairness alert(s) detected in the last 24 hours
        </div>
      )}

      {fairness?.metrics && (
        <div className="fairness-metrics">
          {Object.entries(fairness.metrics).map(([key, data]) => (
            <div key={key} className="fairness-card">
              <h3>{key.replace(/_/g, ' ').toUpperCase()}</h3>
              
              {data.disparity !== undefined && (
                <div className="disparity-indicator">
                  <span>Disparity:</span>
                  <strong className={data.disparity > 0.1 ? 'high' : 'normal'}>
                    {(data.disparity * 100).toFixed(2)}%
                  </strong>
                </div>
              )}

              {data.groups && (
                <div className="groups-breakdown">
                  <h4>Groups:</h4>
                  {Object.entries(data.groups).map(([group, value]) => (
                    <div key={group} className="group-metric">
                      <span>{group}:</span>
                      <span>
                        {typeof value === 'object' 
                          ? `TPR: ${(value.tpr * 100).toFixed(1)}%, FPR: ${(value.fpr * 100).toFixed(1)}%`
                          : `${(value * 100).toFixed(1)}%`
                        }
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="info-section">
        <h3>Fairness Metrics</h3>
        <p><strong>Demographic Parity:</strong> Measures equal approval rates across groups</p>
        <p><strong>Equalized Odds:</strong> Ensures equal TPR and FPR across groups</p>
        <p><strong>Threshold:</strong> Alerts trigger when disparity exceeds 10%</p>
      </div>
    </div>
  );
}

export default FairnessPanel;
