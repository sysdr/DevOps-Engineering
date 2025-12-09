import React, { useState, useEffect } from 'react';

function Recommendations() {
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecommendations();
    const interval = setInterval(fetchRecommendations, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchRecommendations = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/recommendations');
      const data = await response.json();
      setRecommendations(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    }
  };

  if (loading) return <div className="loading">Loading recommendations...</div>;

  const getSeverityColor = (severity) => {
    const colors = {
      'HIGH': '#ff4757',
      'MEDIUM': '#ffa502',
      'LOW': '#26de81'
    };
    return colors[severity] || '#95afc0';
  };

  const getTypeIcon = (type) => {
    const icons = {
      'HIGH_CARDINALITY': '📊',
      'AGGRESSIVE_SAMPLING': '🎯',
      'ALERT_OPTIMIZATION': '🔔',
      'RETENTION_POLICY': '💾',
      'DATA_QUALITY': '✅'
    };
    return icons[type] || '💡';
  };

  return (
    <div className="recommendations">
      <div className="recommendations-header">
        <h2>Cost Optimization Recommendations</h2>
        <div className="total-savings">
          <span>Total Potential Savings</span>
          <span className="savings-amount">
            ${recommendations?.total_potential_savings?.toFixed(2) || 0}/mo
          </span>
        </div>
      </div>

      {recommendations?.recommendations.length === 0 ? (
        <div className="no-recommendations">
          <div className="success-icon">✅</div>
          <h3>All Optimized!</h3>
          <p>No cost optimization opportunities found. Your observability setup is efficient.</p>
        </div>
      ) : (
        <div className="recommendations-list">
          {recommendations?.recommendations.map((rec, index) => (
            <div 
              key={index} 
              className="recommendation-card"
              style={{ borderLeftColor: getSeverityColor(rec.severity) }}
            >
              <div className="rec-header">
                <div className="rec-icon">{getTypeIcon(rec.type)}</div>
                <div className="rec-title">
                  <h3>{rec.service}</h3>
                  <span className={`severity-badge ${rec.severity.toLowerCase()}`}>
                    {rec.severity}
                  </span>
                </div>
                <div className="rec-savings">
                  <div className="savings-label">Potential Savings</div>
                  <div className="savings-value">${rec.potential_savings}/mo</div>
                </div>
              </div>

              <div className="rec-body">
                <div className="rec-type">{rec.type.replace(/_/g, ' ')}</div>
                <p className="rec-message">{rec.message}</p>
              </div>

              <div className="rec-actions">
                <button className="action-button primary">
                  Apply Optimization
                </button>
                <button className="action-button secondary">
                  Learn More
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="optimization-tips">
        <h3>🎓 Quick Optimization Tips</h3>
        <div className="tips-grid">
          <div className="tip-card">
            <h4>Reduce Cardinality</h4>
            <ul>
              <li>Remove user_id, request_id from metrics</li>
              <li>Use fixed label value sets</li>
              <li>Aggregate rare values to "other"</li>
            </ul>
          </div>

          <div className="tip-card">
            <h4>Smart Sampling</h4>
            <ul>
              <li>100% of errors, always</li>
              <li>1-10% of successful requests</li>
              <li>Increase sampling for rare endpoints</li>
            </ul>
          </div>

          <div className="tip-card">
            <h4>Retention Strategy</h4>
            <ul>
              <li>7 days hot for active debugging</li>
              <li>30 days warm for recent incidents</li>
              <li>90 days cold for trend analysis</li>
            </ul>
          </div>

          <div className="tip-card">
            <h4>Alert Quality</h4>
            <ul>
              <li>Deduplicate similar alerts</li>
              <li>Throttle low-priority notifications</li>
              <li>Use webhooks over SMS when possible</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Recommendations;
