import React from 'react';

const CDNDashboard = ({ metrics }) => {
  if (!metrics) {
    return <div className="loading">Loading CDN metrics...</div>;
  }

  const { edge_nodes, cost_metrics, cache_hit_rate, total_requests, recent_requests } = metrics;

  // Calculate derived metrics
  const totalCost = Object.values(edge_nodes).reduce((sum, node) => {
    return sum + Object.values(node.cached_items || {}).reduce((nodeSum, item) => {
      return nodeSum + (item.size * 0.01); // Simple cost calculation
    }, 0);
  }, 0);

  const avgResponseTime = recent_requests.length > 0 
    ? Math.round(recent_requests.reduce((sum, req) => sum + req.response_time, 0) / recent_requests.length)
    : 0;

  return (
    <div className="dashboard">
      <div className="overview-cards">
        <div className="metric-card">
          <h3>📨 Total Requests</h3>
          <div className="metric-value">{total_requests.toLocaleString()}</div>
        </div>
        <div className="metric-card">
          <h3>⚡ Cache Hit Rate</h3>
          <div className="metric-value">{cache_hit_rate.toFixed(1)}%</div>
        </div>
        <div className="metric-card">
          <h3>⏱️ Avg Response Time</h3>
          <div className="metric-value">{avgResponseTime}ms</div>
        </div>
        <div className="metric-card">
          <h3>💰 Total Cost</h3>
          <div className="metric-value">${totalCost.toFixed(2)}</div>
        </div>
      </div>

      <div className="regional-overview">
        <h2>🌍 Regional Performance</h2>
        <div className="regional-grid">
          {edge_nodes.map(node => {
            const nodeCost = Object.values(node.cached_items || {}).reduce((sum, item) => {
              return sum + (item.size * 0.01);
            }, 0);
            
            return (
              <div key={node.id} className="region-card">
                <h4>{node.region.toUpperCase()}</h4>
                <div className="region-stats">
                  <div className="stat">
                    <span className="label">Status:</span>
                    <span className="value">{node.status}</span>
                  </div>
                  <div className="stat">
                    <span className="label">Load:</span>
                    <span className="value">{node.current_load}/{node.capacity}</span>
                  </div>
                  <div className="stat">
                    <span className="label">Cache Items:</span>
                    <span className="value">{Object.keys(node.cached_items || {}).length}</span>
                  </div>
                  <div className="stat">
                    <span className="label">Cost:</span>
                    <span className="value">${nodeCost.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="cost-breakdown">
        <h2>💸 Cost Breakdown by Region</h2>
        <div className="cost-chart">
          {edge_nodes.map(node => {
            const nodeCost = Object.values(node.cached_items || {}).reduce((sum, item) => {
              return sum + (item.size * 0.01);
            }, 0);
            
            const maxCost = Math.max(...edge_nodes.map(n => 
              Object.values(n.cached_items || {}).reduce((sum, item) => sum + (item.size * 0.01), 0)
            ));
            
            return (
              <div key={node.id} className="cost-bar">
                <span className="region-name">{node.region}</span>
                <div className="bar-container">
                  <div 
                    className="cost-bar-fill" 
                    style={{ width: `${maxCost > 0 ? (nodeCost / maxCost) * 100 : 0}%` }}
                  ></div>
                </div>
                <span className="cost-value">${nodeCost.toFixed(2)}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default CDNDashboard;
