import React, { useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

const ExplainabilityDemo = () => {
  const [inputData, setInputData] = useState({
    credit_score: 620,
    income: 55000,
    debt_ratio: 0.45,
    age: 35
  });
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Calculate prediction based on input data
  const calculatePrediction = (data) => {
    // Simple scoring model: base score + feature contributions
    let score = 0.5; // base value
    
    // Credit score contribution (normalized to 0-1 scale)
    const creditScoreNorm = Math.max(0, Math.min(1, (data.credit_score - 300) / 400));
    score += (creditScoreNorm - 0.5) * 0.3;
    
    // Income contribution
    const incomeNorm = Math.max(0, Math.min(1, (data.income - 20000) / 100000));
    score += (incomeNorm - 0.5) * 0.2;
    
    // Debt ratio (negative impact)
    score -= (data.debt_ratio - 0.3) * 0.4;
    
    // Age contribution (optimal around 40-50)
    const ageNorm = Math.max(0, Math.min(1, Math.abs(data.age - 45) / 30));
    score += (1 - ageNorm - 0.5) * 0.1;
    
    // Clamp to [0, 1]
    return Math.max(0, Math.min(1, score));
  };

  const generateExplanation = async () => {
    // Validate inputs
    if (!inputData.credit_score || inputData.credit_score < 300 || inputData.credit_score > 850) {
      setError('Credit score must be between 300 and 850');
      return;
    }
    if (!inputData.income || inputData.income < 0) {
      setError('Income must be a positive number');
      return;
    }
    if (inputData.debt_ratio < 0 || inputData.debt_ratio > 1) {
      setError('Debt-to-income ratio must be between 0 and 1');
      return;
    }
    if (!inputData.age || inputData.age < 18 || inputData.age > 100) {
      setError('Age must be between 18 and 100');
      return;
    }

    setLoading(true);
    setError(null);
    setExplanation(null);
    
    try {
      const prediction = calculatePrediction(inputData);
      const response = await axios.post('http://localhost:8003/api/v1/explain/generate', {
        model_id: 'loan-model-v1',
        prediction_id: `pred-${Date.now()}`,
        input_data: inputData,
        prediction: prediction
      });
      setExplanation(response.data);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to generate explanation. Please try again.';
      setError(errorMsg);
      console.error('Failed to generate explanation:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateInput = (field, value) => {
    const numValue = value === '' ? '' : parseFloat(value);
    if (numValue === '' || !isNaN(numValue)) {
      setInputData({ ...inputData, [field]: numValue });
      setError(null); // Clear error when user starts typing
    }
  };

  const chartData = explanation?.shap_values?.feature_contributions 
    ? Object.entries(explanation.shap_values.feature_contributions).map(([feature, value]) => ({
        feature: feature.replace(/_/g, ' '),
        contribution: value
      }))
    : [];

  return (
    <div>
      <h2 className="section-title">AI Explainability Engine</h2>

      <div className="card">
        <h3>Loan Application Example</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '15px', marginBottom: '20px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600' }}>Credit Score</label>
            <input
              type="number"
              value={inputData.credit_score}
              onChange={(e) => updateInput('credit_score', e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                fontSize: '1em',
                borderRadius: '6px',
                border: '2px solid #dee2e6'
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600' }}>Annual Income ($)</label>
            <input
              type="number"
              value={inputData.income}
              onChange={(e) => updateInput('income', e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                fontSize: '1em',
                borderRadius: '6px',
                border: '2px solid #dee2e6'
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600' }}>Debt-to-Income Ratio</label>
            <input
              type="number"
              step="0.01"
              value={inputData.debt_ratio}
              onChange={(e) => updateInput('debt_ratio', e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                fontSize: '1em',
                borderRadius: '6px',
                border: '2px solid #dee2e6'
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600' }}>Age</label>
            <input
              type="number"
              value={inputData.age}
              onChange={(e) => updateInput('age', e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                fontSize: '1em',
                borderRadius: '6px',
                border: '2px solid #dee2e6'
              }}
            />
          </div>
        </div>
        <button className="btn" onClick={generateExplanation} disabled={loading}>
          {loading ? 'Generating...' : 'Generate Explanation'}
        </button>
        {error && (
          <div className="error" style={{ marginTop: '15px' }}>
            {error}
          </div>
        )}
      </div>

      {explanation && (
        <>
          <div className="card">
            <h3>Prediction Summary</h3>
            <div style={{ 
              padding: '15px', 
              background: explanation.shap_values?.prediction >= 0.5 ? '#d3f9d8' : '#ffe0e0',
              borderRadius: '8px',
              borderLeft: `4px solid ${explanation.shap_values?.prediction >= 0.5 ? '#51cf66' : '#ff6b6b'}`,
              fontSize: '1.1em',
              fontWeight: 'bold',
              marginBottom: '20px'
            }}>
              Approval Probability: {(explanation.shap_values?.prediction * 100).toFixed(1)}%
              {explanation.shap_values?.prediction >= 0.5 ? ' ✓ Likely Approved' : ' ✗ Likely Rejected'}
            </div>
          </div>

          <div className="card">
            <h3>Natural Language Explanation</h3>
            <div style={{ 
              padding: '15px', 
              background: '#e7f5ff', 
              borderRadius: '8px',
              borderLeft: '4px solid #1c7ed6',
              fontSize: '1.05em',
              lineHeight: '1.6'
            }}>
              {explanation.natural_language}
            </div>
          </div>

          <div className="card">
            <h3>Feature Contribution Analysis (SHAP Values)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="feature" type="category" width={100} />
                <Tooltip />
                <Legend />
                <Bar dataKey="contribution" name="Impact on Score">
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.contribution > 0 ? '#51cf66' : '#ff6b6b'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div style={{ marginTop: '10px', fontSize: '0.9em', color: '#6c757d' }}>
              <p>🟢 Positive values increase approval likelihood | 🔴 Negative values decrease it</p>
            </div>
          </div>

          <div className="card">
            <h3>Feature Ranking</h3>
            {explanation.feature_ranking && explanation.feature_ranking.length > 0 ? (
              explanation.feature_ranking.map(([feature, value], idx) => (
                <div key={idx} className="metric-row">
                  <span className="metric-label">{idx + 1}. {feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                  <span className={`metric-value ${value > 0 ? 'pass' : 'fail'}`}>
                    {value > 0 ? '+' : ''}{value.toFixed(4)}
                  </span>
                </div>
              ))
            ) : (
              <div style={{ padding: '10px', color: '#6c757d', fontStyle: 'italic' }}>
                No feature ranking available
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default ExplainabilityDemo;
