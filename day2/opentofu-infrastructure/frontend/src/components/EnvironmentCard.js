import React, { useState } from 'react';
import axios from 'axios';

const EnvironmentCard = ({ environment, onRefresh }) => {
  const [deploying, setDeploying] = useState(false);
  const [checkingDrift, setCheckingDrift] = useState(false);

  const handleDeploy = async (action) => {
    setDeploying(true);
    try {
      await axios.post('/api/infrastructure/deploy', {
        environment: environment.environment,
        action: action,
        auto_approve: false
      });
      
      // Wait a moment then refresh
      setTimeout(() => {
        onRefresh();
        setDeploying(false);
      }, 2000);
    } catch (error) {
      console.error('Deployment failed:', error);
      setDeploying(false);
    }
  };

  const handleDriftCheck = async () => {
    setCheckingDrift(true);
    try {
      await axios.get(`/api/drift-detection/${environment.environment}`);
      setTimeout(() => {
        onRefresh();
        setCheckingDrift(false);
      }, 1000);
    } catch (error) {
      console.error('Drift check failed:', error);
      setCheckingDrift(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'green';
      case 'destroyed': return 'red';
      case 'deploying': return 'orange';
      default: return 'gray';
    }
  };

  return (
    <div className="environment-card">
      <div className="environment-header">
        <h3>{environment.environment}</h3>
        <div className={`status-badge ${getStatusColor(environment.status)}`}>
          {environment.status}
        </div>
      </div>
      
      <div className="environment-details">
        <div className="detail-row">
          <span>Resources:</span>
          <span>{environment.resources?.length || 0}</span>
        </div>
        <div className="detail-row">
          <span>Last Updated:</span>
          <span>{new Date(environment.last_updated).toLocaleString()}</span>
        </div>
        <div className="detail-row">
          <span>Drift Status:</span>
          <span className={environment.drift_detected ? 'drift-detected' : 'drift-clean'}>
            {environment.drift_detected ? '⚠️ Detected' : '✅ Clean'}
          </span>
        </div>
      </div>

      <div className="environment-actions">
        <button 
          onClick={() => handleDeploy('plan')}
          disabled={deploying}
          className="action-button plan"
        >
          {deploying ? 'Planning...' : 'Plan'}
        </button>
        <button 
          onClick={() => handleDeploy('apply')}
          disabled={deploying}
          className="action-button apply"
        >
          {deploying ? 'Applying...' : 'Apply'}
        </button>
        <button 
          onClick={handleDriftCheck}
          disabled={checkingDrift}
          className="action-button drift"
        >
          {checkingDrift ? 'Checking...' : 'Check Drift'}
        </button>
      </div>

      {environment.resources?.length > 0 && (
        <div className="resources-list">
          <h4>Resources</h4>
          {environment.resources.slice(0, 3).map((resource, index) => (
            <div key={index} className="resource-item">
              <span className="resource-type">{resource.type}</span>
              <span className="resource-name">{resource.name}</span>
              <span className={`resource-status ${resource.status}`}>
                {resource.status}
              </span>
            </div>
          ))}
          {environment.resources.length > 3 && (
            <div className="resource-item more">
              +{environment.resources.length - 3} more resources
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EnvironmentCard;
