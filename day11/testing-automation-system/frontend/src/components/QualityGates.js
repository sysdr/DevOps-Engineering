import React from 'react';
import styled from 'styled-components';

const Card = styled.div`
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const CardHeader = styled.div`
  margin-bottom: 20px;
  
  h3 {
    margin: 0;
    color: #2d3748;
    font-size: 1.25rem;
  }
`;

const GateItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px;
  margin-bottom: 12px;
  border-radius: 8px;
  background: ${props => props.passed ? '#f0fff4' : '#fff5f5'};
  border-left: 4px solid ${props => props.passed ? '#48bb78' : '#f56565'};
`;

const GateInfo = styled.div`
  flex: 1;
  
  .gate-name {
    font-weight: 600;
    color: #2d3748;
    margin-bottom: 4px;
  }
  
  .gate-details {
    font-size: 0.875rem;
    color: #718096;
  }
`;

const GateStatus = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  
  .status-badge {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    
    &.passed {
      background: #c6f6d5;
      color: #22543d;
    }
    
    &.failed {
      background: #fed7d7;
      color: #742a2a;
    }
  }
  
  .status-icon {
    font-size: 1.25rem;
  }
`;

const GateMetric = styled.div`
  text-align: center;
  
  .current-value {
    font-size: 1.1rem;
    font-weight: bold;
    color: ${props => props.passed ? '#22543d' : '#742a2a'};
  }
  
  .threshold {
    font-size: 0.75rem;
    color: #718096;
  }
`;

const OverallStatus = styled.div`
  text-align: center;
  padding: 20px;
  border-radius: 8px;
  background: ${props => props.$allPassed ? 
    'linear-gradient(135deg, #c6f6d5 0%, #9ae6b4 100%)' : 
    'linear-gradient(135deg, #fed7d7 0%, #fbb6ce 100%)'
  };
  margin-bottom: 20px;
  
  .status-text {
    font-size: 1.1rem;
    font-weight: bold;
    color: ${props => props.$allPassed ? '#22543d' : '#742a2a'};
    margin-bottom: 5px;
  }
  
  .status-description {
    font-size: 0.875rem;
    color: ${props => props.$allPassed ? '#276749' : '#822727'};
  }
`;

function QualityGates({ gates }) {
  const allPassed = gates.every(gate => gate.passed);
  
  const formatValue = (value, name) => {
    if (name === 'Code Coverage' || name === 'Success Rate') {
      return `${(value * 100).toFixed(1)}%`;
    }
    if (name === 'Performance') {
      return `${value.toFixed(1)}s`;
    }
    return value.toString();
  };
  
  const formatThreshold = (threshold, name) => {
    if (name === 'Code Coverage' || name === 'Success Rate') {
      return `Target: ${(threshold * 100).toFixed(0)}%`;
    }
    if (name === 'Performance') {
      return `Target: ≤${threshold}s`;
    }
    return `Target: ${threshold}`;
  };
  
  return (
    <Card>
      <CardHeader>
        <h3>🛡️ Quality Gates</h3>
      </CardHeader>
      
      <OverallStatus $allPassed={allPassed}>
        <div className="status-text">
          {allPassed ? '✅ All Gates Passed' : '❌ Quality Gates Failed'}
        </div>
        <div className="status-description">
          {allPassed ? 
            'Deployment approved - all quality criteria met' : 
            'Deployment blocked - quality issues detected'
          }
        </div>
      </OverallStatus>
      
      {gates.map((gate, index) => (
        <GateItem key={index} passed={gate.passed}>
          <GateInfo>
            <div className="gate-name">{gate.name}</div>
            <div className="gate-details">
              {formatThreshold(gate.threshold, gate.name)}
            </div>
          </GateInfo>
          
          <GateMetric passed={gate.passed}>
            <div className="current-value">
              {formatValue(gate.current_value, gate.name)}
            </div>
          </GateMetric>
          
          <GateStatus>
            <span className="status-icon">
              {gate.passed ? '✅' : '❌'}
            </span>
            <span className={`status-badge ${gate.status}`}>
              {gate.status}
            </span>
          </GateStatus>
        </GateItem>
      ))}
      
      {gates.length === 0 && (
        <div style={{ textAlign: 'center', color: '#718096', padding: '40px' }}>
          No quality gate data available. Run some tests to see results.
        </div>
      )}
    </Card>
  );
}

export default QualityGates;
