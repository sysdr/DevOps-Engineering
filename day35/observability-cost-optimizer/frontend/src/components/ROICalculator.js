import React, { useState, useEffect } from 'react';

function ROICalculator() {
  const [roi, setRoi] = useState(null);
  const [metrics, setMetrics] = useState({
    mttr_hours: 0,
    incidents_prevented: 0,
    optimization_savings: 0
  });

  useEffect(() => {
    fetchROI();
  }, []);

  const fetchROI = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/roi/calculate');
      const data = await response.json();
      setRoi(data);
    } catch (error) {
      console.error('Error fetching ROI:', error);
    }
  };

  const handleUpdate = async () => {
    try {
      await fetch('http://localhost:8000/api/roi/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(metrics)
      });
      
      // Reset metrics
      setMetrics({
        mttr_hours: 0,
        incidents_prevented: 0,
        optimization_savings: 0
      });
      
      // Fetch updated ROI
      fetchROI();
    } catch (error) {
      console.error('Error updating ROI:', error);
    }
  };

  const handleChange = (field, value) => {
    setMetrics(prev => ({
      ...prev,
      [field]: Number(value)
    }));
  };

  return (
    <div className="analyzer">
      <h2>Observability ROI Calculator</h2>
      <p className="description">
        Measure the business value of your observability investment against its costs.
      </p>

      {roi && (
        <div className="roi-overview">
          <div className="roi-header">
            <div className="roi-status">
              <div className={`status-badge ${roi.roi_status.toLowerCase()}`}>
                {roi.roi_status}
              </div>
              <div className="roi-percentage">
                {roi.roi_percentage >= 0 ? '+' : ''}{roi.roi_percentage}% ROI
              </div>
            </div>
          </div>

          <div className="roi-summary">
            <div className="roi-card cost">
              <div className="card-label">Monthly Cost</div>
              <div className="card-value">${roi.monthly_observability_cost}</div>
            </div>
            
            <div className="roi-arrow">vs</div>
            
            <div className="roi-card value">
              <div className="card-label">Monthly Value</div>
              <div className="card-value">${roi.value_metrics.total_value}</div>
            </div>
          </div>

          <div className="value-breakdown">
            <h3>Value Breakdown</h3>
            <div className="breakdown-grid">
              <div className="breakdown-item">
                <div className="item-icon">⏱️</div>
                <div className="item-content">
                  <div className="item-label">MTTR Reduction Value</div>
                  <div className="item-value">${roi.value_metrics.mttr_reduction_value}</div>
                  <div className="item-description">Faster incident resolution</div>
                </div>
              </div>

              <div className="breakdown-item">
                <div className="item-icon">🛡️</div>
                <div className="item-content">
                  <div className="item-label">Incident Prevention Value</div>
                  <div className="item-value">${roi.value_metrics.incident_prevention_value}</div>
                  <div className="item-description">Outages prevented</div>
                </div>
              </div>

              <div className="breakdown-item">
                <div className="item-icon">⚡</div>
                <div className="item-content">
                  <div className="item-label">Optimization Value</div>
                  <div className="item-value">${roi.value_metrics.optimization_value}</div>
                  <div className="item-description">Performance improvements</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="roi-input-section">
        <h3>Update Value Metrics</h3>
        
        <div className="analyzer-form">
          <div className="form-group">
            <label>MTTR Reduction (hours)</label>
            <input
              type="number"
              value={metrics.mttr_hours}
              onChange={(e) => handleChange('mttr_hours', e.target.value)}
              step="0.5"
              placeholder="e.g., 2.5"
            />
            <small>Hours saved in debugging/incident resolution</small>
          </div>

          <div className="form-group">
            <label>Incidents Prevented</label>
            <input
              type="number"
              value={metrics.incidents_prevented}
              onChange={(e) => handleChange('incidents_prevented', e.target.value)}
              placeholder="e.g., 1"
            />
            <small>Outages caught before user impact</small>
          </div>

          <div className="form-group">
            <label>Optimization Savings ($)</label>
            <input
              type="number"
              value={metrics.optimization_savings}
              onChange={(e) => handleChange('optimization_savings', e.target.value)}
              placeholder="e.g., 5000"
            />
            <small>Cost saved from performance optimizations identified</small>
          </div>

          <button onClick={handleUpdate} className="analyze-button">
            Update ROI Metrics
          </button>
        </div>
      </div>

      <div className="info-box">
        <strong>💡 Understanding ROI</strong>
        <p>
          <strong>Positive ROI:</strong> Observability value exceeds costs - you're getting good return<br/>
          <strong>Negative ROI:</strong> Costs exceed value - time to optimize or prove more value<br/>
          <strong>Break-even:</strong> ${roi?.break_even_cost || 0} - max cost for current value level
        </p>
      </div>
    </div>
  );
}

export default ROICalculator;
