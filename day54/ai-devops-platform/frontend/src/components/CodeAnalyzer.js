import React, { useState } from 'react';

function CodeAnalyzer() {
  const [code, setCode] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [demoLoaded, setDemoLoaded] = useState(false);

  const sampleCode = `import os
password = "admin123"  # Hardcoded password
api_key = "sk-1234567890"

def process_data(user_input):
    # Potential SQL injection
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    result = eval(user_input)  # Dangerous eval
    return result

class DataProcessor:
    def __init__(self, a, b, c, d, e, f, g):  # Too many parameters
        self.a = a
        # ... many more assignments
    
    def complex_method(self, x):  # High complexity
        if x > 10:
            if x < 20:
                for i in range(x):
                    if i % 2 == 0:
                        if i > 5:
                            pass  # TODO: Fix this
        return x
`;

  // Auto-load demo data on mount
  React.useEffect(() => {
    if (!demoLoaded) {
      setCode(sampleCode);
      setDemoLoaded(true);
      // Auto-analyze after a short delay
      setTimeout(() => {
        analyzeCode();
      }, 500);
    }
  }, []);

  const analyzeCode = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: code,
          language: 'python',
          filename: 'sample.py'
        })
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Failed to analyze code. Make sure the service is running.');
    } finally {
      setLoading(false);
    }
  };

  const getScoreClass = (score) => {
    if (score >= 80) return 'good';
    if (score >= 60) return 'medium';
    return 'poor';
  };

  return (
    <div className="panel">
      <h2>📝 AI Code Analyzer</h2>
      <p style={{ color: '#718096', marginBottom: '1rem' }}>
        Paste your Python code below for intelligent security and quality analysis
      </p>

      <button
        onClick={() => setCode(sampleCode)}
        style={{
          background: '#e2e8f0',
          color: '#2d3748',
          border: 'none',
          padding: '0.5rem 1rem',
          borderRadius: '6px',
          cursor: 'pointer',
          marginBottom: '1rem'
        }}
      >
        Load Sample Code
      </button>

      <textarea
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="Paste your Python code here..."
      />

      <button
        className="primary"
        onClick={analyzeCode}
        disabled={!code || loading}
      >
        {loading ? 'Analyzing...' : 'Analyze Code'}
      </button>

      {result && (
        <div className="results">
          <div style={{ textAlign: 'center' }}>
            <div className={`score-circle ${getScoreClass(result.score)}`}>
              {result.score.toFixed(0)}
            </div>
            <p style={{ color: '#718096', marginTop: '0.5rem' }}>Code Quality Score</p>
          </div>

          <div className="metric-grid">
            {Object.entries(result.metrics).map(([key, value]) => (
              <div key={key} className="metric-card">
                <div className="metric-value">
                  {typeof value === 'number' ? value.toFixed(0) : value}
                </div>
                <div className="metric-label">
                  {key.replace(/_/g, ' ').toUpperCase()}
                </div>
              </div>
            ))}
          </div>

          <h3 style={{ marginTop: '2rem', marginBottom: '1rem' }}>
            Issues Found: {result.issues.length}
          </h3>

          {result.issues.length === 0 ? (
            <p style={{ color: '#48bb78', fontWeight: '600' }}>
              ✅ No issues detected! Great job!
            </p>
          ) : (
            result.issues.map((issue, idx) => (
              <div key={idx} className={`issue ${issue.severity}`}>
                <div className="issue-header">
                  <span>
                    <strong>Line {issue.line}:</strong> {issue.message}
                  </span>
                  <span className={`severity-badge ${issue.severity}`}>
                    {issue.severity}
                  </span>
                </div>
                <p style={{ color: '#4a5568', margin: '0.5rem 0' }}>
                  💡 {issue.suggestion}
                </p>
                <p style={{ color: '#718096', fontSize: '0.85rem' }}>
                  Confidence: {(issue.confidence * 100).toFixed(0)}%
                </p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default CodeAnalyzer;
