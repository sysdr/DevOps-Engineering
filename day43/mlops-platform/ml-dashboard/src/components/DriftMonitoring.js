import React, { useState, useEffect } from 'react';
import axios from 'axios';

const DriftMonitoring = () => {
  const [driftReport, setDriftReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [baselineSet, setBaselineSet] = useState(false);

  useEffect(() => {
    fetchDrift();
    const interval = setInterval(fetchDrift, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchDrift = async () => {
    try {
      const response = await axios.get('http://localhost:8002/drift/fraud_detection_demo_random_forest');
      setDriftReport(response.data);
      setLoading(false);
    } catch (err) {
      setLoading(false);
    }
  };

  const setBaseline = async () => {
    try {
      // Generate synthetic baseline data
      const baselineFeatures = Array.from({ length: 100 }, () =>
        Array.from({ length: 20 }, () => Math.random() * 2 - 1)
      );
      
      await axios.post('http://localhost:8002/baseline/fraud_detection_demo_random_forest', {
        features: baselineFeatures
      });
      
      setBaselineSet(true);
      fetchDrift();
    } catch (err) {
      console.error('Failed to set baseline:', err);
    }
  };

  if (loading) {
    return <div className="card"><div className="loading">Loading drift monitoring...</div></div>;
  }

  return (
    <div>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>Model Drift Monitoring</h2>
          {!baselineSet && (
            <button className="btn btn-secondary" onClick={setBaseline}>
              Set Baseline
            </button>
          )}
        </div>

        <div className="grid" style={{ marginTop: '2rem' }}>
          <div className="metric-card">
            <div className="metric-label">Drift Score</div>
            <div className="metric-value">{driftReport?.drift_score?.toFixed(4) || 'N/A'}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Drift Status</div>
            <div className="metric-value" style={{ color: driftReport?.drift_detected ? '#ef4444' : '#10b981' }}>
              {driftReport?.drift_detected ? 'Detected' : 'Normal'}
            </div>
          </div>
        </div>

        {driftReport?.feature_drifts && Object.keys(driftReport.feature_drifts).length > 0 && (
          <div style={{ marginTop: '2rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>Feature-Level Drift</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '1rem' }}>
              {Object.entries(driftReport.feature_drifts).slice(0, 10).map(([feature, score]) => (
                <div key={feature} className="metric-card" style={{ padding: '1rem' }}>
                  <div className="metric-label" style={{ fontSize: '0.8rem' }}>{feature}</div>
                  <div className="metric-value" style={{ fontSize: '1.2rem', color: score > 0.3 ? '#ef4444' : '#10b981' }}>
                    {score.toFixed(3)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {driftReport?.drift_detected && (
          <div style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', borderLeft: '4px solid #ef4444' }}>
            <strong>⚠️ Drift Alert:</strong> Significant distribution shift detected. Consider retraining the model with recent data.
          </div>
        )}
      </div>
    </div>
  );
};

export default DriftMonitoring;
