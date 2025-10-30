import React, { useEffect, useState } from 'react';

const CostAnalysis = () => {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  const load = async () => {
    setError('');
    try {
      const apiBase = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
      const res = await fetch(`${apiBase}/api/cost-analysis/report`, { headers: { 'Accept': 'application/json' } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (e) {
      setError(`Failed to load cost analysis: ${e.message}`);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="cost-analysis">
      <h1>Cost Analysis</h1>
      <p>Resource utilization and cost optimization recommendations</p>
      <button style={{ marginTop: 8 }} onClick={load}>Refresh</button>
      {error && <p style={{ color: 'red', marginTop: 12 }}>{error}</p>}
      {data && (
        <div style={{ marginTop: 16 }}>
          <h3>Summary</h3>
          <pre style={{ background: '#111', color: '#eee', padding: 12, borderRadius: 6, overflowX: 'auto' }}>
{JSON.stringify(data.analysis || data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default CostAnalysis;
