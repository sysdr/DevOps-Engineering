import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  const [assessmentData, setAssessmentData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/assessment/status');
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  const runAssessment = async () => {
    console.log('Run assessment button clicked');
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/assessment/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.assessment_id) {
        // Poll for results
        pollForResults(data.assessment_id);
      } else {
        console.error('No assessment_id in response:', data);
        setLoading(false);
      }
    } catch (error) {
      console.error('Error running assessment:', error);
      setLoading(false);
      alert('Failed to start assessment. Please check if the backend is running.');
    }
  };

  const pollForResults = async (assessmentId) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = setInterval(async () => {
      attempts++;
      try {
        const response = await fetch(`http://localhost:8000/api/assessment/results/${assessmentId}`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();

        if (data.status === 'completed') {
          setAssessmentData(data);
          setLoading(false);
          clearInterval(poll);
        } else if (attempts >= maxAttempts) {
          setLoading(false);
          clearInterval(poll);
          console.warn('Assessment polling timeout after', maxAttempts, 'attempts');
        }
      } catch (error) {
        console.error('Error polling results:', error);
        // Stop polling on error and re-enable button
        setLoading(false);
        clearInterval(poll);
      }
    }, 2000);
  };

  const loadLatestResults = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/assessment/results/latest');
      const data = await response.json();
      setAssessmentData(data);
    } catch (error) {
      console.error('Error loading results:', error);
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🛡️ Security Assessment Platform</h1>
        <p>Phase 2 Integration & Validation Dashboard</p>
      </header>

      <div className="control-panel">
        <button onClick={runAssessment} disabled={loading} className="btn-primary">
          {loading ? '⏳ Running Assessment...' : '▶️ Run Security Assessment'}
        </button>
        <button onClick={loadLatestResults} className="btn-secondary">
          📊 Load Latest Results
        </button>
        {status && (
          <div className="status-badge">
            <span>Active: {status.active_assessments}</span>
            <span>Completed: {status.completed_assessments}</span>
          </div>
        )}
      </div>

      {assessmentData && <Dashboard data={assessmentData} />}
    </div>
  );
}

export default App;
