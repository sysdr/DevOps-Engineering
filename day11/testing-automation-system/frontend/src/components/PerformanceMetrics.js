import React from 'react';
import styled from 'styled-components';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

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

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
`;

const MetricBox = styled.div`
  text-align: center;
  padding: 15px;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  
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
  
  .trend {
    font-size: 0.75rem;
    margin-top: 5px;
    font-weight: 600;
    
    &.up {
      color: #f56565;
    }
    
    &.down {
      color: #48bb78;
    }
    
    &.stable {
      color: #4299e1;
    }
  }
`;

const ChartContainer = styled.div`
  height: 200px;
  margin-bottom: 20px;
`;

const PerformanceIndicator = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #f7fafc;
  border-radius: 8px;
  margin-bottom: 8px;
  
  .indicator-name {
    font-weight: 500;
    color: #2d3748;
  }
  
  .indicator-value {
    font-weight: bold;
    color: ${props => {
      if (props.$status === 'good') return '#48bb78';
      if (props.$status === 'warning') return '#ed8936';
      return '#f56565';
    }};
  }
`;

function PerformanceMetrics({ metrics }) {
  const formatDuration = (duration) => {
    return `${duration?.toFixed(1) || 0}s`;
  };
  
  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };
  
  const getPerformanceStatus = (value, threshold, inverse = false) => {
    if (!value) return 'unknown';
    if (inverse) {
      if (value <= threshold * 0.8) return 'good';
      if (value <= threshold) return 'warning';
      return 'poor';
    } else {
      if (value >= threshold * 1.2) return 'good';
      if (value >= threshold) return 'warning';
      return 'poor';
    }
  };
  
  const getTrendIndicator = (trend) => {
    if (!trend || trend.length < 2) return 'stable';
    const last = trend[trend.length - 1];
    const previous = trend[trend.length - 2];
    if (last > previous * 1.05) return 'up';
    if (last < previous * 0.95) return 'down';
    return 'stable';
  };
  
  const performanceTrend = metrics.performance_trend || [];
  const chartData = performanceTrend.map((value, index) => ({
    index: index + 1,
    duration: value,
    target: 30 // Target response time
  }));
  
  return (
    <Card>
      <CardHeader>
        <h3>⚡ Performance Metrics</h3>
      </CardHeader>
      
      <MetricsGrid>
        <MetricBox>
          <div className="value">{formatDuration(metrics.avg_duration)}</div>
          <div className="label">Avg Response Time</div>
          <div className={`trend ${getTrendIndicator(performanceTrend)}`}>
            {getTrendIndicator(performanceTrend) === 'up' && '↗️ Slower'}
            {getTrendIndicator(performanceTrend) === 'down' && '↘️ Faster'}
            {getTrendIndicator(performanceTrend) === 'stable' && '→ Stable'}
          </div>
        </MetricBox>
        
        <MetricBox>
          <div className="value">{formatPercentage(metrics.success_rate || 0)}</div>
          <div className="label">Success Rate</div>
          <div className={`trend ${metrics.success_rate >= 0.95 ? 'down' : 'up'}`}>
            {metrics.success_rate >= 0.95 ? '✅ Good' : '⚠️ Needs Attention'}
          </div>
        </MetricBox>
        
        <MetricBox>
          <div className="value">{metrics.total_tests_run || 0}</div>
          <div className="label">Tests Executed</div>
          <div className="trend stable">📊 Tracking</div>
        </MetricBox>
      </MetricsGrid>
      
      {chartData.length > 0 && (
        <ChartContainer>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorDuration" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4299e1" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#4299e1" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="index" />
              <YAxis />
              <Tooltip formatter={(value, name) => [
                `${value.toFixed(1)}s`, 
                name === 'duration' ? 'Response Time' : 'Target'
              ]} />
              <Area 
                type="monotone" 
                dataKey="duration" 
                stroke="#4299e1" 
                fillUrl="#colorDuration"
                strokeWidth={2}
              />
              <Area 
                type="monotone" 
                dataKey="target" 
                stroke="#f56565" 
                strokeDasharray="5 5"
                fill="transparent"
                strokeWidth={1}
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartContainer>
      )}
      
      <div>
        <h4>Performance Indicators</h4>
        <PerformanceIndicator 
          $status={getPerformanceStatus(metrics.avg_duration, 30, true)}
        >
          <span className="indicator-name">Average Response Time</span>
          <span className="indicator-value">
            {formatDuration(metrics.avg_duration)} / 30.0s target
          </span>
        </PerformanceIndicator>
        
        <PerformanceIndicator 
          $status={getPerformanceStatus(metrics.success_rate, 0.95)}
        >
          <span className="indicator-name">Success Rate</span>
          <span className="indicator-value">
            {formatPercentage(metrics.success_rate || 0)} / 95% target
          </span>
        </PerformanceIndicator>
        
        <PerformanceIndicator $status="good">
          <span className="indicator-name">System Health</span>
          <span className="indicator-value">Operational</span>
        </PerformanceIndicator>
      </div>
    </Card>
  );
}

export default PerformanceMetrics;
