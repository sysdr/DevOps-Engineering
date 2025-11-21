import React, { useState, useEffect } from 'react';

function DashboardList() {
  const [dashboards, setDashboards] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusMessage, setStatusMessage] = useState('');
  const [deployingTemplate, setDeployingTemplate] = useState(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [dashRes, tempRes] = await Promise.all([
        fetch('http://localhost:8001/api/dashboards'),
        fetch('http://localhost:8001/api/templates')
      ]);

      const dashData = await dashRes.json();
      const tempData = await tempRes.json();

      setDashboards(dashData.dashboards || []);
      setTemplates(tempData.templates || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  const openDashboard = (uid) => {
    window.open(`http://localhost:3000/d/${uid}`, '_blank');
  };

  const handleUseTemplate = async (template) => {
    setDeployingTemplate(template.filename);
    setStatusMessage('');
    try {
      const response = await fetch('http://localhost:8001/api/templates/deploy', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          filename: template.filename,
          title: template.title
        })
      });

      const data = await response.json();
      if (!response.ok || data.status === 'error') {
        throw new Error(data.detail || data.message || 'Failed to deploy template');
      }

      setStatusMessage(`Template "${template.title}" deployed successfully. Refresh Grafana to view demo data.`);
      fetchData();
    } catch (error) {
      console.error('Error deploying template:', error);
      setStatusMessage(`Failed to deploy template "${template.title}": ${error.message}`);
    } finally {
      setDeployingTemplate(null);
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboards...</div>;
  }

  return (
    <div className="dashboard-list">
      <section className="section">
        {statusMessage && <div className="status-banner">{statusMessage}</div>}
        <h2>Active Dashboards ({dashboards.length})</h2>
        <div className="card-grid">
          {dashboards.map((dash) => (
            <div key={dash.uid} className="card" onClick={() => openDashboard(dash.uid)}>
              <h3>{dash.title}</h3>
              <div className="tags">
                {dash.tags && dash.tags.map((tag, i) => (
                  <span key={i} className="tag">{tag}</span>
                ))}
              </div>
              <p className="meta">URI: {dash.uri}</p>
              <button className="btn-primary">Open in Grafana →</button>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <h2>Available Templates ({templates.length})</h2>
        <div className="card-grid">
          {templates.map((template, i) => (
            <div key={i} className="card template">
              <h3>{template.title}</h3>
              <div className="tags">
                {template.tags && template.tags.map((tag, i) => (
                  <span key={i} className="tag">{tag}</span>
                ))}
              </div>
              <p className="meta">File: {template.filename}</p>
              <button
                className="btn-secondary"
                onClick={() => handleUseTemplate(template)}
                disabled={deployingTemplate === template.filename}
              >
                {deployingTemplate === template.filename ? 'Deploying...' : 'Use Template'}
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default DashboardList;
