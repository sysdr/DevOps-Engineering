import React from 'react';

function CostPanel({ metrics }) {
  const cost = metrics.cost || {};
  
  return (
    <div className="panel full-width">
      <h2>Cost Optimization</h2>
      
      <div className="cost-grid">
        <div className="cost-card">
          <div className="cost-label">Current Rate</div>
          <div className="cost-value">
            ${cost.cost_per_hour?.toFixed(2) || 0}/hour
          </div>
        </div>
        
        <div className="cost-card">
          <div className="cost-label">Est. Daily Cost</div>
          <div className="cost-value">
            ${cost.estimated_daily_cost?.toFixed(2) || 0}
          </div>
        </div>
        
        <div className="cost-card">
          <div className="cost-label">Preemptible Savings</div>
          <div className="cost-value savings">
            {(cost.preemptible_savings * 100)?.toFixed(0) || 0}%
          </div>
        </div>
        
        <div className="cost-card">
          <div className="cost-label">Preemption Overhead</div>
          <div className="cost-value">
            {(cost.preemption_overhead * 100)?.toFixed(1) || 0}%
          </div>
        </div>
      </div>
      
      <div className="cost-info">
        <p>💡 Using preemptible TPUs saves 70% on compute costs</p>
        <p>⚡ Smart checkpointing minimizes preemption impact</p>
      </div>
    </div>
  );
}

export default CostPanel;
