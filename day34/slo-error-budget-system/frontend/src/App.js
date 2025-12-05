import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE = 'http://localhost:8005';
const POLICY_API = 'http://localhost:8006';

function App() {
  const [summary, setSummary] = useState({});
  const [policies, setPolicies] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedService, setSelectedService] = useState('order');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [summaryRes, policiesRes, alertsRes] = await Promise.all([
        fetch(`${API_BASE}/api/slo/all/summary`),
        fetch(`${POLICY_API}/api/policy/all/status`),
        fetch(`${POLICY_API}/api/alerts/all/recent?limit=10`)
      ]);

      const summaryData = await summaryRes.json();
      const policiesData = await policiesRes.json();
      const alertsData = await alertsRes.json();

      setSummary(summaryData);
      setPolicies(policiesData);
      setAlerts(alertsData);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const getBudgetStateColor = (state) => {
    const colors = {
      'HEALTHY': '#10b981',
      'CAUTION': '#f59e0b',
      'WARNING': '#f97316',
      'CRITICAL': '#ef4444',
      'EXHAUSTED': '#991b1b'
    };
    return colors[state] || '#6b7280';
  };

  const getAlertLevelColor = (level) => {
    const colors = {
      'LOG': '#3b82f6',
      'TICKET': '#f59e0b',
      'PAGE': '#ef4444',
      'CRITICAL': '#991b1b'
    };
    return colors[level] || '#6b7280';
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading">Loading SLO Dashboard...</div>
      </div>
    );
  }

  const serviceData = summary[selectedService] || {};
  const servicePolicy = policies[selectedService] || {};
  const sloConfig = serviceData.slo_config || {};
  const windows = serviceData.windows || {};
  const latency = serviceData.latency || {};

  return (
    <div className="app">
      <header className="header">
        <h1>🎯 SLO & Error Budget Dashboard</h1>
        <div className="header-subtitle">Real-time Reliability Tracking & Policy Enforcement</div>
      </header>

      <div className="container">
        {/* Service Selector */}
        <div className="service-selector">
          {Object.keys(summary).map(service => (
            <button
              key={service}
              className={`service-button ${selectedService === service ? 'active' : ''}`}
              onClick={() => setSelectedService(service)}
              style={{
                borderLeft: `4px solid ${getBudgetStateColor(policies[service]?.budget_state)}`
              }}
            >
              <div className="service-name">{service.toUpperCase()}</div>
              <div className="service-status">
                {policies[service]?.budget_state || 'N/A'}
              </div>
            </button>
          ))}
        </div>

        {/* Main Metrics Grid */}
        <div className="metrics-grid">
          {/* SLO Configuration Card */}
          <div className="card">
            <h3>📋 SLO Configuration</h3>
            <div className="slo-config">
              <div className="config-item">
                <span className="label">Availability Target:</span>
                <span className="value">{sloConfig.availability}%</span>
              </div>
              <div className="config-item">
                <span className="label">P95 Latency SLO:</span>
                <span className="value">{sloConfig.latency_p95}ms</span>
              </div>
              <div className="config-item">
                <span className="label">P99 Latency SLO:</span>
                <span className="value">{sloConfig.latency_p99}ms</span>
              </div>
              <div className="config-item">
                <span className="label">Error Budget:</span>
                <span className="value">{(100 - sloConfig.availability).toFixed(2)}%</span>
              </div>
            </div>
          </div>

          {/* Policy Status Card */}
          <div className="card">
            <h3>⚖️ Policy Status</h3>
            <div className="policy-status">
              <div className="status-badge" style={{
                backgroundColor: getBudgetStateColor(servicePolicy.budget_state),
                color: 'white'
              }}>
                {servicePolicy.budget_state || 'UNKNOWN'}
              </div>
              <div className="policy-details">
                <div className="policy-item">
                  <span className="label">Burn Rate:</span>
                  <span className="value burn-rate">{servicePolicy.burn_rate?.toFixed(2)}x</span>
                </div>
                <div className="policy-item">
                  <span className="label">Deployments:</span>
                  <span className={`value ${servicePolicy.deployment_blocked ? 'blocked' : 'allowed'}`}>
                    {servicePolicy.deployment_blocked ? '🚫 BLOCKED' : '✅ ALLOWED'}
                  </span>
                </div>
                {servicePolicy.alert_level && (
                  <div className="policy-item">
                    <span className="label">Alert Level:</span>
                    <span className="value" style={{
                      color: getAlertLevelColor(servicePolicy.alert_level)
                    }}>
                      {servicePolicy.alert_level}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Error Budget Card */}
          <div className="card">
            <h3>💰 Error Budget (1h Window)</h3>
            {windows['1h'] && (
              <div className="budget-display">
                <div className="budget-bar">
                  <div 
                    className="budget-fill"
                    style={{
                      width: `${Math.max(0, windows['1h'].budget_remaining * 10)}%`,
                      backgroundColor: getBudgetStateColor(servicePolicy.budget_state)
                    }}
                  />
                </div>
                <div className="budget-stats">
                  <div className="stat">
                    <span className="stat-label">Remaining</span>
                    <span className="stat-value">{windows['1h'].budget_remaining?.toFixed(4)}%</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Error Rate</span>
                    <span className="stat-value">{windows['1h'].error_rate?.toFixed(4)}%</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Time to Exhaustion</span>
                    <span className="stat-value">
                      {windows['1h'].time_to_exhaustion > 1000 
                        ? '∞' 
                        : `${windows['1h'].time_to_exhaustion?.toFixed(1)}h`}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Latency Metrics Card */}
          <div className="card">
            <h3>⚡ Latency Metrics</h3>
            <div className="latency-metrics">
              <div className="latency-item">
                <span className="latency-label">P95 Latency:</span>
                <span className={`latency-value ${latency.p95_violation ? 'violation' : 'ok'}`}>
                  {latency.p95?.toFixed(2)}ms
                </span>
                <span className="latency-slo">/ {latency.p95_slo}ms SLO</span>
              </div>
              <div className="latency-item">
                <span className="latency-label">P99 Latency:</span>
                <span className={`latency-value ${latency.p99_violation ? 'violation' : 'ok'}`}>
                  {latency.p99?.toFixed(2)}ms
                </span>
                <span className="latency-slo">/ {latency.p99_slo}ms SLO</span>
              </div>
            </div>
          </div>
        </div>

        {/* Burn Rate Multi-Window Display */}
        <div className="card">
          <h3>🔥 Burn Rate Analysis (Multi-Window)</h3>
          <div className="burn-rate-grid">
            {['1h', '6h', '24h', '72h'].map(window => {
              const windowData = windows[window];
              if (!windowData) return null;
              
              return (
                <div key={window} className="burn-rate-card">
                  <div className="burn-rate-header">{window} Window</div>
                  <div className="burn-rate-value">{windowData.burn_rate?.toFixed(2)}x</div>
                  <div className="burn-rate-details">
                    <div>Error: {windowData.error_rate?.toFixed(4)}%</div>
                    <div>Budget: {windowData.budget_remaining?.toFixed(4)}%</div>
                  </div>
                  <div className="burn-rate-bar">
                    <div 
                      className="burn-rate-fill"
                      style={{
                        width: `${Math.min(100, (windowData.burn_rate / 20) * 100)}%`,
                        backgroundColor: windowData.burn_rate > 10 ? '#ef4444' : 
                                       windowData.burn_rate > 5 ? '#f59e0b' : 
                                       windowData.burn_rate > 2 ? '#f59e0b' : '#10b981'
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="card">
          <h3>🚨 Recent Alerts</h3>
          <div className="alerts-list">
            {alerts.length === 0 ? (
              <div className="no-alerts">No recent alerts - All services healthy! 🎉</div>
            ) : (
              alerts.map((alert, index) => (
                <div key={index} className="alert-item" style={{
                  borderLeft: `4px solid ${getAlertLevelColor(alert.level)}`
                }}>
                  <div className="alert-header">
                    <span className="alert-level" style={{
                      backgroundColor: getAlertLevelColor(alert.level),
                      color: 'white'
                    }}>
                      {alert.level}
                    </span>
                    <span className="alert-service">{alert.service}</span>
                    <span className="alert-time">
                      {new Date(alert.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="alert-message">{alert.message}</div>
                  <div className="alert-details">
                    Budget State: {alert.budget_state} | Burn Rate: {alert.burn_rate?.toFixed(2)}x
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* All Services Overview */}
        <div className="card">
          <h3>📊 All Services Overview</h3>
          <div className="services-overview">
            {Object.entries(summary).map(([service, data]) => {
              const policy = policies[service] || {};
              const window1h = data.windows?.['1h'] || {};
              
              return (
                <div key={service} className="service-overview-card">
                  <div className="service-overview-header">
                    <h4>{service.toUpperCase()}</h4>
                    <span className="service-state-badge" style={{
                      backgroundColor: getBudgetStateColor(policy.budget_state),
                      color: 'white'
                    }}>
                      {policy.budget_state}
                    </span>
                  </div>
                  <div className="service-overview-metrics">
                    <div className="overview-metric">
                      <span className="overview-label">SLO:</span>
                      <span className="overview-value">{data.slo_config?.availability}%</span>
                    </div>
                    <div className="overview-metric">
                      <span className="overview-label">Burn Rate:</span>
                      <span className="overview-value">{window1h.burn_rate?.toFixed(2)}x</span>
                    </div>
                    <div className="overview-metric">
                      <span className="overview-label">Budget Left:</span>
                      <span className="overview-value">{window1h.budget_remaining?.toFixed(3)}%</span>
                    </div>
                    <div className="overview-metric">
                      <span className="overview-label">Deployments:</span>
                      <span className={`overview-value ${policy.deployment_blocked ? 'blocked' : 'allowed'}`}>
                        {policy.deployment_blocked ? 'BLOCKED' : 'ALLOWED'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
