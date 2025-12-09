import React, { useState } from 'react';

function TraceOptimizer() {
  const [optimization, setOptimization] = useState(null);
  const [formData, setFormData] = useState({
    service: 'payment-service',
    traces_per_second: 25,
    avg_spans_per_trace: 12,
    error_rate: 0.02
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('http://localhost:8000/api/traces/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      setOptimization(data);
    } catch (error) {
      console.error('Error optimizing traces:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: isNaN(value) ? value : Number(value)
    }));
  };

  return (
    <div className="analyzer">
      <h2>Trace Sampling Optimizer</h2>
      <p className="description">
        Find the optimal sampling rate for traces. Keep 100% of errors, intelligently sample successes.
      </p>

      <form onSubmit={handleSubmit} className="analyzer-form">
        <div className="form-group">
          <label>Service Name</label>
          <input
            type="text"
            name="service"
            value={formData.service}
            onChange={handleChange}
            placeholder="e.g., payment-service"
          />
        </div>

        <div className="form-group">
          <label>Traces per Second</label>
          <input
            type="number"
            name="traces_per_second"
            value={formData.traces_per_second}
            onChange={handleChange}
            step="0.1"
            placeholder="e.g., 25"
          />
        </div>

        <div className="form-group">
          <label>Average Spans per Trace</label>
          <input
            type="number"
            name="avg_spans_per_trace"
            value={formData.avg_spans_per_trace}
            onChange={handleChange}
            placeholder="e.g., 12"
          />
          <small>More spans = more storage needed per trace</small>
        </div>

        <div className="form-group">
          <label>Error Rate (0-1)</label>
          <input
            type="number"
            name="error_rate"
            value={formData.error_rate}
            onChange={handleChange}
            step="0.001"
            placeholder="e.g., 0.02"
          />
          <small>2% = 0.02. Errors are always sampled at 100%</small>
        </div>

        <button type="submit" className="analyze-button">
          Calculate Optimal Sampling
        </button>
      </form>

      {optimization && (
        <div className="analysis-result">
          <h3>Sampling Optimization Results</h3>
          
          <div className="result-grid">
            <div className="result-card">
              <div className="result-label">Traces per Month</div>
              <div className="result-value">{optimization.traces_per_month.toLocaleString()}</div>
            </div>

            <div className="result-card">
              <div className="result-label">Processing Cost</div>
              <div className="result-value">${optimization.processing_cost}</div>
            </div>

            <div className="result-card">
              <div className="result-label">Storage Cost</div>
              <div className="result-value">${optimization.storage_cost}</div>
            </div>

            <div className="result-card highlight">
              <div className="result-label">Current Monthly Cost</div>
              <div className="result-value large">${optimization.total_monthly_cost}</div>
              <div className="result-sublabel">At 100% sampling</div>
            </div>
          </div>

          <div className="optimization-comparison">
            <div className="comparison-section">
              <h4>Current Sampling</h4>
              <div className="sampling-rate">
                {(optimization.current_sample_rate * 100).toFixed(1)}%
              </div>
              <div className="cost-value">${optimization.total_monthly_cost}/mo</div>
            </div>

            <div className="comparison-arrow">→</div>

            <div className="comparison-section recommended">
              <h4>Recommended Sampling</h4>
              <div className="sampling-rate">
                {(optimization.optimal_sample_rate * 100).toFixed(1)}%
              </div>
              <div className="cost-value">
                ${(optimization.total_monthly_cost - optimization.potential_monthly_savings).toFixed(2)}/mo
              </div>
            </div>
          </div>

          <div className="savings-box">
            <h4>💰 Potential Monthly Savings</h4>
            <div className="savings-amount">${optimization.potential_monthly_savings}</div>
            <p>
              By sampling {(optimization.optimal_sample_rate * 100).toFixed(1)}% of traces 
              (100% errors + {((optimization.optimal_sample_rate - formData.error_rate) * 100 / (1 - formData.error_rate)).toFixed(1)}% successes)
            </p>
          </div>

          <div className="info-box">
            <strong>📊 Sampling Strategy</strong>
            <ul>
              <li>Error traces: 100% sampling (always captured)</li>
              <li>Success traces: Adaptive sampling based on cost</li>
              <li>Maintains full debugging capability for failures</li>
              <li>Reduces storage/processing for routine traffic</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default TraceOptimizer;
