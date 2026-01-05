import React, { useState, useEffect, useRef } from 'react';

function LogAnalyzer() {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef(null);
  const streamIntervalRef = useRef(null);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  // Auto-start streaming demo data on mount
  useEffect(() => {
    if (!isStreaming) {
      const timer = setTimeout(() => {
        setIsStreaming(true);
        // WebSocket connection
        wsRef.current = new WebSocket('ws://localhost:8002/ws');
        wsRef.current.onmessage = (event) => {
          const data = JSON.parse(event.data);
          setLogs(prev => [data, ...prev].slice(0, 50));
        };
        wsRef.current.onerror = () => {
          console.log('WebSocket connection failed, using HTTP fallback');
        };
        // Generate and send sample logs
        streamIntervalRef.current = setInterval(async () => {
          const log = generateSampleLog();
          try {
            await fetch('http://localhost:8002/ingest', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(log)
            });
          } catch (error) {
            console.error('Failed to send log:', error);
          }
        }, 1000);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8002/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const generateSampleLog = () => {
    const levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG', 'CRITICAL'];
    const sources = ['api-server', 'database', 'cache', 'queue', 'frontend'];
    const messages = [
      'Request processed successfully',
      'High memory usage detected',
      'Connection timeout occurred',
      'User authentication failed',
      'Database query slow: 2.5s',
      'Cache miss rate: 45%',
      'API rate limit exceeded',
      'Background job completed',
      'Disk space low: 85% used',
      'Network latency spike detected'
    ];

    // Occasionally generate anomalies
    const isAnomaly = Math.random() < 0.15;
    const level = isAnomaly
      ? Math.random() < 0.5 ? 'ERROR' : 'CRITICAL'
      : levels[Math.floor(Math.random() * levels.length)];

    return {
      timestamp: new Date().toISOString(),
      level: level,
      message: messages[Math.floor(Math.random() * messages.length)],
      source: sources[Math.floor(Math.random() * sources.length)],
      metadata: {}
    };
  };

  const startStreaming = () => {
    setIsStreaming(true);

    // WebSocket connection
    wsRef.current = new WebSocket('ws://localhost:8002/ws');

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLogs(prev => [data, ...prev].slice(0, 50));
    };

    wsRef.current.onerror = () => {
      console.log('WebSocket connection failed, using HTTP fallback');
    };

    // Generate and send sample logs
    streamIntervalRef.current = setInterval(async () => {
      const log = generateSampleLog();
      try {
        await fetch('http://localhost:8002/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(log)
        });
      } catch (error) {
        console.error('Failed to send log:', error);
      }
    }, 1000);
  };

  const stopStreaming = () => {
    setIsStreaming(false);
    if (wsRef.current) {
      wsRef.current.close();
    }
    if (streamIntervalRef.current) {
      clearInterval(streamIntervalRef.current);
    }
  };

  useEffect(() => {
    return () => {
      stopStreaming();
    };
  }, []);

  return (
    <div className="panel">
      <h2>📊 Intelligent Log Analyzer</h2>
      <p style={{ color: '#718096', marginBottom: '1rem' }}>
        Real-time log monitoring with AI-powered anomaly detection
      </p>

      {stats && (
        <div className="metric-grid">
          <div className="metric-card">
            <div className="metric-value">{stats.total_logs}</div>
            <div className="metric-label">TOTAL LOGS</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{stats.is_trained ? 'YES' : 'NO'}</div>
            <div className="metric-label">MODEL TRAINED</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{stats.buffer_size}</div>
            <div className="metric-label">BUFFER SIZE</div>
          </div>
        </div>
      )}

      <button
        className="primary"
        onClick={isStreaming ? stopStreaming : startStreaming}
      >
        {isStreaming ? '⏸ Stop Streaming' : '▶ Start Log Stream'}
      </button>

      {logs.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>
            Recent Logs ({logs.length})
          </h3>
          <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
            {logs.map((logResult, idx) => (
              <div
                key={idx}
                className={`log-entry ${logResult.is_anomaly ? 'anomaly' : ''}`}
              >
                <div className="log-header">
                  <span style={{ fontSize: '0.75rem', color: '#718096' }}>
                    {new Date(logResult.log.timestamp).toLocaleTimeString()}
                  </span>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span className={`log-level ${logResult.log.level}`}>
                      {logResult.log.level}
                    </span>
                    {logResult.is_anomaly && (
                      <span style={{
                        background: '#fc8181',
                        color: 'white',
                        padding: '0.2rem 0.6rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: '600'
                      }}>
                        ANOMALY
                      </span>
                    )}
                  </div>
                </div>
                <div style={{ marginTop: '0.5rem' }}>
                  <strong>{logResult.log.source}:</strong> {logResult.log.message}
                </div>
                {logResult.is_anomaly && (
                  <div style={{
                    marginTop: '0.5rem',
                    padding: '0.5rem',
                    background: 'rgba(252, 129, 129, 0.1)',
                    borderRadius: '4px',
                    fontSize: '0.85rem'
                  }}>
                    🔍 {logResult.reason} (Score: {logResult.anomaly_score.toFixed(2)})
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default LogAnalyzer;
