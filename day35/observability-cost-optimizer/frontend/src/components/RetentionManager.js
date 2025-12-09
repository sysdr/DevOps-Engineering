import React, { useState } from 'react';

function RetentionManager() {
  const [savings, setSavings] = useState(null);
  const [service, setService] = useState('api-gateway');
  const [currentGb, setCurrentGb] = useState(100);

  const handleOptimize = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/retention/optimize/${service}?current_gb=${currentGb}`
      );
      const data = await response.json();
      setSavings(data);
    } catch (error) {
      console.error('Error optimizing retention:', error);
    }
  };

  return (
    <div className="analyzer">
      <h2>Data Retention Optimizer</h2>
      <p className="description">
        Multi-tier storage can reduce costs by 70%. Hot data for active debugging, cold data for historical analysis.
      </p>

      <div className="analyzer-form">
        <div className="form-group">
          <label>Service Name</label>
          <input
            type="text"
            value={service}
            onChange={(e) => setService(e.target.value)}
            placeholder="e.g., api-gateway"
          />
        </div>

        <div className="form-group">
          <label>Current Monthly Data (GB)</label>
          <input
            type="number"
            value={currentGb}
            onChange={(e) => setCurrentGb(Number(e.target.value))}
            placeholder="e.g., 100"
          />
          <small>Total data volume per month</small>
        </div>

        <button onClick={handleOptimize} className="analyze-button">
          Calculate Retention Savings
        </button>
      </div>

      {savings && (
        <div className="analysis-result">
          <h3>Retention Optimization Results</h3>

          <div className="retention-comparison">
            <div className="retention-option current">
              <h4>Current Setup</h4>
              <div className="retention-details">
                <p>All data in hot storage</p>
                <p className="retention-period">30 days total</p>
                <div className="cost-display">
                  ${savings.current_monthly_cost}/mo
                </div>
              </div>
            </div>

            <div className="retention-arrow">
              <span>Optimize</span>
              <span className="arrow">→</span>
            </div>

            <div className="retention-option optimized">
              <h4>Multi-Tier Retention</h4>
              <div className="retention-details">
                <div className="tier-breakdown">
                  <div className="tier">
                    <span className="tier-name">🔥 Hot</span>
                    <span>{savings.retention_policy.hot}</span>
                  </div>
                  <div className="tier">
                    <span className="tier-name">🌡️ Warm</span>
                    <span>{savings.retention_policy.warm}</span>
                  </div>
                  <div className="tier">
                    <span className="tier-name">❄️ Cold</span>
                    <span>{savings.retention_policy.cold}</span>
                  </div>
                  <div className="tier">
                    <span className="tier-name">🗄️ Archive</span>
                    <span>{savings.retention_policy.archive}</span>
                  </div>
                </div>
                <div className="cost-display optimized">
                  ${savings.optimized_monthly_cost}/mo
                </div>
              </div>
            </div>
          </div>

          <div className="savings-summary">
            <div className="summary-card">
              <div className="summary-label">Monthly Savings</div>
              <div className="summary-value">${savings.monthly_savings}</div>
            </div>
            <div className="summary-card">
              <div className="summary-label">Cost Reduction</div>
              <div className="summary-value">{savings.savings_percentage}%</div>
            </div>
            <div className="summary-card">
              <div className="summary-label">Annual Savings</div>
              <div className="summary-value">${(savings.monthly_savings * 12).toFixed(2)}</div>
            </div>
          </div>

          <div className="info-box">
            <strong>📚 Storage Tier Strategy</strong>
            <ul>
              <li><strong>Hot:</strong> SSD storage, instant queries for active debugging</li>
              <li><strong>Warm:</strong> Compressed SSD for recent incident investigation</li>
              <li><strong>Cold:</strong> Object storage for historical trend analysis</li>
              <li><strong>Archive:</strong> Glacier-class for compliance and yearly reviews</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default RetentionManager;
