import React, { useState } from 'react';
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
  
  .description {
    font-size: 0.875rem;
    color: #718096;
    margin-top: 8px;
  }
`;

const ChaosControls = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
`;

const ChaosButton = styled.button`
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  background: ${props => {
    switch(props.$faultType) {
      case 'latency': return 'linear-gradient(135deg, #ed8936 0%, #dd6b20 100%)';
      case 'error': return 'linear-gradient(135deg, #f56565 0%, #e53e3e 100%)';
      case 'shutdown': return 'linear-gradient(135deg, #805ad5 0%, #6b46c1 100%)';
      default: return 'linear-gradient(135deg, #4299e1 0%, #3182ce 100%)';
    }
  }};
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
  
  .fault-icon {
    margin-right: 8px;
  }
`;

const ConfigPanel = styled.div`
  background: #f7fafc;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  
  .config-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    label {
      font-weight: 500;
      color: #2d3748;
    }
    
    input, select {
      padding: 6px 12px;
      border: 1px solid #e2e8f0;
      border-radius: 4px;
      background: white;
      min-width: 120px;
    }
  }
`;

const ChaosResults = styled.div`
  .result-item {
    background: #f7fafc;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 8px;
    border-left: 4px solid #4299e1;
    
    .result-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      
      .fault-type {
        font-weight: 600;
        color: #2d3748;
      }
      
      .timestamp {
        font-size: 0.75rem;
        color: #718096;
      }
    }
    
    .result-details {
      font-size: 0.875rem;
      color: #4a5568;
      
      .detail-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 4px;
      }
    }
    
    &.success {
      border-left-color: #48bb78;
    }
    
    &.failure {
      border-left-color: #f56565;
    }
  }
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 20px;
  background: ${props => props.$active ? 
    'linear-gradient(135deg, #fed7d7 0%, #fbb6ce 100%)' : 
    'linear-gradient(135deg, #c6f6d5 0%, #9ae6b4 100%)'
  };
  
  .status-text {
    font-weight: 600;
    color: ${props => props.$active ? '#742a2a' : '#22543d'};
  }
`;

const faultTypes = [
  { 
    type: 'latency', 
    icon: '🐌', 
    name: 'Network Latency',
    description: 'Introduces network delays to test timeout handling'
  },
  { 
    type: 'error', 
    icon: '💥', 
    name: 'Error Injection',
    description: 'Simulates service errors and failures'
  },
  { 
    type: 'shutdown', 
    icon: '🔌', 
    name: 'Service Shutdown',
    description: 'Tests graceful degradation when services are unavailable'
  }
];

function ChaosEngineering({ onInjectChaos }) {
  const [selectedFault, setSelectedFault] = useState('latency');
  const [duration, setDuration] = useState(30);
  const [intensity, setIntensity] = useState('medium');
  const [isRunning, setIsRunning] = useState(false);
  const [chaosResults, setChaosResults] = useState([]);
  
  const handleInjectChaos = async (faultType) => {
    setIsRunning(true);
    setSelectedFault(faultType);
    
    try {
      await onInjectChaos(faultType, duration);
      
      // Simulate result
      const result = {
        id: Date.now(),
        faultType,
        duration,
        intensity,
        timestamp: new Date().toLocaleTimeString(),
        status: Math.random() > 0.2 ? 'success' : 'failure',
        recoveryTime: Math.random() * 25 + 5,
        impactRadius: Math.floor(Math.random() * 3) + 1
      };
      
      setChaosResults(prev => [result, ...prev.slice(0, 4)]);
      
      // Simulate chaos duration
      setTimeout(() => {
        setIsRunning(false);
      }, duration * 100); // Simulate faster for demo
      
    } catch (error) {
      setIsRunning(false);
      console.error('Chaos injection failed:', error);
    }
  };
  
  const getIntensityColor = (intensity) => {
    switch(intensity) {
      case 'low': return '#48bb78';
      case 'medium': return '#ed8936';
      case 'high': return '#f56565';
      default: return '#4299e1';
    }
  };
  
  return (
    <Card>
      <CardHeader>
        <h3>🌪️ Chaos Engineering</h3>
        <div className="description">
          Test system resilience by intentionally injecting faults
        </div>
      </CardHeader>
      
      <StatusIndicator $active={isRunning}>
        <div className="status-text">
          {isRunning ? 
            `🔥 Chaos Active: ${selectedFault} injection in progress...` : 
            '✅ System Stable: Ready for chaos experiments'
          }
        </div>
      </StatusIndicator>
      
      <ConfigPanel>
        <div className="config-row">
          <label>Duration (seconds)</label>
          <input 
            type="number" 
            value={duration}
            onChange={(e) => setDuration(parseInt(e.target.value))}
            min="5"
            max="300"
            disabled={isRunning}
          />
        </div>
        <div className="config-row">
          <label>Intensity</label>
          <select 
            value={intensity}
            onChange={(e) => setIntensity(e.target.value)}
            disabled={isRunning}
          >
            <option value="low">Low Impact</option>
            <option value="medium">Medium Impact</option>
            <option value="high">High Impact</option>
          </select>
        </div>
      </ConfigPanel>
      
      <ChaosControls>
        {faultTypes.map(fault => (
          <ChaosButton
            key={fault.type}
            $faultType={fault.type}
            onClick={() => handleInjectChaos(fault.type)}
            disabled={isRunning}
            title={fault.description}
          >
            <span className="fault-icon">{fault.icon}</span>
            {fault.name}
          </ChaosButton>
        ))}
      </ChaosControls>
      
      <ChaosResults>
        <h4>Recent Chaos Experiments</h4>
        {chaosResults.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#718096', padding: '20px' }}>
            No chaos experiments yet. Start by injecting a fault above.
          </div>
        ) : (
          chaosResults.map(result => (
            <div key={result.id} className={`result-item ${result.status}`}>
              <div className="result-header">
                <span className="fault-type">
                  {faultTypes.find(f => f.type === result.faultType)?.icon} {result.faultType}
                </span>
                <span className="timestamp">{result.timestamp}</span>
              </div>
              <div className="result-details">
                <div className="detail-row">
                  <span>Recovery Time:</span>
                  <span>{result.recoveryTime.toFixed(1)}s</span>
                </div>
                <div className="detail-row">
                  <span>Impact Radius:</span>
                  <span>{result.impactRadius} services</span>
                </div>
                <div className="detail-row">
                  <span>Result:</span>
                  <span style={{ 
                    color: result.status === 'success' ? '#22543d' : '#742a2a',
                    fontWeight: '600'
                  }}>
                    {result.status === 'success' ? '✅ System Recovered' : '❌ Recovery Failed'}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </ChaosResults>
    </Card>
  );
}

export default ChaosEngineering;
