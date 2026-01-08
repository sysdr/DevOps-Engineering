import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function CacheMetrics({ cache }) {
  const data = [
    { name: 'L1 Cache', hits: cache.l1_hits, color: '#10b981' },
    { name: 'L2 Cache', hits: cache.l2_hits, color: '#3b82f6' },
    { name: 'L3 Cache', hits: cache.l3_hits, color: '#8b5cf6' },
    { name: 'Misses', hits: cache.misses, color: '#ef4444' }
  ];

  return (
    <div className="card">
      <h2>💾 Cache Performance</h2>
      <div className="cache-summary">
        <div className="cache-stat">
          <div className="cache-label">Hit Rate</div>
          <div className="cache-value">{(cache.hit_rate * 100).toFixed(2)}%</div>
        </div>
        <div className="cache-stat">
          <div className="cache-label">Total Requests</div>
          <div className="cache-value">
            {(cache.l1_hits + cache.l2_hits + cache.l3_hits + cache.misses).toLocaleString()}
          </div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="hits" fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
      <div className="cache-breakdown">
        {data.map((item) => (
          <div key={item.name} className="cache-tier">
            <div className="tier-header">
              <span className="tier-dot" style={{ backgroundColor: item.color }}></span>
              <span className="tier-name">{item.name}</span>
            </div>
            <div className="tier-value">{item.hits.toLocaleString()}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default CacheMetrics;
