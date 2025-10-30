import React, { useState, useEffect } from 'react';
import TestResultsTable from '../components/TestResultsTable';

const IntegrationTests = () => {
  const [testResults, setTestResults] = useState([]);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    // Load initial test results
    setTestResults([
      {
        id: 1,
        name: 'user_registration_flow',
        status: 'passed',
        duration: 2.3,
        timestamp: new Date().toISOString(),
        details: 'All steps completed successfully'
      },
      {
        id: 2,
        name: 'order_checkout_flow',
        status: 'passed',
        duration: 4.1,
        timestamp: new Date().toISOString(),
        details: 'Payment processing validated'
      },
      {
        id: 3,
        name: 'inventory_sync_flow',
        status: 'failed',
        duration: 1.8,
        timestamp: new Date().toISOString(),
        details: 'Database connection timeout'
      }
    ]);
  }, []);

  const runIntegrationTests = async () => {
    setIsRunning(true);
    
    try {
      const apiBase = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/integration-tests/run`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setTestResults(data.results || []);
      } else {
        console.error('Integration tests endpoint returned', response.status);
      }
    } catch (error) {
      console.error('Failed to run integration tests:', error);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="integration-tests">
      <div className="page-header">
        <h1>Integration Testing</h1>
        <p>End-to-end workflow validation across all system components</p>
        
        <button 
          className={`run-tests-btn ${isRunning ? 'running' : ''}`}
          onClick={runIntegrationTests}
          disabled={isRunning}
        >
          {isRunning ? '🔄 Running Tests...' : '▶️ Run Integration Tests'}
        </button>
      </div>

      <div className="test-summary">
        <div className="summary-card">
          <h3>Test Summary</h3>
          <div className="summary-stats">
            <div className="stat">
              <span className="value">{testResults.length}</span>
              <span className="label">Total Tests</span>
            </div>
            <div className="stat success">
              <span className="value">
                {testResults.filter(t => t.status === 'passed').length}
              </span>
              <span className="label">Passed</span>
            </div>
            <div className="stat error">
              <span className="value">
                {testResults.filter(t => t.status === 'failed').length}
              </span>
              <span className="label">Failed</span>
            </div>
          </div>
        </div>
      </div>

      <TestResultsTable results={testResults} />

      <div className="test-scenarios">
        <h3>Test Scenarios</h3>
        <div className="scenarios-grid">
          <div className="scenario-card">
            <h4>User Registration Flow</h4>
            <p>Tests user creation, email verification, and initial login</p>
            <div className="scenario-steps">
              <span className="step">Create User</span>
              <span className="step">Verify Email</span>
              <span className="step">Login</span>
            </div>
          </div>
          
          <div className="scenario-card">
            <h4>Order Checkout Flow</h4>
            <p>Validates complete purchase process from cart to confirmation</p>
            <div className="scenario-steps">
              <span className="step">Add to Cart</span>
              <span className="step">Checkout</span>
              <span className="step">Payment</span>
              <span className="step">Confirmation</span>
            </div>
          </div>
          
          <div className="scenario-card">
            <h4>Inventory Sync Flow</h4>
            <p>Tests inventory updates across multiple services</p>
            <div className="scenario-steps">
              <span className="step">Update Inventory</span>
              <span className="step">Sync Services</span>
              <span className="step">Validate Consistency</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntegrationTests;
