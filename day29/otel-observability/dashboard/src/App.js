import React, { useState, useEffect } from 'react';

const styles = {
  container: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
    minHeight: '100vh',
    padding: '24px',
    color: '#e8e8e8'
  },
  header: {
    textAlign: 'center',
    marginBottom: '32px'
  },
  title: {
    fontSize: '2.5rem',
    fontWeight: '700',
    background: 'linear-gradient(90deg, #00d4ff, #7b2cbf)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    marginBottom: '8px'
  },
  subtitle: {
    color: '#a0a0a0',
    fontSize: '1rem'
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
    gap: '20px',
    marginBottom: '24px'
  },
  card: {
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '16px',
    padding: '24px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)'
  },
  cardTitle: {
    fontSize: '1.1rem',
    fontWeight: '600',
    marginBottom: '16px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  metricValue: {
    fontSize: '2.5rem',
    fontWeight: '700',
    marginBottom: '4px'
  },
  metricLabel: {
    color: '#a0a0a0',
    fontSize: '0.875rem'
  },
  serviceGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '12px',
    marginTop: '16px'
  },
  serviceCard: {
    background: 'rgba(0, 212, 255, 0.1)',
    borderRadius: '8px',
    padding: '12px',
    textAlign: 'center'
  },
  serviceName: {
    fontSize: '0.75rem',
    color: '#a0a0a0',
    marginBottom: '4px'
  },
  serviceStatus: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '6px'
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%'
  },
  traceList: {
    maxHeight: '300px',
    overflowY: 'auto'
  },
  traceItem: {
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '8px',
    padding: '12px',
    marginBottom: '8px',
    borderLeft: '3px solid'
  },
  traceHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '8px'
  },
  traceId: {
    fontFamily: 'monospace',
    fontSize: '0.75rem',
    color: '#00d4ff'
  },
  traceDuration: {
    fontSize: '0.875rem',
    fontWeight: '600'
  },
  spanBar: {
    height: '4px',
    borderRadius: '2px',
    marginTop: '8px'
  },
  logItem: {
    fontFamily: 'monospace',
    fontSize: '0.75rem',
    padding: '8px',
    background: 'rgba(0, 0, 0, 0.3)',
    borderRadius: '4px',
    marginBottom: '6px',
    borderLeft: '3px solid'
  },
  button: {
    background: 'linear-gradient(90deg, #00d4ff, #7b2cbf)',
    border: 'none',
    borderRadius: '8px',
    padding: '12px 24px',
    color: 'white',
    fontWeight: '600',
    cursor: 'pointer',
    fontSize: '0.875rem',
    marginRight: '12px',
    marginBottom: '8px'
  },
  buttonSecondary: {
    background: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.2)'
  },
  pillarIndicator: {
    display: 'flex',
    gap: '24px',
    justifyContent: 'center',
    marginBottom: '24px'
  },
  pillar: {
    textAlign: 'center',
    padding: '16px 24px',
    borderRadius: '12px',
    background: 'rgba(255, 255, 255, 0.05)'
  },
  pillarIcon: {
    fontSize: '2rem',
    marginBottom: '8px'
  },
  pillarName: {
    fontWeight: '600',
    fontSize: '0.875rem'
  },
  pillarCount: {
    fontSize: '1.5rem',
    fontWeight: '700'
  },
  links: {
    display: 'flex',
    gap: '12px',
    flexWrap: 'wrap',
    marginTop: '16px'
  },
  link: {
    color: '#00d4ff',
    textDecoration: 'none',
    fontSize: '0.875rem',
    padding: '8px 16px',
    background: 'rgba(0, 212, 255, 0.1)',
    borderRadius: '6px'
  }
};

