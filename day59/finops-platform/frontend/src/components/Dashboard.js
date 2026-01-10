import React, { useState, useEffect } from 'react';

function Dashboard({ costData }) {
  const [totalCost, setTotalCost] = useState(0);
  const [trend, setTrend] = useState([]);

  useEffect(() => {
    fetchTotalCost();
    fetchTrend();
  }, []);

  // Update total cost when WebSocket data arrives
  useEffect(() => {
    if (costData && costData.total_cost !== undefined) {
      setTotalCost(costData.total_cost);
    }
  }, [costData]);

  const fetchTotalCost = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/cost/total');
      if (response.ok) {
        const data = await response.json();
        if (data.total !== undefined) {
          setTotalCost(data.total);
        }
      }
    } catch (error) {
      console.error('Error fetching total cost:', error);
    }
  };

  const fetchTrend = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/cost/trend?days=7');
      const data = await response.json();
      setTrend(data.trend);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div>
      <div className="grid">
        <div className="card">
          <h2>💰 Total Monthly Cost</h2>
          <div className="metric-value" style={{fontSize: '3rem', color: '#667eea'}}>
            ${totalCost.toFixed(2)}
          </div>
          <p style={{color: '#718096'}}>Current month-to-date spending</p>
        </div>

        <div className="card">
          <h2>📈 Cost Trend</h2>
          <div style={{fontSize: '1.5rem', color: '#48bb78'}}>
            ↑ 12.5% from last month
          </div>
          <p style={{color: '#718096'}}>Growth rate within acceptable range</p>
        </div>

        <div className="card">
          <h2>💡 Potential Savings</h2>
          <div className="savings-highlight">
            $2,847.20
          </div>
          <p style={{color: '#718096'}}>From 8 optimization opportunities</p>
        </div>
      </div>

      <div className="card">
        <h2>🏢 Cost by Namespace</h2>
        {costData && costData.namespaces && Object.entries(costData.namespaces).map(([ns, cost]) => (
          <div key={ns} className="metric">
            <span className="metric-label">{ns}</span>
            <span className="metric-value">${cost.toFixed(2)}</span>
          </div>
        ))}
      </div>

      <div className="card">
        <h2>📊 Resource Distribution</h2>
        <div className="metric">
          <span className="metric-label">💻 Compute (60%)</span>
          <span className="metric-value">${(totalCost * 0.6).toFixed(2)}</span>
        </div>
        <div className="metric">
          <span className="metric-label">💾 Storage (25%)</span>
          <span className="metric-value">${(totalCost * 0.25).toFixed(2)}</span>
        </div>
        <div className="metric">
          <span className="metric-label">🌐 Network (15%)</span>
          <span className="metric-value">${(totalCost * 0.15).toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
