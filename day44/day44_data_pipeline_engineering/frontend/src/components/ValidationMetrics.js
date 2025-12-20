import React from 'react';
import './ValidationMetrics.css';

function ValidationMetrics({ data }) {
  if (!data) {
    return <div className="validation-metrics-card">Loading...</div>;
  }
  
  const { 
    validation = { 
      score: 0, 
      passed_checks: 0, 
      total_checks: 0, 
      failures: [], 
      last_run: 'N/A' 
    } 
  } = data;
  
  const getScoreColor = (score) => {
    if (score >= 95) return 'excellent';
    if (score >= 85) return 'good';
    if (score >= 70) return 'warning';
    return 'critical';
  };
  
  const formatDate = (dateStr) => {
    if (!dateStr || dateStr === 'N/A') return 'N/A';
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };
  
  const score = validation.score || 0;
  const passedChecks = validation.passed_checks || 0;
  const totalChecks = validation.total_checks || 0;
  
  return (
    <div className="validation-metrics-card">
      <h2>Data Quality Metrics</h2>
      
      <div className="validation-score">
        <div className={`score-circle ${getScoreColor(score)}`}>
          <span className="score-value">{score.toFixed(1)}</span>
          <span className="score-unit">%</span>
        </div>
        <p className="score-label">Quality Score</p>
      </div>
      
      <div className="validation-details">
        <div className="detail-row">
          <span>Passed Checks:</span>
          <strong className="passed">{passedChecks}</strong>
        </div>
        <div className="detail-row">
          <span>Total Checks:</span>
          <strong>{totalChecks}</strong>
        </div>
        <div className="detail-row">
          <span>Failed Checks:</span>
          <strong className="failed">{totalChecks - passedChecks}</strong>
        </div>
      </div>
      
      {validation.failures && validation.failures.length > 0 && (
        <div className="failures-section">
          <h3>⚠️ Validation Failures</h3>
          <ul className="failures-list">
            {validation.failures.map((failure, idx) => (
              <li key={idx} className="failure-item">{failure}</li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="last-validation">
        <small>Last validated: {formatDate(validation.last_run)}</small>
      </div>
    </div>
  );
}

export default ValidationMetrics;
