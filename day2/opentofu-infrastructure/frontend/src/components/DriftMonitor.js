import React, { useState, useEffect } from 'react';
import axios from 'axios';

const DriftMonitor = () => {
  const [driftResults, setDriftResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [initialLoading, setInitialLoading] = useState(true);

  useEffect(() => {
    fetchDriftResults();
    // Check for drift every 5 minutes
    const interval = setInterval(fetchDriftResults, 300000);
    return () => clearInterval(interval);
  }, []);

  const fetchDriftResults = async () => {
    try {
      setError(null);
      const response = await axios.get('/api/drift-detection/results');
      // Handle both old format (single result) and new format (results object)
      const data = response.data;
      if (data.results) {
        setDriftResults(data.results);
      } else {
        // Convert single result to results object format
        setDriftResults({ [data.environment || 'default']: data });
      }
    } catch (error) {
      console.error('Failed to fetch drift results:', error);
      setError('Failed to fetch drift results. Please try again.');
      setDriftResults({});
    } finally {
      setInitialLoading(false);
    }
  };

  const handleRunDriftCheck = async (environment) => {
    setLoading(true);
    setError(null);
    try {
      await axios.get(`/api/drift-detection/${environment}`);
      await fetchDriftResults();
    } catch (error) {
      console.error('Drift check failed:', error);
      setError('Drift check failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRemediate = async (environment) => {
    try {
      setError(null);
      await axios.post(`/api/drift-detection/remediate/${environment}`);
      setTimeout(fetchDriftResults, 2000);
    } catch (error) {
      console.error('Remediation failed:', error);
      setError('Remediation failed. Please try again.');
    }
  };

  return (
    <div className="drift-monitor">
      <h2>Drift Detection & Monitoring</h2>
      
      {error && (
        <div className="error-message" style={{ 
          color: 'red', 
          backgroundColor: '#ffe6e6', 
          padding: '10px', 
          borderRadius: '4px', 
          marginBottom: '15px',
          border: '1px solid #ffcccc'
        }}>
          ⚠️ {error}
        </div>
      )}
      
      <div className="drift-controls">
        <button 
          onClick={() => handleRunDriftCheck('dev')}
          disabled={loading}
          className="drift-check-button"
        >
          {loading ? 'Checking...' : 'Run Drift Check (All Environments)'}
        </button>
      </div>

      <div className="drift-results">
        {driftResults && Object.entries(driftResults).map(([env, result]) => (
          <div key={env} className="drift-result-card">
            <div className="drift-result-header">
              <h3>{env}</h3>
              <div className={`drift-status ${result.drift_detected ? 'detected' : 'clean'}`}>
                {result.drift_detected ? '⚠️ Drift Detected' : '✅ No Drift'}
              </div>
            </div>
            
            <div className="drift-timestamp">
              Last Check: {result.timestamp ? new Date(result.timestamp).toLocaleString() : 'Unknown'}
            </div>

            {result.changes && Array.isArray(result.changes) && result.changes.length > 0 && (
              <div className="drift-changes">
                <h4>Detected Changes:</h4>
                {result.changes.map((change, index) => (
                  <div key={index} className={`change-item ${change.severity}`}>
                    <span className="change-resource">{change.resource}</span>
                    <span className="change-type">{change.change}</span>
                    <span className="change-severity">{change.severity}</span>
                  </div>
                ))}
                <button 
                  onClick={() => handleRemediate(env)}
                  className="remediate-button"
                >
                  Auto-Remediate
                </button>
              </div>
            )}
          </div>
        ))}

        {initialLoading ? (
          <div className="loading-message" style={{ 
            textAlign: 'center', 
            padding: '20px',
            color: '#666'
          }}>
            🔄 Loading drift detection results...
          </div>
        ) : (!driftResults || Object.keys(driftResults).length === 0) ? (
          <div className="no-results">
            <p>No drift detection results available.</p>
            <p>Run a drift check to see results.</p>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default DriftMonitor;
