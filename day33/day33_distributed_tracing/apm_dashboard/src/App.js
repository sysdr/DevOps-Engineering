import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [metrics, setMetrics] = useState(null);
  const [traces, setTraces] = useState([]);
  const [services, setServices] = useState([]);
  const [connected, setConnected] = useState(false);
  const [selectedService, setSelectedService] = useState(null);
  const [serviceHealth, setServiceHealth] = useState({});

  // Service port mapping
  const serviceUrls = {
    'order-service': 'http://localhost:8001',
    'inventory-service': 'http://localhost:8002',
    'payment-service': 'http://localhost:8003',
    'jaeger-all-in-one': 'http://localhost:16686'
  };

  // Check health status of services
  const checkServicesHealth = async (serviceList) => {
    const healthStatus = {};
    for (const service of serviceList) {
      const url = serviceUrls[service];
      if (url && service !== 'jaeger-all-in-one') {
        try {
          const response = await fetch(`${url}/health`, { timeout: 2000 });
          healthStatus[service] = response.ok ? 'healthy' : 'unhealthy';
        } catch (err) {
          healthStatus[service] = 'unhealthy';
        }
      } else if (service === 'jaeger-all-in-one') {
        healthStatus[service] = 'healthy'; // Assume Jaeger is healthy if traces are fetched
      }
    }
    setServiceHealth(healthStatus);
  };

  // Handle service button click
  const handleServiceClick = (service) => {
    setSelectedService(service);
    const url = serviceUrls[service];
    if (url) {
      if (service === 'jaeger-all-in-one') {
        window.open(url, '_blank');
      } else {
        // Fetch service-specific traces
        fetch(`http://localhost:8000/api/traces/recent?limit=10`)
          .then(res => res.json())
          .then(data => {
            const traceData = data.data || [];
            const serviceTraces = traceData.filter(trace => 
              trace.spans?.some(span => 
                span.process?.serviceName === service
              )
            );
            console.log(`Traces for ${service}:`, serviceTraces);
          })
          .catch(err => console.error('Failed to fetch service traces:', err));
      }
    }
  };

  useEffect(() => {
    // Fetch services
    const fetchServices = () => {
      fetch('http://localhost:8000/api/services')
        .then(res => res.json())
        .then(data => {
          const serviceList = data.services || [];
          setServices(serviceList);
          // Check health for each service
          checkServicesHealth(serviceList);
        })
        .catch(err => console.error('Failed to fetch services:', err));
    };
    fetchServices();

    // Fetch recent traces
    const fetchTraces = () => {
      fetch('http://localhost:8000/api/traces/recent?limit=10')
        .then(res => res.json())
        .then(data => {
          const traceData = data.data || [];
          const formattedTraces = traceData.map(trace => ({
            traceID: trace.traceID,
            spanCount: trace.spans?.length || 0,
            duration: (trace.spans?.[0]?.duration || 0) / 1000,
            serviceName: trace.spans?.[0]?.process?.serviceName || 'unknown'
          }));
          setTraces(formattedTraces);
        })
        .catch(err => console.error('Failed to fetch traces:', err));
    };
    fetchTraces();

    // WebSocket for live metrics with reconnection
    let ws = null;
    let reconnectTimeout = null;
    
    const connectWebSocket = () => {
      try {
        ws = new WebSocket('ws://localhost:8000/ws');
        
        ws.onopen = () => {
          console.log('WebSocket connected');
          setConnected(true);
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setMetrics(data);
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setConnected(false);
        };
        
        ws.onclose = () => {
          console.log('WebSocket disconnected, reconnecting in 3s...');
          setConnected(false);
          // Reconnect after 3 seconds
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        setConnected(false);
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      }
    };

    // Initial connection with a small delay to ensure backend is ready
    const initialTimeout = setTimeout(connectWebSocket, 500);

    return () => {
      clearTimeout(initialTimeout);
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws) {
        ws.onclose = null; // Prevent reconnection on unmount
        ws.close();
      }
    };
  }, []);

  // Separate effect for health checking
  useEffect(() => {
    if (services.length === 0) return;
    
    // Initial health check
    checkServicesHealth(services);
    
    // Periodic health check
    const healthInterval = setInterval(() => {
      checkServicesHealth(services);
    }, 10000); // Every 10 seconds

    return () => clearInterval(healthInterval);
  }, [services]);

  return (
    <div className="app">
      <header className="header">
        <h1>🔍 APM Dashboard - Distributed Tracing</h1>
        <div className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '● Live' : '○ Disconnected'}
        </div>
      </header>

      <div className="dashboard">
        <div className="metrics-grid">
          <div className="metric-card">
            <h3>Total Requests</h3>
            <div className="metric-value">{metrics?.total_requests || 0}</div>
          </div>
          
          <div className="metric-card">
            <h3>Error Rate</h3>
            <div className="metric-value error">{metrics?.error_rate?.toFixed(2) || 0}%</div>
          </div>
          
          <div className="metric-card">
            <h3>Active Services</h3>
            <div className="metric-value">{services.length}</div>
          </div>
        </div>

        <div className="section">
          <h2>Service Performance</h2>
          {metrics?.services && Object.entries(metrics.services).map(([service, data]) => (
            <div key={service} className="service-performance">
              <div className="service-header">
                <span className="service-name">{service}</span>
                <span className="request-count">{data.count} requests</span>
              </div>
              <div className="latency-bars">
                <div className="latency-bar">
                  <span className="label">P50</span>
                  <div className="bar">
                    <div 
                      className="bar-fill p50" 
                      style={{width: `${Math.min(data.p50 / 2, 100)}%`}}
                    ></div>
                  </div>
                  <span className="value">{data.p50.toFixed(1)}ms</span>
                </div>
                <div className="latency-bar">
                  <span className="label">P95</span>
                  <div className="bar">
                    <div 
                      className="bar-fill p95" 
                      style={{width: `${Math.min(data.p95 / 2, 100)}%`}}
                    ></div>
                  </div>
                  <span className="value">{data.p95.toFixed(1)}ms</span>
                </div>
                <div className="latency-bar">
                  <span className="label">P99</span>
                  <div className="bar">
                    <div 
                      className="bar-fill p99" 
                      style={{width: `${Math.min(data.p99 / 2, 100)}%`}}
                    ></div>
                  </div>
                  <span className="value">{data.p99.toFixed(1)}ms</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="section">
          <h2>Recent Traces</h2>
          <div className="traces-list">
            {traces.map((trace, idx) => (
              <div key={idx} className="trace-item">
                <div className="trace-id">
                  <a 
                    href={`http://localhost:16686/trace/${trace.traceID}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {trace.traceID.substring(0, 16)}...
                  </a>
                </div>
                <div className="trace-info">
                  <span className="service-badge">{trace.serviceName}</span>
                  <span className="span-count">{trace.spanCount} spans</span>
                  <span className="duration">{trace.duration.toFixed(2)}ms</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="section">
          <h2>Service Map</h2>
          <div className="service-map">
            {services.map(service => {
              const health = serviceHealth[service] || 'unknown';
              const isSelected = selectedService === service;
              const url = serviceUrls[service];
              
              return (
                <button
                  key={service}
                  className={`service-node ${health} ${isSelected ? 'selected' : ''}`}
                  onClick={() => handleServiceClick(service)}
                  title={url ? `Click to view ${service}` : service}
                >
                  <div className="service-status-indicator">
                    <span className={`status-dot ${health}`}></span>
                  </div>
                  <div className="service-name-text">{service}</div>
                  <div className="service-url">{url ? url.replace('http://', '') : ''}</div>
                </button>
              );
            })}
          </div>
          {selectedService && serviceUrls[selectedService] && selectedService !== 'jaeger-all-in-one' && (
            <div className="service-details">
              <h3>Selected: {selectedService}</h3>
              <div className="service-links">
                <a 
                  href={`${serviceUrls[selectedService]}/docs`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="service-link"
                >
                  📚 View API Docs →
                </a>
                <a 
                  href={`${serviceUrls[selectedService]}/health`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="service-link"
                >
                  💚 Health Check →
                </a>
                <a 
                  href={`http://localhost:16686/search?service=${selectedService}`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="service-link"
                >
                  🔍 View Traces →
                </a>
              </div>
            </div>
          )}
        </div>
      </div>

      <footer className="footer">
        <p>Last updated: {metrics?.timestamp ? new Date(metrics.timestamp).toLocaleTimeString() : 'N/A'}</p>
        <p>View full traces in <a href="http://localhost:16686" target="_blank" rel="noopener noreferrer">Jaeger UI</a></p>
      </footer>
    </div>
  );
}

export default App;
