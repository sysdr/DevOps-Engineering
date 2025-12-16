import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [threats, setThreats] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    
    // Fetch initial metrics
    fetchMetrics();
    const metricsInterval = setInterval(fetchMetrics, 5000);

    // Setup WebSocket connection with a small delay to avoid React Strict Mode issues
    const connectTimeout = setTimeout(() => {
      if (isMountedRef.current) {
        connectWebSocket();
      }
    }, 100);

    return () => {
      isMountedRef.current = false;
      clearInterval(metricsInterval);
      
      // Clear connection timeout
      if (connectTimeout) {
        clearTimeout(connectTimeout);
      }
      
      // Clear any pending reconnection attempts
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      
      // Close WebSocket if it exists
      if (wsRef.current) {
        const ws = wsRef.current;
        // Remove event handlers to prevent reconnection
        ws.onopen = null;
        ws.onclose = null;
        ws.onerror = null;
        ws.onmessage = null;
        
        // Only close if not already closed or closing
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          try {
            ws.close(1000, 'Component unmounting');
          } catch (e) {
            // Ignore errors when closing
          }
        }
        wsRef.current = null;
      }
    };
  }, []);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/health');
      return response.ok;
    } catch (error) {
      return false;
    }
  };

  const connectWebSocket = async () => {
    // Don't reconnect if component is unmounted
    if (!isMountedRef.current) {
      return;
    }
    
    // Clean up any existing connection first
    if (wsRef.current) {
      const existingWs = wsRef.current;
      // Only proceed if the existing connection is closed or closing
      if (existingWs.readyState === WebSocket.CONNECTING || 
          existingWs.readyState === WebSocket.OPEN) {
        // Don't create a new connection if one is already active
        return;
      }
      // Clean up closed connection
      existingWs.onopen = null;
      existingWs.onclose = null;
      existingWs.onerror = null;
      existingWs.onmessage = null;
      wsRef.current = null;
    }
    
    // Check if backend is available before connecting
    const backendAvailable = await checkBackendHealth();
    if (!backendAvailable) {
      console.log('Backend not available, will retry...');
      if (isMountedRef.current) {
        setConnected(false);
        // Retry after delay
        reconnectTimeoutRef.current = setTimeout(() => {
          if (isMountedRef.current) {
            connectWebSocket();
          }
        }, 3000);
      }
      return;
    }
    
    try {
      const ws = new WebSocket('ws://localhost:8000/ws');
      
      // Set up handlers immediately to catch all events
      ws.onopen = () => {
        console.log('WebSocket connected');
        if (isMountedRef.current && wsRef.current === ws) {
          setConnected(true);
          reconnectAttemptsRef.current = 0; // Reset on successful connection
        }
      };
      
      ws.onmessage = (event) => {
        if (!isMountedRef.current || wsRef.current !== ws) return;
        
        try {
          const message = JSON.parse(event.data);
          
          if (message.type === 'threat_detected') {
            setThreats(prev => [message.data, ...prev].slice(0, 20));
          } else if (message.type === 'incident_response') {
            setIncidents(prev => [message.data, ...prev].slice(0, 10));
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      ws.onerror = (error) => {
        // Only log if this is still the active connection
        if (wsRef.current === ws) {
          // Don't log the generic error event, wait for onclose for more details
          if (isMountedRef.current) {
            setConnected(false);
          }
        }
      };
      
      ws.onclose = (event) => {
        // Only handle if this is still the active connection
        if (wsRef.current === ws) {
          // Only log if it's not a normal closure
          if (event.code !== 1000) {
            console.log('WebSocket disconnected', event.code, event.reason || '');
          }
          if (isMountedRef.current) {
            setConnected(false);
            
            // Only reconnect if component is still mounted and it wasn't a manual close
            // Code 1000 = normal closure, 1001 = going away, 1006 = abnormal closure
            if (event.code !== 1000 && isMountedRef.current) {
              // Exponential backoff: 3s, 6s, 12s, max 30s
              const delay = Math.min(3000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
              reconnectAttemptsRef.current++;
              
              reconnectTimeoutRef.current = setTimeout(() => {
                if (isMountedRef.current) {
                  connectWebSocket();
                }
              }, delay);
            }
          }
          wsRef.current = null;
        }
      };
      
      // Store reference only after handlers are set up
      wsRef.current = ws;
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      if (isMountedRef.current) {
        setConnected(false);
        // Retry after delay
        reconnectTimeoutRef.current = setTimeout(() => {
          if (isMountedRef.current) {
            connectWebSocket();
          }
        }, 3000);
      }
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/metrics');
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const triggerTestIncident = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/test-incident', {
        method: 'POST'
      });
      const data = await response.json();
      alert(`Test incident triggered: ${data.status}`);
    } catch (error) {
      console.error('Error triggering test:', error);
      alert('Error triggering test incident');
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      'CRITICAL': '#dc2626',
      'HIGH': '#ea580c',
      'MEDIUM': '#eab308',
      'LOW': '#3b82f6',
      'INFO': '#6b7280'
    };
    return colors[severity] || '#6b7280';
  };

  return (
    <div className="App">
      <header className="header">
        <h1>🛡️ Security Operations Center</h1>
        <div className="connection-status">
          <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}></span>
          <span>{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </header>

      <div className="container">
        {/* Metrics Section */}
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-label">MTTD</div>
            <div className="metric-value">
              {metrics ? `${metrics.mttd_seconds.toFixed(2)}s` : '—'}
            </div>
            <div className="metric-subtitle">Mean Time To Detect</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-label">MTTR</div>
            <div className="metric-value">
              {metrics ? `${metrics.mttr_seconds.toFixed(2)}s` : '—'}
            </div>
            <div className="metric-subtitle">Mean Time To Respond</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-label">False Positive Rate</div>
            <div className="metric-value">
              {metrics ? `${metrics.false_positive_rate.toFixed(1)}%` : '—'}
            </div>
            <div className="metric-subtitle">Alert Accuracy</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-label">Coverage</div>
            <div className="metric-value">
              {metrics ? `${metrics.coverage_percentage.toFixed(1)}%` : '—'}
            </div>
            <div className="metric-subtitle">Infrastructure Monitored</div>
          </div>
        </div>

        {/* Incidents by Severity */}
        {metrics && (
          <div className="severity-section">
            <h2>Incidents by Severity (Total: {metrics.total_incidents})</h2>
            <div className="severity-grid">
              {Object.entries(metrics.incidents_by_severity).map(([severity, count]) => (
                <div key={severity} className="severity-badge" style={{ borderColor: getSeverityColor(severity) }}>
                  <span className="severity-name" style={{ color: getSeverityColor(severity) }}>{severity}</span>
                  <span className="severity-count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Test Button */}
        <div className="test-section">
          <button onClick={triggerTestIncident} className="test-button">
            🔥 Trigger Test Incident
          </button>
        </div>

        {/* Live Threat Feed */}
        <div className="section">
          <h2>🎯 Live Threat Feed</h2>
          <div className="threat-list">
            {threats.length === 0 ? (
              <div className="empty-state">Monitoring for threats...</div>
            ) : (
              threats.map((threat, index) => (
                <div key={index} className="threat-item" style={{ borderLeftColor: getSeverityColor(threat.severity) }}>
                  <div className="threat-header">
                    <span className="threat-severity" style={{ backgroundColor: getSeverityColor(threat.severity) }}>
                      {threat.severity}
                    </span>
                    <span className="threat-score">Score: {threat.threat_score}</span>
                    <span className="threat-time">
                      {new Date(threat.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="threat-findings">
                    {threat.findings.map((finding, i) => (
                      <div key={i} className="finding">• {finding}</div>
                    ))}
                  </div>
                  <div className="threat-details">
                    Pod: {threat.original_event.pod_name} | 
                    Event: {threat.event_id}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Active Incidents */}
        <div className="section">
          <h2>🚨 Active Incidents</h2>
          <div className="incident-list">
            {incidents.length === 0 ? (
              <div className="empty-state">No active incidents</div>
            ) : (
              incidents.map((incident, index) => (
                <div key={index} className="incident-item">
                  <div className="incident-header">
                    <span className="incident-id">{incident.incident_id}</span>
                    <span className="incident-severity" style={{ backgroundColor: getSeverityColor(incident.severity) }}>
                      {incident.severity}
                    </span>
                    <span className="incident-status">{incident.status}</span>
                  </div>
                  <div className="incident-actions">
                    <strong>Actions Executed:</strong>
                    {incident.actions_executed.map((action, i) => (
                      <div key={i} className="action-item">
                        ✓ {action.action}: {action.details}
                      </div>
                    ))}
                  </div>
                  <div className="incident-footer">
                    Response Time: {incident.response_time_ms}ms | 
                    {new Date(incident.timestamp).toLocaleString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
