import React, { useEffect, useState } from 'react';

const PerformanceMonitoring = () => {
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const load = async () => {
    setError('');
    try {
      const apiBase = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
      const res = await fetch(`${apiBase}/api/performance/report`, { headers: { 'Accept': 'application/json' } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setReport(data.report || data);
    } catch (e) {
      setError(`Failed to load performance report: ${e.message}`);
    }
  };
  useEffect(() => { load(); }, []);

  return (
    <div className="performance-monitoring">
      <h1>Performance Monitoring</h1>
      <p>Real-time system performance metrics</p>
      <button style={{ marginTop: 8 }} onClick={load}>Refresh</button>
      {error && <p style={{ color: 'red', marginTop: 12 }}>{error}</p>}
      {report && (
        <pre style={{ marginTop: 16, background: '#111', color: '#eee', padding: 12, borderRadius: 6, overflowX: 'auto' }}>
{JSON.stringify(report, null, 2)}
        </pre>
      )}
    </div>
  );
};

export default PerformanceMonitoring;
