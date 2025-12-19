import React, { useState } from 'react';
import axios from 'axios';

const PredictionDemo = () => {
  const [predicting, setPredicting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const makePrediction = async () => {
    setPredicting(true);
    setError(null);
    
    try {
      // Generate random features for demonstration
      const features = Array.from({ length: 20 }, () => Math.random() * 2 - 1);
      
      const response = await axios.post('http://localhost:8001/predict', {
        model_name: 'fraud_detection_demo_random_forest',
        version: 'Production',
        features: [features]
      });

      setResult(response.data);
      
      // Log to monitoring
      await axios.post('http://localhost:8002/log', {
        model_name: response.data.model_name,
        model_version: response.data.model_version,
        features: features,
        prediction: response.data.predictions[0],
        timestamp: response.data.timestamp,
        latency_ms: response.data.latency_ms
      });
      
    } catch (err) {
      setError('Prediction failed. Make sure model is registered in Production stage.');
    } finally {
      setPredicting(false);
    }
  };

  return (
    <div>
      <div className="card">
        <h2>Live Prediction Demo</h2>
        
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <p style={{ color: '#6b7280', marginBottom: '2rem' }}>
            Generate a prediction using random features to test the model serving pipeline
          </p>
          
          <button
            className="btn btn-primary"
            onClick={makePrediction}
            disabled={predicting}
            style={{ fontSize: '1.1rem', padding: '1rem 2rem' }}
          >
            {predicting ? 'Predicting...' : '🎯 Make Prediction'}
          </button>
        </div>

        {error && (
          <div className="error" style={{ marginTop: '1rem' }}>
            {error}
          </div>
        )}

        {result && (
          <div style={{ marginTop: '2rem', padding: '2rem', background: 'rgba(16, 185, 129, 0.05)', borderRadius: '12px', borderLeft: '4px solid #10b981' }}>
            <h3 style={{ marginBottom: '1rem' }}>Prediction Result</h3>
            <div className="grid">
              <div className="metric-card">
                <div className="metric-label">Prediction</div>
                <div className="metric-value" style={{ color: result.predictions[0] === 1 ? '#ef4444' : '#10b981' }}>
                  {result.predictions[0] === 1 ? 'Fraud' : 'Normal'}
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Model Version</div>
                <div className="metric-value" style={{ fontSize: '1.2rem' }}>{result.model_version}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Latency</div>
                <div className="metric-value" style={{ fontSize: '1.2rem' }}>{result.latency_ms}ms</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Timestamp</div>
                <div className="metric-value" style={{ fontSize: '1rem' }}>
                  {new Date(result.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PredictionDemo;
