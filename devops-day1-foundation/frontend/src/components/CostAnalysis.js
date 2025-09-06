import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const CostAnalysis = () => {
  const [costs, setCosts] = useState(null);

  useEffect(() => {
    const fetchCosts = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/aws/costs');
        const data = await response.json();
        setCosts(data);
      } catch (error) {
        console.error('Error fetching costs:', error);
      }
    };

    fetchCosts();
    const interval = setInterval(fetchCosts, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!costs) return <div className="loading">Loading cost data...</div>;

  const serviceData = Object.entries(costs.services).map(([name, data]) => ({
    name,
    cost: data.cost
  }));

  const teamData = Object.entries(costs.cost_by_team).map(([name, cost]) => ({
    name,
    cost
  }));

  const COLORS = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dda0dd', '#98d8c8'];

  return (
    <div className="cost-container">
      <div className="cost-summary">
        <h2>Total Monthly Cost: ${costs.total_cost}</h2>
        <p>Last updated: {new Date(costs.timestamp).toLocaleString()}</p>
      </div>
      
      <div className="cost-charts">
        <div className="chart-section">
          <h3>Cost by AWS Service</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={serviceData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, cost }) => `${name}: $${cost}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="cost"
              >
                {serviceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `$${value}`} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        
        <div className="chart-section">
          <h3>Cost by Team</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={teamData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => `$${value}`} />
              <Bar dataKey="cost" fill="#4ecdc4" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <div className="service-details">
        <h3>Service Details</h3>
        <div className="service-grid">
          {Object.entries(costs.services).map(([service, details]) => (
            <div key={service} className="service-card">
              <h4>{service}</h4>
              <div className="service-cost">${details.cost}</div>
              <div className="service-meta">
                {details.instances && <span>Instances: {details.instances}</span>}
                {details.storage_gb && <span>Storage: {details.storage_gb}GB</span>}
                {details.requests && <span>Requests: {details.requests.toLocaleString()}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CostAnalysis;
