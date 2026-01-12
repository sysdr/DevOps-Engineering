import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [validationStatus, setValidationStatus] = useState(null);
  const [testResults, setTestResults] = useState(null);
  const [runbooks, setRunbooks] = useState([]);
  const [knowledge, setKnowledge] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('validation');

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [validation, tests, runbookList, knowledgeData] = await Promise.all([
        axios.get(`${API_URL}/api/v1/validation/status`),
        axios.get(`${API_URL}/api/v1/integration-tests/status`),
        axios.get(`${API_URL}/api/v1/runbooks`),
        axios.get(`${API_URL}/api/v1/knowledge`)
      ]);
      
      setValidationStatus(validation.data);
      setTestResults(tests.data);
      setRunbooks(runbookList.data);
      setKnowledge(knowledgeData.data);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const runValidation = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/v1/validate`);
      setValidationStatus(response.data);
    } catch (error) {
      console.error('Error running validation:', error);
    }
    setLoading(false);
  };

  const runTests = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/v1/integration-tests`);
      setTestResults(response.data);
    } catch (error) {
      console.error('Error running tests:', error);
    }
    setLoading(false);
  };

  const getScoreColor = (score) => {
    if (score >= 90) return '#10b981';
    if (score >= 80) return '#3b82f6';
    if (score >= 70) return '#f59e0b';
    return '#ef4444';
  };

  const getStatusColor = (status) => {
    const colors = {
      pass: '#10b981',
      passed: '#10b981',
      warning: '#f59e0b',
      fail: '#ef4444',
      failed: '#ef4444',
      excellent: '#10b981',
      good: '#3b82f6',
      acceptable: '#f59e0b',
      needs_improvement: '#ef4444'
    };
    return colors[status] || '#6b7280';
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🎯 Production Readiness Platform</h1>
        <p className="subtitle">Complete Integration & Validation Dashboard</p>
      </header>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'validation' ? 'active' : ''}`}
          onClick={() => setActiveTab('validation')}
        >
          Validation
        </button>
        <button 
          className={`tab ${activeTab === 'tests' ? 'active' : ''}`}
          onClick={() => setActiveTab('tests')}
        >
          Integration Tests
        </button>
        <button 
          className={`tab ${activeTab === 'runbooks' ? 'active' : ''}`}
          onClick={() => setActiveTab('runbooks')}
        >
          Runbooks
        </button>
        <button 
          className={`tab ${activeTab === 'knowledge' ? 'active' : ''}`}
          onClick={() => setActiveTab('knowledge')}
        >
          Knowledge
        </button>
      </div>

      <div className="content">
        {activeTab === 'validation' && (
          <div className="section">
            <div className="section-header">
              <h2>Production Readiness Validation</h2>
              <button 
                className="action-button"
                onClick={runValidation}
                disabled={loading}
              >
                {loading ? 'Running...' : 'Run Validation'}
              </button>
            </div>

            {validationStatus && validationStatus.scores && (
              <>
                <div className="scores-grid">
                  {Object.entries(validationStatus.scores).map(([pillar, score]) => (
                    <div key={pillar} className="score-card">
                      <h3>{pillar}</h3>
                      <div 
                        className="score"
                        style={{ color: getScoreColor(score) }}
                      >
                        {score.toFixed(1)}%
                      </div>
                      <div className="score-bar">
                        <div 
                          className="score-fill"
                          style={{ 
                            width: `${score}%`,
                            backgroundColor: getScoreColor(score)
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                {validationStatus.last_run && (
                  <div className="info-card">
                    <p><strong>Last Validation:</strong> {new Date(validationStatus.last_run).toLocaleString()}</p>
                    <p>
                      <strong>Status:</strong>{' '}
                      <span style={{ color: getStatusColor(validationStatus.status) }}>
                        {validationStatus.status}
                      </span>
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'tests' && (
          <div className="section">
            <div className="section-header">
              <h2>Integration Test Results</h2>
              <button 
                className="action-button"
                onClick={runTests}
                disabled={loading}
              >
                {loading ? 'Running...' : 'Run Tests'}
              </button>
            </div>

            {testResults && testResults.tests && (
              <>
                <div className="test-summary">
                  <div className="summary-card">
                    <h3>Pass Rate</h3>
                    <div 
                      className="big-number"
                      style={{ color: getScoreColor(testResults.pass_rate) }}
                    >
                      {testResults.pass_rate.toFixed(1)}%
                    </div>
                  </div>
                  <div className="summary-card">
                    <h3>Total Tests</h3>
                    <div className="big-number">{testResults.total}</div>
                  </div>
                  <div className="summary-card">
                    <h3>Passed</h3>
                    <div className="big-number" style={{ color: '#10b981' }}>
                      {testResults.passed}
                    </div>
                  </div>
                  <div className="summary-card">
                    <h3>Failed</h3>
                    <div className="big-number" style={{ color: '#ef4444' }}>
                      {testResults.failed}
                    </div>
                  </div>
                </div>

                <div className="test-list">
                  {testResults.tests.map((test, idx) => (
                    <div key={idx} className="test-item">
                      <div className="test-info">
                        <span 
                          className="test-status"
                          style={{ backgroundColor: getStatusColor(test.status) }}
                        >
                          {test.status}
                        </span>
                        <span className="test-name">{test.scenario.replace(/_/g, ' ')}</span>
                      </div>
                      <div className="test-meta">
                        <span>Duration: {test.duration_seconds}s</span>
                        <span>Assertions: {test.assertions}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === 'runbooks' && (
          <div className="section">
            <h2>Operational Runbooks</h2>
            <div className="runbook-list">
              {runbooks.map((runbook) => (
                <div key={runbook.id} className="runbook-card">
                  <div className="runbook-header">
                    <h3>{runbook.title}</h3>
                    <span 
                      className="severity-badge"
                      style={{ 
                        backgroundColor: runbook.severity === 'high' ? '#ef4444' : '#f59e0b' 
                      }}
                    >
                      {runbook.severity}
                    </span>
                  </div>
                  <p className="runbook-scenario">{runbook.scenario.replace(/_/g, ' ')}</p>
                  <p className="runbook-updated">
                    Updated: {new Date(runbook.updated).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'knowledge' && (
          <div className="section">
            <h2>Knowledge Transfer Materials</h2>
            <div className="knowledge-list">
              {knowledge.map((material) => (
                <div key={material.id} className="knowledge-card">
                  <h3>{material.title}</h3>
                  <div className="knowledge-meta">
                    <span className="knowledge-type">{material.type}</span>
                    <span className="knowledge-difficulty">{material.difficulty}</span>
                    <span className="knowledge-time">{material.estimated_time}</span>
                  </div>
                  <div className="knowledge-topics">
                    {material.topics.map((topic, idx) => (
                      <span key={idx} className="topic-tag">{topic}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
