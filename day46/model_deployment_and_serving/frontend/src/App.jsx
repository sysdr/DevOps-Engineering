import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [models, setModels] = useState([]);
  const [trafficSplit, setTrafficSplit] = useState({ v1: 90, v2: 10 });
  const [metrics, setMetrics] = useState({});
  const [predictionInput, setPredictionInput] = useState('5.1,3.5,1.4,0.2');
  const [predictionResult, setPredictionResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchModels();
    fetchTrafficSplit();
    fetchMetrics();
    
    const interval = setInterval(() => {
      fetchMetrics();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchModels = async () => {
    try {
      const response = await fetch(`${API_BASE}/v1/models`);
      const data = await response.json();
      setModels(data.models);
    } catch (error) {
      console.error('Error fetching models:', error);
    }
  };

  const fetchTrafficSplit = async () => {
    try {
      const response = await fetch(`${API_BASE}/v1/traffic-split`);
      const data = await response.json();
      setTrafficSplit(data);
    } catch (error) {
      console.error('Error fetching traffic split:', error);
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE}/v1/compare-models`);
      const data = await response.json();
      setMetrics(data.comparison);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const updateTrafficSplit = async () => {
    try {
      await fetch(`${API_BASE}/v1/traffic-split`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trafficSplit)
      });
      alert('Traffic split updated successfully');
    } catch (error) {
      alert('Error updating traffic split');
    }
  };

  const makePrediction = async () => {
    setLoading(true);
    try {
      const features = predictionInput.split(',').map(f => parseFloat(f.trim()));
      const response = await fetch(`${API_BASE}/v1/models/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instances: [features] })
      });
      const data = await response.json();
      setPredictionResult(data);
      fetchMetrics();
    } catch (error) {
      alert('Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  const classNames = ['Setosa', 'Versicolor', 'Virginica'];

  return (
    <div style={{ 
      padding: '40px',
      maxWidth: '1400px',
      margin: '0 auto',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      background: 'linear-gradient(135deg, #3b82f6 0%, #10b981 100%)',
      minHeight: '100vh'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '20px',
        padding: '40px',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
      }}>
        <h1 style={{ 
          margin: '0 0 10px 0',
          fontSize: '36px',
          background: 'linear-gradient(135deg, #3b82f6 0%, #10b981 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          fontWeight: '800'
        }}>
          Model Serving Platform
        </h1>
        <p style={{ 
          margin: '0 0 40px 0',
          color: '#64748b',
          fontSize: '16px'
        }}>
          Production ML Deployment with A/B Testing
        </p>

        {/* Model Deployment Section */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '20px',
          marginBottom: '30px'
        }}>
          {models.map(model => (
            <div key={model.version} style={{
              border: '2px solid #e2e8f0',
              borderRadius: '12px',
              padding: '20px',
              background: model.quantized ? '#f0fdf4' : '#faf5ff'
            }}>
              <h3 style={{ 
                margin: '0 0 15px 0',
                color: '#1e293b',
                fontSize: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px'
              }}>
                <span style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: model.status === 'ready' ? '#22c55e' : '#94a3b8',
                  display: 'inline-block'
                }}></span>
                {model.version}
                {model.quantized && (
                  <span style={{
                    fontSize: '12px',
                    background: '#22c55e',
                    color: 'white',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontWeight: '600'
                  }}>QUANTIZED</span>
                )}
              </h3>
              <div style={{ fontSize: '14px', color: '#64748b' }}>
                <div style={{ marginBottom: '8px' }}>
                  <strong>Framework:</strong> {model.framework}
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>Size:</strong> {model.size_mb} MB
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>Accuracy:</strong> {(model.accuracy * 100).toFixed(1)}%
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>Status:</strong> <span style={{ color: '#22c55e', fontWeight: '600' }}>{model.status}</span>
                </div>
                {metrics[model.version] && (
                  <>
                    <div style={{ marginBottom: '8px' }}>
                      <strong>Predictions:</strong> {metrics[model.version].total_predictions}
                    </div>
                    <div style={{ marginBottom: '8px' }}>
                      <strong>Latency:</strong> {metrics[model.version].avg_latency_ms.toFixed(2)} ms
                    </div>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* A/B Testing Section */}
        <div style={{
          border: '2px solid #e2e8f0',
          borderRadius: '12px',
          padding: '30px',
          marginBottom: '30px',
          background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)'
        }}>
          <h2 style={{ margin: '0 0 20px 0', color: '#1e293b', fontSize: '24px' }}>
            A/B Testing Configuration
          </h2>
          <div style={{ display: 'flex', gap: '20px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ flex: '1', minWidth: '200px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#1e293b' }}>
                Model v1 Traffic %
              </label>
              <input
                type="number"
                value={trafficSplit.v1}
                onChange={(e) => setTrafficSplit({ ...trafficSplit, v1: parseInt(e.target.value), v2: 100 - parseInt(e.target.value) })}
                min="0"
                max="100"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '2px solid #d97706',
                  borderRadius: '8px',
                  fontSize: '16px'
                }}
              />
            </div>
            <div style={{ flex: '1', minWidth: '200px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#1e293b' }}>
                Model v2 Traffic %
              </label>
              <input
                type="number"
                value={trafficSplit.v2}
                onChange={(e) => setTrafficSplit({ ...trafficSplit, v2: parseInt(e.target.value), v1: 100 - parseInt(e.target.value) })}
                min="0"
                max="100"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '2px solid #d97706',
                  borderRadius: '8px',
                  fontSize: '16px'
                }}
              />
            </div>
            <button
              onClick={updateTrafficSplit}
              style={{
                padding: '12px 30px',
                background: '#d97706',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer',
                marginTop: '30px'
              }}
            >
              Update Split
            </button>
          </div>
          <div style={{
            marginTop: '20px',
            padding: '15px',
            background: 'white',
            borderRadius: '8px',
            fontSize: '14px',
            color: '#64748b'
          }}>
            <strong>Current Split:</strong> {trafficSplit.v1}% → v1 | {trafficSplit.v2}% → v2
          </div>
        </div>

        {/* Prediction Testing Section */}
        <div style={{
          border: '2px solid #e2e8f0',
          borderRadius: '12px',
          padding: '30px',
          background: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)'
        }}>
          <h2 style={{ margin: '0 0 20px 0', color: '#1e293b', fontSize: '24px' }}>
            Test Model Inference
          </h2>
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#1e293b' }}>
              Iris Features (sepal_length, sepal_width, petal_length, petal_width)
            </label>
            <input
              type="text"
              value={predictionInput}
              onChange={(e) => setPredictionInput(e.target.value)}
              placeholder="5.1,3.5,1.4,0.2"
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #3b82f6',
                borderRadius: '8px',
                fontSize: '16px'
              }}
            />
          </div>
          <button
            onClick={makePrediction}
            disabled={loading}
            style={{
              padding: '12px 30px',
              background: loading ? '#94a3b8' : '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Predicting...' : 'Make Prediction'}
          </button>

          {predictionResult && (
            <div style={{
              marginTop: '20px',
              padding: '20px',
              background: 'white',
              borderRadius: '8px',
              border: '2px solid #22c55e'
            }}>
              <h3 style={{ margin: '0 0 15px 0', color: '#1e293b', fontSize: '18px' }}>
                Prediction Result
              </h3>
              <div style={{ fontSize: '14px', color: '#64748b' }}>
                <div style={{ marginBottom: '10px' }}>
                  <strong>Class:</strong> <span style={{ fontSize: '20px', color: '#22c55e', fontWeight: '700' }}>
                    {classNames[predictionResult.predictions[0]]}
                  </span>
                </div>
                <div style={{ marginBottom: '10px' }}>
                  <strong>Model Version:</strong> {predictionResult.model_version}
                </div>
                <div style={{ marginBottom: '10px' }}>
                  <strong>Latency:</strong> {predictionResult.latency_ms.toFixed(2)} ms
                </div>
                <div>
                  <strong>Timestamp:</strong> {new Date(predictionResult.timestamp).toLocaleString()}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
