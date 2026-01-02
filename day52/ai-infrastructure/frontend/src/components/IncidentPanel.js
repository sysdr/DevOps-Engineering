import React, { useState, useEffect } from 'react';

function IncidentPanel() {
  const [incidents, setIncidents] = useState([]);

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 20000);
    return () => clearInterval(interval);
  }, []);

  const fetchIncidents = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/incidents/recent?hours=24');
      const data = await response.json();
      setIncidents(data.slice(0, 5));
    } catch (error) {
      console.error('Error fetching incidents:', error);
    }
  };

  return (
    <div className="incident-panel">
      {incidents.length === 0 ? (
        <div className="no-data">✅ No active incidents</div>
      ) : (
        incidents.map(incident => (
          <div key={incident.id} className="incident-item">
            <div className="incident-header">
              <span className="incident-id">#{incident.id}</span>
              <span className={`incident-status ${incident.status}`}>
                {incident.status}
              </span>
            </div>
            <div className="incident-title">{incident.title}</div>
            <div className="incident-cause">{incident.root_cause}</div>
            <div className="incident-time">
              {new Date(incident.created_at).toLocaleString()}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default IncidentPanel;
