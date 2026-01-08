import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import TrafficMap from './components/TrafficMap';
import CacheMetrics from './components/CacheMetrics';
import ShardDistribution from './components/ShardDistribution';

function App() {
  const [metrics, setMetrics] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    let ws = null;

    const connect = () => {
      if (!isMountedRef.current) return;

      ws = new WebSocket('ws://localhost:8000/ws/metrics');
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMountedRef.current) {
          ws?.close();
          return;
        }
        console.log('Connected to metrics WebSocket');
        setConnected(true);
      };

      ws.onmessage = (event) => {
        if (!isMountedRef.current) return;
        try {
          const data = JSON.parse(event.data);
          setMetrics(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        if (!isMountedRef.current) return;
        console.log('Disconnected from WebSocket');
        setConnected(false);
      };

      ws.onerror = (error) => {
        if (!isMountedRef.current) return;
        console.error('WebSocket error:', error);
      };
    };

    connect();

    return () => {
      isMountedRef.current = false;
      const currentWs = wsRef.current;
      if (currentWs) {
        // Remove all event handlers first to prevent any callbacks
        currentWs.onopen = null;
        currentWs.onmessage = null;
        currentWs.onclose = null;
        currentWs.onerror = null;
        
        // Only close if the connection is actually open
        // Don't close if still connecting - removing handlers is enough
        // Closing during CONNECTING state causes the error "WebSocket is closed before the connection is established"
        if (currentWs.readyState === WebSocket.OPEN) {
          try {
            currentWs.close();
          } catch (error) {
            // Ignore errors when closing
          }
        }
        // If CONNECTING or CLOSING, just let it fail/complete naturally
        wsRef.current = null;
      }
    };
  }, []);

  if (!metrics) {
    return (
      <div className="App">
        <div className="loading">
          <h2>Connecting to Hyperscale System...</h2>
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="header">
        <h1>🌍 Hyperscale Architecture Dashboard</h1>
        <div className="status">
          <span className={`indicator ${connected ? 'connected' : 'disconnected'}`}></span>
          <span>{connected ? 'Live' : 'Disconnected'}</span>
        </div>
      </header>

      <div className="stats-bar">
        <div className="stat">
          <div className="stat-label">Global RPS</div>
          <div className="stat-value">{(metrics.global_rps / 1000).toFixed(1)}K</div>
        </div>
        <div className="stat">
          <div className="stat-label">Cache Hit Rate</div>
          <div className="stat-value">{(metrics.cache.hit_rate * 100).toFixed(1)}%</div>
        </div>
        <div className="stat">
          <div className="stat-label">Active Regions</div>
          <div className="stat-value">
            {Object.values(metrics.regions).filter(r => !r.failed).length}/3
          </div>
        </div>
        <div className="stat">
          <div className="stat-label">Total Shards</div>
          <div className="stat-value">{Object.keys(metrics.shards).length}</div>
        </div>
      </div>

      <div className="dashboard">
        <TrafficMap regions={metrics.regions} />
        <CacheMetrics cache={metrics.cache} />
        <ShardDistribution shards={metrics.shards} />
      </div>
    </div>
  );
}

export default App;
