import React, { useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './Panel.css';

function ExplainabilityPanel() {
  const [predictionId, setPredictionId] = useState('');
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);

  const generateExplanation = async (type) => {
    if (!predictionId.trim()) {
      alert('Please enter a prediction ID');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`http://localhost:8003/explain/${type}`, {
        prediction_id: predictionId,
        model_id: 'default'
      });
      setExplanation(response.data);
    } catch (error) {
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    }
    setLoading(false);
  };

  const getChartData = () => {
    if (!explanation?.explanation) return [];
    const values = explanation.explanation.shap_values || explanation.explanation.weights || {};
    return Object.entries(values).map(([feature, value]) => ({
      feature,
      contribution: Math.abs(value),
      positive: value > 0
    }));
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🔍 Model Explainability</h2>
      </div>

      <div className="input-section">
        <input
          type="text"
          placeholder="Enter Prediction ID (e.g., pred-1234567890)"
          value={predictionId}
          onChange={(e) => setPredictionId(e.target.value)}
          className="text-input"
        />
        <div className="button-group">
          <button 
            onClick={() => generateExplanation('shap')} 
            className="action-button"
            disabled={loading}
          >
            Generate SHAP Explanation
          </button>
          <button 
            onClick={() => generateExplanation('lime')} 
            className="action-button secondary"
            disabled={loading}
          >
            Generate LIME Explanation
          </button>
        </div>
      </div>

      {explanation && (
        <div className="explanation-results">
          <div className="result-header">
            <h3>{explanation.explanation_type.toUpperCase()} Explanation</h3>
            <span className="prediction-id">ID: {explanation.prediction_id}</span>
          </div>

          {explanation.explanation.base_value !== undefined && (
            <div className="base-value">
              <span>Base Value:</span>
              <strong>{explanation.explanation.base_value.toFixed(4)}</strong>
            </div>
          )}

          {explanation.explanation.predicted_value !== undefined && (
            <div className="predicted-value">
              <span>Predicted Value:</span>
              <strong>{explanation.explanation.predicted_value.toFixed(4)}</strong>
            </div>
          )}

          <div className="chart-container">
            <h4>Feature Contributions</h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getChartData()}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis dataKey="feature" stroke="#666" />
                <YAxis stroke="#666" />
                <Tooltip 
                  contentStyle={{ background: '#fff', border: '1px solid #ddd', borderRadius: '8px' }}
                />
                <Bar dataKey="contribution" fill="#667eea" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}

export default ExplainabilityPanel;
