import React from 'react';

function SecurityMetrics({ metrics }) {
  return (
    <div className="metrics-dashboard">
      <div className="metric-card">
        <h3>Total Images</h3>
        <div className="metric-value">{metrics.total_images || 0}</div>
      </div>
      
      <div className="metric-card">
        <h3>Signed Images</h3>
        <div className="metric-value">{metrics.signed_images || 0}</div>
        <div className="metric-subtitle">{metrics.signature_coverage || 0}% Coverage</div>
      </div>
      
      <div className="metric-card">
        <h3>Scanned Images</h3>
        <div className="metric-value">{metrics.scanned_images || 0}</div>
      </div>
      
      <div className="metric-card">
        <h3>Compliance Score</h3>
        <div className="metric-value">{metrics.compliance_score || 0}%</div>
        <div className={`status ${metrics.compliance_score >= 80 ? 'good' : 'warning'}`}>
          {metrics.compliance_score >= 80 ? '✅ Good' : '⚠️ Needs Attention'}
        </div>
      </div>
      
      <div className="metric-card alert">
        <h3>High Risk Images</h3>
        <div className="metric-value">{metrics.high_risk_images || 0}</div>
      </div>
    </div>
  );
}

export default SecurityMetrics;
