import React, { useState } from 'react';
import axios from 'axios';

const BiasAnalysis = () => {
  const [modelId, setModelId] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyzeModel = async () => {
    if (!modelId.trim()) {
      setError('Please enter a model ID');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('http://localhost:8001/api/v1/bias/analyze', {
        model_id: modelId,
        dataset_id: 'test-dataset-1'
      });
      setResults(response.data);
    } catch (err) {
      setError('Failed to analyze model: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="section-title">Bias Detection & Analysis</h2>
      
      <div className="card">
        <div style={{ marginBottom: '20px' }}>
          <input
            type="text"
            value={modelId}
            onChange={(e) => setModelId(e.target.value)}
            placeholder="Enter Model ID (e.g., loan-model-v1)"
            style={{
              width: '300px',
              padding: '10px',
              fontSize: '1em',
              borderRadius: '6px',
              border: '2px solid #dee2e6',
              marginRight: '10px'
            }}
          />
          <button className="btn" onClick={analyzeModel} disabled={loading}>
            {loading ? 'Analyzing...' : 'Run Bias Analysis'}
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {results && (
          <div>
            <div className={results.passed ? 'success' : 'error'}>
              <strong>{results.passed ? '✓ Model Passed Bias Checks' : '✗ Model Failed Bias Checks'}</strong>
            </div>

            <div style={{ marginTop: '20px' }}>
              <div className="metric-row">
                <span className="metric-label">Demographic Parity Ratio</span>
                <span className={`metric-value ${results.demographic_parity >= 0.80 ? 'pass' : 'fail'}`}>
                  {results.demographic_parity.toFixed(3)}
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Equalized Odds (TPR)</span>
                <span className={`metric-value ${results.equalized_odds_tpr >= 0.85 ? 'pass' : 'fail'}`}>
                  {results.equalized_odds_tpr.toFixed(3)}
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Equalized Odds (FPR)</span>
                <span className={`metric-value ${results.equalized_odds_fpr >= 0.85 ? 'pass' : 'fail'}`}>
                  {results.equalized_odds_fpr.toFixed(3)}
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Statistical Significance (p-value)</span>
                <span className={`metric-value ${results.statistical_significance >= 0.05 ? 'pass' : 'fail'}`}>
                  {results.statistical_significance.toFixed(4)}
                </span>
              </div>
            </div>

            <div style={{ marginTop: '20px', background: '#f1f3f5', padding: '15px', borderRadius: '6px' }}>
              <h4 style={{ marginBottom: '10px' }}>Recommendations:</h4>
              <ul style={{ paddingLeft: '20px' }}>
                {results.recommendations.map((rec, idx) => (
                  <li key={idx} style={{ marginBottom: '8px' }}>{rec}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      <div className="card">
        <h3 style={{ marginBottom: '15px' }}>Understanding Bias Metrics</h3>
        <div style={{ fontSize: '0.95em', lineHeight: '1.6' }}>
          <p><strong>Demographic Parity:</strong> Measures if positive predictions are equally distributed across groups. A ratio of 1.0 indicates perfect parity. Values below 0.80 indicate significant disparity.</p>
          <p><strong>Equalized Odds:</strong> Ensures equal true positive and false positive rates across groups. Both metrics should be above 0.85 for fairness.</p>
          <p><strong>Statistical Significance:</strong> P-value from chi-square test. Values below 0.05 indicate statistically significant bias.</p>
        </div>
      </div>
    </div>
  );
};

export default BiasAnalysis;
