import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Area, ComposedChart, ResponsiveContainer } from 'recharts';

function PredictionPanel() {
  const [predictions, setPredictions] = useState(null);
  const [metric, setMetric] = useState('cpu_usage_percent');
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPrediction();
    const interval = setInterval(fetchPrediction, 30000);
    return () => clearInterval(interval);
  }, [metric]);

  const fetchPrediction = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/predictions/${metric}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      // Check if prediction data is available
      if (data.status === 'success' && data.predicted_value != null) {
        setPredictions(data);
        setError(null);
      } else {
        // Insufficient data or model not trained - show message
        setError(data.message || 'Insufficient data for predictions');
        setPredictions(null);
      }
    } catch (error) {
      console.error('Error fetching prediction:', error);
      setError('Failed to fetch prediction');
      setPredictions(null);
    }
  };

  return (
    <div className="prediction-panel">
      <select value={metric} onChange={(e) => setMetric(e.target.value)}>
        <option value="cpu_usage_percent">CPU Usage</option>
        <option value="memory_usage_percent">Memory Usage</option>
        <option value="network_bytes_sent">Network Traffic</option>
      </select>

      {predictions ? (
        <div className="prediction-display">
          <div className="prediction-value">
            <div className="label">Predicted (15min)</div>
            <div className="value">
              {predictions.predicted_value != null ? predictions.predicted_value.toFixed(2) : 'N/A'}
            </div>
          </div>
          
          <div className="confidence-range">
            <div className="range-label">Confidence Range</div>
            <div className="range-values">
              <span>
                {predictions.confidence_lower != null ? predictions.confidence_lower.toFixed(2) : 'N/A'}
              </span>
              <span> - </span>
              <span>
                {predictions.confidence_upper != null ? predictions.confidence_upper.toFixed(2) : 'N/A'}
              </span>
            </div>
          </div>

          <div className="prediction-time">
            Updated: {predictions.timestamp ? new Date(predictions.timestamp).toLocaleTimeString() : 'N/A'}
          </div>
        </div>
      ) : error ? (
        <div className="prediction-error" style={{ padding: '20px', color: '#888', textAlign: 'center' }}>
          <div>{error}</div>
          <div style={{ fontSize: '0.9em', marginTop: '10px' }}>
            Collecting data... Predictions will be available once enough metrics are collected.
          </div>
        </div>
      ) : (
        <div className="prediction-loading" style={{ padding: '20px', color: '#888', textAlign: 'center' }}>
          Loading predictions...
        </div>
      )}
    </div>
  );
}

export default PredictionPanel;