function App() {
  const [services, setServices] = useState({
    order: { status: 'unknown', latency: 0 },
    inventory: { status: 'unknown', latency: 0 },
    payment: { status: 'unknown', latency: 0 }
  });
  const [traces, setTraces] = useState([]);
  const [logs, setLogs] = useState([]);
  const [metrics, setMetrics] = useState({
    totalOrders: 0,
    successRate: 100,
    avgLatency: 0,
    activeSpans: 0
  });
  const [isGenerating, setIsGenerating] = useState(false);

  // Check service health
  const checkServices = async () => {
    const serviceUrls = {
      order: 'http://localhost:8000/health',
      inventory: 'http://localhost:8001/health',
      payment: 'http://localhost:8002/health'
    };

    const newServices = { ...services };

    for (const [name, url] of Object.entries(serviceUrls)) {
      const start = Date.now();
      try {
        const response = await fetch(url);
        const latency = Date.now() - start;
        newServices[name] = {
          status: response.ok ? 'healthy' : 'unhealthy',
          latency
        };
      } catch (error) {
        newServices[name] = { status: 'down', latency: 0 };
      }
    }

    setServices(newServices);
  };

  // Generate test order
  const generateOrder = async () => {
    setIsGenerating(true);
    
    const orderData = {
      customer_id: `CUST-${Math.floor(Math.random() * 1000)}`,
      items: [
        {
          product_id: `PROD-00${Math.floor(Math.random() * 5) + 1}`,
          quantity: Math.floor(Math.random() * 3) + 1,
          price: Math.floor(Math.random() * 100) + 10
        }
      ],
      payment_method: ['credit_card', 'debit_card', 'paypal'][Math.floor(Math.random() * 3)]
    };

    try {
      const start = Date.now();
      const response = await fetch('http://localhost:8000/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
      });
      
      const duration = Date.now() - start;
      const result = await response.json();

      // Add trace
      const newTrace = {
        id: result.order_id || `trace-${Date.now()}`,
        duration,
        status: response.ok ? 'success' : 'error',
        spans: [
          { name: 'order-service', duration: duration * 0.3 },
          { name: 'inventory-service', duration: duration * 0.2 },
          { name: 'payment-service', duration: duration * 0.5 }
        ],
        timestamp: new Date().toISOString()
      };
      
      setTraces(prev => [newTrace, ...prev].slice(0, 10));

      // Add log
      const newLog = {
        level: response.ok ? 'info' : 'error',
        message: response.ok 
          ? `Order ${result.order_id} completed successfully`
          : `Order failed: ${result.detail || 'Unknown error'}`,
        timestamp: new Date().toISOString(),
        traceId: newTrace.id
      };
      
      setLogs(prev => [newLog, ...prev].slice(0, 20));

      // Update metrics
      setMetrics(prev => ({
        totalOrders: prev.totalOrders + 1,
        successRate: response.ok 
          ? Math.round((prev.successRate * prev.totalOrders + 100) / (prev.totalOrders + 1))
          : Math.round((prev.successRate * prev.totalOrders) / (prev.totalOrders + 1)),
        avgLatency: Math.round((prev.avgLatency * prev.totalOrders + duration) / (prev.totalOrders + 1)),
        activeSpans: prev.activeSpans + 3
      }));

    } catch (error) {
      const newLog = {
        level: 'error',
        message: `Request failed: ${error.message}`,
        timestamp: new Date().toISOString(),
        traceId: 'N/A'
      };
      setLogs(prev => [newLog, ...prev].slice(0, 20));
    }

    setIsGenerating(false);
  };

  // Generate multiple orders
  const generateBatch = async () => {
    for (let i = 0; i < 5; i++) {
      await generateOrder();
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  };

  useEffect(() => {
    checkServices();
    const interval = setInterval(checkServices, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return '#00ff88';
      case 'unhealthy': return '#ffaa00';
      case 'down': return '#ff4444';
      default: return '#888888';
    }
  };

  const getLogColor = (level) => {
    switch (level) {
      case 'error': return '#ff4444';
      case 'warn': return '#ffaa00';
      case 'info': return '#00d4ff';
      default: return '#888888';
    }
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>OpenTelemetry Observability</h1>
        <p style={styles.subtitle}>Distributed Tracing • Metrics • Logs</p>
      </header>

      {/* Three Pillars */}
      <div style={styles.pillarIndicator}>
        <div style={styles.pillar}>
          <div style={styles.pillarIcon}>📊</div>
          <div style={styles.pillarName}>Traces</div>
          <div style={{ ...styles.pillarCount, color: '#00d4ff' }}>{traces.length}</div>
        </div>
        <div style={styles.pillar}>
          <div style={styles.pillarIcon}>📈</div>
          <div style={styles.pillarName}>Metrics</div>
          <div style={{ ...styles.pillarCount, color: '#7b2cbf' }}>{metrics.activeSpans}</div>
        </div>
        <div style={styles.pillar}>
          <div style={styles.pillarIcon}>📝</div>
          <div style={styles.pillarName}>Logs</div>
          <div style={{ ...styles.pillarCount, color: '#00ff88' }}>{logs.length}</div>
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <button 
          style={styles.button}
          onClick={generateOrder}
          disabled={isGenerating}
        >
          {isGenerating ? 'Processing...' : 'Create Order'}
        </button>
        <button 
          style={{ ...styles.button, ...styles.buttonSecondary }}
          onClick={generateBatch}
          disabled={isGenerating}
        >
          Generate 5 Orders
        </button>
        <button 
          style={{ ...styles.button, ...styles.buttonSecondary }}
          onClick={checkServices}
        >
          Refresh Services
        </button>
      </div>

      <div style={styles.grid}>
        {/* Services Status */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>
            <span>🔗</span> Service Health
          </h3>
          <div style={styles.serviceGrid}>
            {Object.entries(services).map(([name, data]) => (
              <div key={name} style={styles.serviceCard}>
                <div style={styles.serviceName}>{name.toUpperCase()}</div>
                <div style={styles.serviceStatus}>
                  <div style={{
                    ...styles.statusDot,
                    background: getStatusColor(data.status)
                  }}></div>
                  <span style={{ fontSize: '0.75rem' }}>
                    {data.latency > 0 ? `${data.latency}ms` : data.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Metrics Overview */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>
            <span>📊</span> Metrics
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <div style={{ ...styles.metricValue, color: '#00d4ff' }}>
                {metrics.totalOrders}
              </div>
              <div style={styles.metricLabel}>Total Orders</div>
            </div>
            <div>
              <div style={{ ...styles.metricValue, color: '#00ff88' }}>
                {metrics.successRate}%
              </div>
              <div style={styles.metricLabel}>Success Rate</div>
            </div>
            <div>
              <div style={{ ...styles.metricValue, color: '#7b2cbf' }}>
                {metrics.avgLatency}ms
              </div>
              <div style={styles.metricLabel}>Avg Latency</div>
            </div>
            <div>
              <div style={{ ...styles.metricValue, color: '#ffaa00' }}>
                {metrics.activeSpans}
              </div>
              <div style={styles.metricLabel}>Total Spans</div>
            </div>
          </div>
        </div>

        {/* Traces */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>
            <span>🔍</span> Recent Traces
          </h3>
          <div style={styles.traceList}>
            {traces.length === 0 ? (
              <p style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
                No traces yet. Create an order to see traces.
              </p>
            ) : (
              traces.map((trace, idx) => (
                <div key={idx} style={{
                  ...styles.traceItem,
                  borderLeftColor: trace.status === 'success' ? '#00ff88' : '#ff4444'
                }}>
                  <div style={styles.traceHeader}>
                    <span style={styles.traceId}>{trace.id}</span>
                    <span style={{
                      ...styles.traceDuration,
                      color: trace.duration < 200 ? '#00ff88' : trace.duration < 500 ? '#ffaa00' : '#ff4444'
                    }}>
                      {trace.duration}ms
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    {trace.spans.map((span, i) => (
                      <div key={i} style={{
                        ...styles.spanBar,
                        flex: span.duration,
                        background: ['#00d4ff', '#7b2cbf', '#00ff88'][i]
                      }} title={`${span.name}: ${Math.round(span.duration)}ms`}></div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Logs */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>
            <span>📝</span> Structured Logs
          </h3>
          <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
            {logs.length === 0 ? (
              <p style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
                No logs yet. Create an order to see logs.
              </p>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} style={{
                  ...styles.logItem,
                  borderLeftColor: getLogColor(log.level)
                }}>
                  <div style={{ color: getLogColor(log.level), marginBottom: '4px' }}>
                    [{log.level.toUpperCase()}] {log.timestamp.split('T')[1].split('.')[0]}
                  </div>
                  <div>{log.message}</div>
                  {log.traceId !== 'N/A' && (
                    <div style={{ color: '#666', marginTop: '4px' }}>
                      trace_id: {log.traceId}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* External Links */}
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>
          <span>🔗</span> Observability Tools
        </h3>
        <div style={styles.links}>
          <a href="http://localhost:16686" target="_blank" rel="noopener noreferrer" style={styles.link}>
            Jaeger Tracing UI
          </a>
          <a href="http://localhost:9090" target="_blank" rel="noopener noreferrer" style={styles.link}>
            Prometheus Metrics
          </a>
          <a href="http://localhost:55679/debug/tracez" target="_blank" rel="noopener noreferrer" style={styles.link}>
            Collector zPages
          </a>
          <a href="http://localhost:8889/metrics" target="_blank" rel="noopener noreferrer" style={styles.link}>
            OTEL Metrics Endpoint
          </a>
        </div>
      </div>
    </div>
  );
}

export default App;
