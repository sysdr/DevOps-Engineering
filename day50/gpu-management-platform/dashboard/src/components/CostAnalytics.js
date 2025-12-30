import React from 'react';
import './CostAnalytics.css';

function CostAnalytics({ analytics }) {
  return (
    <div className="cost-analytics">
      <h2>Cost Optimization Analytics</h2>
      
      <div className="cost-summary">
        <div className="cost-card current">
          <h3>Current Cost</h3>
          <div className="cost-amount">${analytics.total_cost_current.toFixed(2)}</div>
          <div className="cost-period">per hour</div>
        </div>
        
        <div className="cost-card optimized">
          <h3>Optimized Cost</h3>
          <div className="cost-amount">${analytics.potential_cost_optimized.toFixed(2)}</div>
          <div className="cost-period">per hour</div>
        </div>
        
        <div className="cost-card savings">
          <h3>Potential Savings</h3>
          <div className="cost-amount">${analytics.savings_amount.toFixed(2)}</div>
          <div className="cost-percentage">{analytics.savings_percentage.toFixed(1)}% reduction</div>
        </div>
      </div>

      <div className="recommendations">
        <h3>💡 Optimization Recommendations</h3>
        <div className="recommendation-list">
          {analytics.recommendations.map((rec, index) => (
            <div key={index} className="recommendation-item">
              <div className="recommendation-icon">→</div>
              <div className="recommendation-text">{rec}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="cost-breakdown">
        <h3>Cost Breakdown</h3>
        <div className="breakdown-chart">
          <div className="chart-bar">
            <div className="bar-label">Current Spend</div>
            <div className="bar-visual">
              <div 
                className="bar-fill current-fill" 
                style={{ width: '100%' }}
              >
                ${analytics.total_cost_current.toFixed(2)}
              </div>
            </div>
          </div>
          <div className="chart-bar">
            <div className="bar-label">Optimized Spend</div>
            <div className="bar-visual">
              <div 
                className="bar-fill optimized-fill" 
                style={{ 
                  width: `${(analytics.potential_cost_optimized / analytics.total_cost_current * 100)}%` 
                }}
              >
                ${analytics.potential_cost_optimized.toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CostAnalytics;
