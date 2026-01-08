import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

function ShardDistribution({ shards }) {
  const shardData = Object.entries(shards).map(([name, data]) => ({
    name: name.toUpperCase(),
    load: data.load_pct,
    keys: data.keys,
    requests: data.requests
  }));

  const getColor = (load) => {
    if (load < 20) return '#10b981';
    if (load < 30) return '#3b82f6';
    return '#8b5cf6';
  };

  return (
    <div className="card">
      <h2>🔀 Database Sharding Distribution</h2>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={shardData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis label={{ value: 'Load %', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Bar dataKey="load" fill="#3b82f6">
            {shardData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.load)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="shard-details">
        {shardData.map((shard) => (
          <div key={shard.name} className="shard-item">
            <div className="shard-header">
              <span className="shard-name">{shard.name}</span>
              <span className="shard-load">{shard.load.toFixed(1)}%</span>
            </div>
            <div className="shard-metrics">
              <div className="shard-metric">Keys: {shard.keys.toLocaleString()}</div>
              <div className="shard-metric">Requests: {shard.requests.toLocaleString()}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ShardDistribution;
