import React, { useState, useEffect } from 'react';

function AnomalyList() {
  const [anomalies, setAnomalies] = useState([]);

  useEffect(() => {
    fetchAnomalies();
    const interval = setInterval(fetchAnomalies, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchAnomalies = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/anomalies/recent?hours=24');
      const data = await response.json();
      setAnomalies(data.slice(0, 10));
    } catch (error) {
      console.error('Error fetching anomalies:', error);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      high: '#f44336',
      medium: '#ff9800',
      low: '#ffc107'
    };
    return colors[severity] || '#888';
  };

  return (
    <div className="anomaly-list">
      {anomalies.length === 0 ? (
        <div className="no-data">✅ No anomalies detected</div>
      ) : (
        anomalies.map(anomaly => (
          <div key={anomaly.id} className="anomaly-item">
            <div className="anomaly-header">
              <span 
                className="severity-badge" 
                style={{ background: getSeverityColor(anomaly.severity) }}
              >
                {anomaly.severity}
              </span>
              <span className="anomaly-time">
                {new Date(anomaly.detected_at).toLocaleTimeString()}
              </span>
            </div>
            <div className="anomaly-metric">{anomaly.metric_name}</div>
            <div className="anomaly-values">
              <span>Value: {anomaly.value.toFixed(2)}</span>
              <span>Expected: {anomaly.expected_value.toFixed(2)}</span>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default AnomalyList;
