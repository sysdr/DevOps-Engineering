import React, { useState, useEffect } from 'react';

function CostBreakdown() {
  const [breakdown, setBreakdown] = useState(null);

  useEffect(() => {
    fetchBreakdown();
  }, []);

  const fetchBreakdown = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/cost/breakdown');
      const data = await response.json();
      setBreakdown(data);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  if (!breakdown) {
    return <div className="card">Loading breakdown...</div>;
  }

  return (
    <div>
      <div className="card">
        <h2>💰 Detailed Cost Breakdown</h2>
        
        <div style={{marginTop: '2rem'}}>
          <h3>Compute Resources</h3>
          <div className="metric">
            <span className="metric-label">Total Compute Cost</span>
            <span className="metric-value">${breakdown.compute.toFixed(2)}</span>
          </div>
          <div style={{marginLeft: '1rem', color: '#718096'}}>
            <p>• Instance hours: 8,750 hrs</p>
            <p>• Average utilization: 67%</p>
            <p>• Reserved instances: 45%</p>
          </div>
        </div>

        <div style={{marginTop: '2rem'}}>
          <h3>Storage Resources</h3>
          <div className="metric">
            <span className="metric-label">Total Storage Cost</span>
            <span className="metric-value">${breakdown.storage.toFixed(2)}</span>
          </div>
          <div style={{marginLeft: '1rem', color: '#718096'}}>
            <p>• Block storage: 15 TB</p>
            <p>• Object storage: 42 TB</p>
            <p>• Snapshots: 8 TB</p>
          </div>
        </div>

        <div style={{marginTop: '2rem'}}>
          <h3>Network Resources</h3>
          <div className="metric">
            <span className="metric-label">Total Network Cost</span>
            <span className="metric-value">${breakdown.network.toFixed(2)}</span>
          </div>
          <div style={{marginLeft: '1rem', color: '#718096'}}>
            <p>• Data transfer out: 125 TB</p>
            <p>• Inter-AZ transfer: 45 TB</p>
            <p>• Load balancer: $235/month</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CostBreakdown;
