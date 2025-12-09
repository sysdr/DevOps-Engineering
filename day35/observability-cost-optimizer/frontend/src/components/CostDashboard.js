import React, { useState, useEffect } from 'react';

function CostDashboard({ realtimeData }) {
  const [costBreakdown, setCostBreakdown] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCostBreakdown();
    const interval = setInterval(fetchCostBreakdown, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchCostBreakdown = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/costs/breakdown');
      const data = await response.json();
      setCostBreakdown(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching cost breakdown:', error);
    }
  };

  if (loading) return <div className="loading">Loading cost data...</div>;

  const totalCost = costBreakdown?.total_monthly_cost || 0;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Cost Breakdown by Service</h2>
        <div className="total-cost">
          <span className="cost-label">Total Monthly Cost</span>
          <span className="cost-value">${totalCost.toFixed(2)}</span>
        </div>
      </div>

      <div className="cost-summary">
        {costBreakdown?.services.map((service, index) => {
          const percentage = totalCost > 0 ? (service.total / totalCost) * 100 : 0;
          
          return (
            <div key={index} className="service-card">
              <div className="service-header">
                <h3>{service.service}</h3>
                <span className="service-total">${service.total.toFixed(2)}/mo</span>
              </div>
              
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${percentage}%` }}
                ></div>
              </div>
              
              <div className="cost-details">
                <div className="cost-item">
                  <span>Metrics:</span>
                  <span>${service.metrics.toFixed(2)}</span>
                </div>
                <div className="cost-item">
                  <span>Traces:</span>
                  <span>${service.traces.toFixed(2)}</span>
                </div>
                <div className="cost-item">
                  <span>Logs:</span>
                  <span>${service.logs.toFixed(2)}</span>
                </div>
                <div className="cost-item">
                  <span>Storage:</span>
                  <span>${service.storage.toFixed(2)}</span>
                </div>
                <div className="cost-item">
                  <span>Alerts:</span>
                  <span>${service.alerts.toFixed(2)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {realtimeData && (
        <div className="realtime-update">
          <div className="update-badge">New Update</div>
          <p>{realtimeData.type}: {JSON.stringify(realtimeData.data, null, 2)}</p>
        </div>
      )}
    </div>
  );
}

export default CostDashboard;
