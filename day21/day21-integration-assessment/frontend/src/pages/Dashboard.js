import React, { useState, useEffect } from 'react';
import MetricsCard from '../components/MetricsCard';
import StatusIndicator from '../components/StatusIndicator';

const Dashboard = () => {
  const [systemStatus, setSystemStatus] = useState({
    integration_tests: 'running',
    load_tests: 'completed',
    monitoring: 'active',
    cost_analysis: 'completed'
  });

  const [metrics, setMetrics] = useState({
    total_tests: 156,
    passed_tests: 142,
    failed_tests: 3,
    load_test_rps: 1247,
    avg_response_time: 0.89,
    cost_optimization_score: 82
  });

  useEffect(() => {
    // Simulate real-time metrics updates
    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        load_test_rps: prev.load_test_rps + Math.floor(Math.random() * 20 - 10),
        avg_response_time: Math.max(0.1, prev.avg_response_time + (Math.random() * 0.2 - 0.1))
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>System Integration Overview</h1>
        <p>Real-time monitoring of Phase 1 integration assessment</p>
      </div>

      <div className="status-grid">
        <StatusIndicator 
          title="Integration Tests" 
          status={systemStatus.integration_tests}
          description="End-to-end workflow validation"
        />
        <StatusIndicator 
          title="Load Testing" 
          status={systemStatus.load_tests}
          description="Performance under load"
        />
        <StatusIndicator 
          title="Monitoring" 
          status={systemStatus.monitoring}
          description="Real-time system health"
        />
        <StatusIndicator 
          title="Cost Analysis" 
          status={systemStatus.cost_analysis}
          description="Resource optimization"
        />
      </div>

      <div className="metrics-grid">
        <MetricsCard 
          title="Test Success Rate"
          value={`${((metrics.passed_tests / metrics.total_tests) * 100).toFixed(1)}%`}
          subtitle={`${metrics.passed_tests}/${metrics.total_tests} tests passed`}
          trend="up"
          color="green"
        />
        <MetricsCard 
          title="Load Test RPS"
          value={metrics.load_test_rps.toLocaleString()}
          subtitle="Requests per second"
          trend="stable"
          color="blue"
        />
        <MetricsCard 
          title="Avg Response Time"
          value={`${metrics.avg_response_time.toFixed(2)}s`}
          subtitle="P95 response time"
          trend={metrics.avg_response_time > 1.0 ? "down" : "up"}
          color={metrics.avg_response_time > 1.0 ? "red" : "green"}
        />
        <MetricsCard 
          title="Cost Optimization"
          value={`${metrics.cost_optimization_score}/100`}
          subtitle="Optimization score"
          trend="up"
          color="orange"
        />
      </div>

      <div className="recent-activity">
        <h3>Recent Activity</h3>
        <div className="activity-list">
          <div className="activity-item">
            <span className="timestamp">15:42</span>
            <span className="message">Integration test suite completed successfully</span>
            <span className="status success">✓</span>
          </div>
          <div className="activity-item">
            <span className="timestamp">15:38</span>
            <span className="message">Load test reached 1500 RPS peak</span>
            <span className="status info">ℹ</span>
          </div>
          <div className="activity-item">
            <span className="timestamp">15:35</span>
            <span className="message">Cost optimization recommendations generated</span>
            <span className="status success">✓</span>
          </div>
          <div className="activity-item">
            <span className="timestamp">15:30</span>
            <span className="message">Performance monitoring baseline established</span>
            <span className="status success">✓</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
