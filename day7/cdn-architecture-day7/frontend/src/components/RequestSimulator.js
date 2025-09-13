import React, { useState } from 'react';

const RequestSimulator = ({ onMetricsUpdate }) => {
  const [isSimulating, setIsSimulating] = useState(false);
  const [lastResponse, setLastResponse] = useState(null);
  const [simulationParams, setSimulationParams] = useState({
    resource: 'homepage.html',
    lat: 40.7128,
    lng: -74.0060,
    userRegion: 'New York, US'
  });

  const userLocations = [
    { name: 'New York, US', lat: 40.7128, lng: -74.0060 },
    { name: 'London, UK', lat: 51.5074, lng: -0.1278 },
    { name: 'Tokyo, Japan', lat: 35.6762, lng: 139.6503 },
    { name: 'Mumbai, India', lat: 19.0760, lng: 72.8777 },
    { name: 'San Francisco, US', lat: 37.7749, lng: -122.4194 }
  ];

  const resources = [
    'homepage.html', 'logo.png', 'app.js', 'styles.css', 'api-data.json',
    'video.mp4', 'image-gallery.js', 'user-profile.json'
  ];

  const simulateRequest = async () => {
    setIsSimulating(true);
    try {
      const response = await fetch('/api/cdn/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resource: simulationParams.resource,
          lat: simulationParams.lat,
          lng: simulationParams.lng,
          ip: '192.168.1.100'
        })
      });

      const result = await response.json();
      setLastResponse(result);

      // Refresh metrics
      const metricsResponse = await fetch('/api/cdn/metrics');
      const metrics = await metricsResponse.json();
      onMetricsUpdate(metrics);
    } catch (error) {
      console.error('Request failed:', error);
    }
    setIsSimulating(false);
  };

  const runLoadTest = async () => {
    setIsSimulating(true);
    const requests = [];
    
    // Generate 50 random requests
    for (let i = 0; i < 50; i++) {
      const location = userLocations[Math.floor(Math.random() * userLocations.length)];
      const resource = resources[Math.floor(Math.random() * resources.length)];
      
      requests.push(
        fetch('/api/cdn/request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            resource,
            lat: location.lat,
            lng: location.lng,
            ip: `192.168.1.${Math.floor(Math.random() * 255)}`
          })
        })
      );
    }

    try {
      await Promise.all(requests);
      
      // Refresh metrics
      const metricsResponse = await fetch('/api/cdn/metrics');
      const metrics = await metricsResponse.json();
      onMetricsUpdate(metrics);
    } catch (error) {
      console.error('Load test failed:', error);
    }
    setIsSimulating(false);
  };

  const invalidateCache = async () => {
    try {
      await fetch('/api/cdn/invalidate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resource: simulationParams.resource,
          regions: ['us-east', 'us-west', 'eu-west', 'ap-south', 'ap-east']
        })
      });
      alert('Cache invalidated successfully!');
    } catch (error) {
      console.error('Cache invalidation failed:', error);
    }
  };

  return (
    <div className="request-simulator">
      <div className="simulator-controls">
        <h2>🎯 CDN Request Simulator</h2>
        
        <div className="form-group">
          <label>User Location:</label>
          <select 
            value={simulationParams.userRegion}
            onChange={(e) => {
              const location = userLocations.find(loc => loc.name === e.target.value);
              setSimulationParams({
                ...simulationParams,
                userRegion: e.target.value,
                lat: location.lat,
                lng: location.lng
              });
            }}
          >
            {userLocations.map(location => (
              <option key={location.name} value={location.name}>
                {location.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Resource:</label>
          <select 
            value={simulationParams.resource}
            onChange={(e) => setSimulationParams({
              ...simulationParams,
              resource: e.target.value
            })}
          >
            {resources.map(resource => (
              <option key={resource} value={resource}>{resource}</option>
            ))}
          </select>
        </div>

        <div className="action-buttons">
          <button 
            onClick={simulateRequest} 
            disabled={isSimulating}
            className="primary-button"
          >
            {isSimulating ? '⏳ Requesting...' : '🚀 Send Request'}
          </button>
          
          <button 
            onClick={runLoadTest} 
            disabled={isSimulating}
            className="secondary-button"
          >
            {isSimulating ? '⏳ Testing...' : '📈 Load Test (50 requests)'}
          </button>
          
          <button 
            onClick={invalidateCache}
            className="danger-button"
          >
            🗑️ Invalidate Cache
          </button>
        </div>
      </div>

      {lastResponse && (
        <div className="response-details">
          <h3>📊 Last Request Response</h3>
          <div className="response-grid">
            <div className="response-item">
              <span className="label">Edge Node:</span>
              <span className="value">{lastResponse.edge_node.region}</span>
            </div>
            <div className="response-item">
              <span className="label">Cache Hit:</span>
              <span className={`value ${lastResponse.cache_hit ? 'hit' : 'miss'}`}>
                {lastResponse.cache_hit ? '✅ HIT' : '❌ MISS'}
              </span>
            </div>
            <div className="response-item">
              <span className="label">Response Time:</span>
              <span className="value">{Math.round(lastResponse.response_time_ms)}ms</span>
            </div>
            <div className="response-item">
              <span className="label">Cost:</span>
              <span className="value">${lastResponse.cost_usd.toFixed(4)}</span>
            </div>
            <div className="response-item">
              <span className="label">Node Load:</span>
              <span className="value">
                {lastResponse.edge_node.current_load}/{lastResponse.edge_node.capacity}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RequestSimulator;
