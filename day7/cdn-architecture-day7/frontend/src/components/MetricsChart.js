import React from 'react';

const MetricsChart = ({ metrics }) => {
  if (!metrics) {
    return <div className="loading">Loading analytics...</div>;
  }

  const { recent_requests, edge_nodes, cache_hit_rate, total_requests } = metrics;
  
  // Calculate trends from recent requests
  const recentData = recent_requests.slice(-20);
  const avgResponseTime = recentData.length > 0 
    ? recentData.reduce((sum, item) => sum + item.response_time, 0) / recentData.length
    : 0;
  const actualCacheHitRate = recentData.length > 0 
    ? (recentData.filter(item => item.cache_hit).length / recentData.length) * 100
    : 0;

  return (
    <div className="metrics-analytics">
      <h2>📈 Performance Analytics</h2>
      
      <div className="analytics-overview">
        <div className="trend-card">
          <h3>⚡ Response Time Trend</h3>
          <div className="trend-value">{Math.round(avgResponseTime)}ms</div>
          <div className="trend-indicator">
            {avgResponseTime < 100 ? '📈 Excellent' : avgResponseTime < 200 ? '✅ Good' : '⚠️ Needs Optimization'}
          </div>
        </div>
        
        <div className="trend-card">
          <h3>🎯 Cache Efficiency</h3>
          <div className="trend-value">{Math.round(actualCacheHitRate)}%</div>
          <div className="trend-indicator">
            {actualCacheHitRate > 80 ? '🔥 Excellent' : actualCacheHitRate > 60 ? '✅ Good' : '⚠️ Optimize Cache'}
          </div>
        </div>
      </div>

      <div className="time-series-chart">
        <h3>📊 Recent Request Timeline</h3>
        <div className="chart-container">
          {recentData.map((item, index) => (
            <div key={index} className="timeline-item">
              <div className="timeline-marker">
                <span className={`status-dot ${item.cache_hit ? 'hit' : 'miss'}`}></span>
              </div>
              <div className="timeline-content">
                <div className="timeline-region">{item.edge_node}</div>
                <div className="timeline-resource">{item.resource}</div>
                <div className="timeline-time">{Math.round(item.response_time * 1000)}ms</div>
                <div className="timeline-cost">${item.cost.toFixed(4)}</div>
                <div className="timeline-ip">{item.user_ip}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="performance-table">
        <h3>🌍 Regional Performance Summary</h3>
        <table>
          <thead>
            <tr>
              <th>Region</th>
              <th>Status</th>
              <th>Load</th>
              <th>Cache Items</th>
              <th>Cost</th>
              <th>Location</th>
            </tr>
          </thead>
          <tbody>
            {edge_nodes.map(node => {
              const nodeCost = Object.values(node.cached_items || {}).reduce((sum, item) => {
                return sum + (item.size * 0.01);
              }, 0);
              
              const regionRequests = recent_requests.filter(req => req.edge_node === node.id);
              const regionAvgResponseTime = regionRequests.length > 0 
                ? regionRequests.reduce((sum, req) => sum + req.response_time, 0) / regionRequests.length
                : 0;
              
              return (
                <tr key={node.id}>
                  <td>{node.region}</td>
                  <td>
                    <span className={`status ${node.status === 'healthy' ? 'healthy' : 'warning'}`}>
                      {node.status === 'healthy' ? '✅ Healthy' : '⚠️ ' + node.status}
                    </span>
                  </td>
                  <td>{node.current_load}/{node.capacity}</td>
                  <td>{Object.keys(node.cached_items || {}).length}</td>
                  <td>${nodeCost.toFixed(2)}</td>
                  <td>{node.lat.toFixed(2)}, {node.lng.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MetricsChart;
