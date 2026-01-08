import React from 'react';

function TrafficMap({ regions }) {
  const regionData = [
    { name: 'US-EAST', ...regions['us-east'], x: 30, y: 35 },
    { name: 'US-WEST', ...regions['us-west'], x: 15, y: 35 },
    { name: 'EU-WEST', ...regions['eu-west'], x: 50, y: 30 }
  ];

  const getHealthColor = (health) => {
    if (health >= 90) return '#10b981';
    if (health >= 70) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="card">
      <h2>🗺️ Global Traffic Distribution</h2>
      <div className="map-container">
        <svg viewBox="0 0 100 60" className="world-map">
          {/* World map outline (simplified) */}
          <rect x="0" y="0" width="100" height="60" fill="#f0f9ff" />
          
          {/* Regions */}
          {regionData.map((region) => (
            <g key={region.name}>
              <circle
                cx={region.x}
                cy={region.y}
                r={region.failed ? 3 : 4}
                fill={region.failed ? '#ef4444' : getHealthColor(region.health)}
                opacity={region.failed ? 0.5 : 0.9}
              />
              <text
                x={region.x}
                y={region.y + 8}
                textAnchor="middle"
                className="region-label"
                fontSize="2.5"
                fill="#1f2937"
              >
                {region.name}
              </text>
              <text
                x={region.x}
                y={region.y + 11}
                textAnchor="middle"
                fontSize="2"
                fill={region.failed ? '#ef4444' : '#6b7280'}
              >
                {region.failed ? 'FAILED' : `${(region.rps / 1000).toFixed(0)}K RPS`}
              </text>
            </g>
          ))}
        </svg>

        <div className="region-list">
          {regionData.map((region) => (
            <div key={region.name} className="region-item">
              <div className="region-info">
                <span className="region-name">{region.name}</span>
                <span className={`region-status ${region.failed ? 'failed' : 'healthy'}`}>
                  {region.failed ? 'FAILED' : `Health: ${region.health}/100`}
                </span>
              </div>
              <div className="region-metrics">
                <div className="metric">RPS: {(region.rps / 1000).toFixed(1)}K</div>
                <div className="metric">Latency: {region.latency_p99}ms (P99)</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default TrafficMap;
