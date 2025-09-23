import React from 'react';
import styled from 'styled-components';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Card = styled.div`
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
`;

const CardHeader = styled.div`
  display: flex;
  justify-content: between;
  align-items: center;
  margin-bottom: 20px;
  
  h3 {
    margin: 0;
    color: #2d3748;
    font-size: 1.25rem;
  }
`;

const TestButtons = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
`;

const TestButton = styled.button`
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }
  
  &:active {
    transform: translateY(0);
  }
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
`;

const MetricBox = styled.div`
  text-align: center;
  padding: 15px;
  background: #f7fafc;
  border-radius: 8px;
  
  .value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #2d3748;
    margin-bottom: 5px;
  }
  
  .label {
    font-size: 0.875rem;
    color: #718096;
  }
`;

const RecentTests = styled.div`
  max-height: 200px;
  overflow-y: auto;
  
  .test-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #e2e8f0;
    
    &:last-child {
      border-bottom: none;
    }
  }
  
  .status {
    padding: 4px 8px;
    border-radius: 4px;
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
    
    &.running {
      background: #bee3f8;
      color: #2a4365;
    }
  }
`;

function TestDashboard({ data, onRunTest }) {
  const testTypes = ['unit', 'integration', 'e2e', 'performance', 'chaos'];
  
  const formatDuration = (duration) => {
    return `${duration?.toFixed(1) || 0}s`;
  };
  
  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };
  
  const getCoverageColor = (coverage) => {
    if (coverage >= 0.8) return '#48bb78';
    if (coverage >= 0.6) return '#ed8936';
    return '#f56565';
  };
  
  return (
    <Card>
      <CardHeader>
        <h3>🧪 Test Execution Dashboard</h3>
      </CardHeader>
      
      <TestButtons>
        {testTypes.map(testType => (
          <TestButton 
            key={testType} 
            onClick={() => onRunTest(testType)}
          >
            Run {testType.charAt(0).toUpperCase() + testType.slice(1)}
          </TestButton>
        ))}
      </TestButtons>
      
      <MetricsGrid>
        <MetricBox>
          <div className="value">{data?.metrics?.total_tests_run || 0}</div>
          <div className="label">Total Tests</div>
        </MetricBox>
        <MetricBox>
          <div className="value" style={{ color: getCoverageColor(data?.metrics?.success_rate || 0) }}>
            {formatPercentage(data?.metrics?.success_rate || 0)}
          </div>
          <div className="label">Success Rate</div>
        </MetricBox>
        <MetricBox>
          <div className="value">{formatDuration(data?.metrics?.avg_duration)}</div>
          <div className="label">Avg Duration</div>
        </MetricBox>
      </MetricsGrid>
      
      {data?.metrics?.coverage_trend?.length > 0 && (
        <div style={{ height: '200px', marginBottom: '20px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.metrics.coverage_trend.map((val, idx) => ({ index: idx, coverage: val * 100 }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="index" />
              <YAxis domain={[0, 100]} />
              <Tooltip formatter={(value) => [`${value.toFixed(1)}%`, 'Coverage']} />
              <Line type="monotone" dataKey="coverage" stroke="#48bb78" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      
      <RecentTests>
        <h4>Recent Test Results</h4>
        {data?.recent_results?.map((result, index) => (
          <div key={index} className="test-item">
            <span>{result.test_type} - {result.test_id}</span>
            <span className={`status ${result.status}`}>
              {result.status}
            </span>
          </div>
        )) || <p>No test results yet</p>}
      </RecentTests>
    </Card>
  );
}

export default TestDashboard;
