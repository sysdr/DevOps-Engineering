import React, { useState, useEffect } from 'react';

const PerformanceTuning = () => {
  const [performance, setPerformance] = useState(null);

  useEffect(() => {
    const fetchPerformance = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/performance/tuning');
        const data = await response.json();
        setPerformance(data);
      } catch (error) {
        console.error('Error fetching performance:', error);
      }
    };

    fetchPerformance();
    const interval = setInterval(fetchPerformance, 10000);
    return () => clearInterval(interval);
  }, []);

  if (!performance) return <div className="loading">Loading performance data...</div>;

  return (
    <div className="performance-container">
      <div className="performance-score">
        <h2>Optimization Score: {performance.optimization_score}/100</h2>
        <div className="score-bar">
          <div 
            className="score-fill" 
            style={{width: `${performance.optimization_score}%`}}
          ></div>
        </div>
      </div>
      
      <div className="kernel-params">
        <h3>Kernel Parameters</h3>
        <div className="params-grid">
          {Object.entries(performance.kernel_parameters).map(([param, config]) => (
            <div key={param} className="param-card">
              <div className="param-name">{param}</div>
              <div className="param-values">
                <span className="current">Current: {config.current.toLocaleString()}</span>
                <span className="recommended">Recommended: {config.recommended.toLocaleString()}</span>
                <span className="tuned-status">
                  {config.tuned ? '✅ Tuned' : '❌ Not Tuned'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="process-info">
        <h3>Process Information</h3>
        <div className="process-grid">
          <div className="process-card">
            <h4>Total Processes</h4>
            <div className="process-count">{performance.processes.total}</div>
          </div>
          <div className="process-card">
            <h4>Running</h4>
            <div className="process-count">{performance.processes.running}</div>
          </div>
          <div className="process-card">
            <h4>Sleeping</h4>
            <div className="process-count">{performance.processes.sleeping}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceTuning;
