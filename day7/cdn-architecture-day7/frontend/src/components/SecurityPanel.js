import React, { useState, useEffect } from 'react';

const SecurityPanel = () => {
  const [securityStats, setSecurityStats] = useState(null);

  useEffect(() => {
    // Mock security data for demo
    setSecurityStats({
      blocked_ips: ['192.168.100.50', '10.0.0.100'],
      active_connections: {
        '192.168.1.10': 45,
        '192.168.1.20': 32,
        '192.168.1.30': 28
      },
      security_rules: [
        { name: 'allow_http', action: 'allow', rate_limit: 0 },
        { name: 'rate_limit_api', action: 'rate_limit', rate_limit: 100 },
        { name: 'block_suspicious', action: 'deny', rate_limit: 0 }
      ],
      total_ips_tracked: 156
    });
  }, []);

  if (!securityStats) {
    return <div className="loading">Loading security information...</div>;
  }

  return (
    <div className="security-panel">
      <h2>🔒 Network Security Overview</h2>
      
      <div className="security-overview">
        <div className="security-card">
          <h3>🚫 Blocked IPs</h3>
          <div className="metric-value">{securityStats.blocked_ips.length}</div>
          <div className="blocked-ip-list">
            {securityStats.blocked_ips.map(ip => (
              <div key={ip} className="blocked-ip">{ip}</div>
            ))}
          </div>
        </div>
        
        <div className="security-card">
          <h3>🔄 Active Connections</h3>
          <div className="metric-value">{Object.keys(securityStats.active_connections).length}</div>
          <div className="connection-list">
            {Object.entries(securityStats.active_connections).map(([ip, count]) => (
              <div key={ip} className="connection-item">
                <span className="ip">{ip}</span>
                <span className="count">{count} req/min</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="security-card">
          <h3>📊 Total IPs Tracked</h3>
          <div className="metric-value">{securityStats.total_ips_tracked}</div>
          <div className="security-note">Monitoring for suspicious activity</div>
        </div>
      </div>

      <div className="security-rules">
        <h3>⚙️ Security Rules</h3>
        <table className="rules-table">
          <thead>
            <tr>
              <th>Rule Name</th>
              <th>Action</th>
              <th>Rate Limit</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {securityStats.security_rules.map(rule => (
              <tr key={rule.name}>
                <td>{rule.name}</td>
                <td>
                  <span className={`action-badge ${rule.action}`}>
                    {rule.action.toUpperCase()}
                  </span>
                </td>
                <td>{rule.rate_limit || 'No Limit'}</td>
                <td>
                  <span className="status-badge active">🟢 Active</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="security-alerts">
        <h3>🚨 Recent Security Events</h3>
        <div className="alert-list">
          <div className="alert-item warning">
            <span className="alert-icon">⚠️</span>
            <span className="alert-message">Rate limit exceeded for 192.168.1.25</span>
            <span className="alert-time">2 minutes ago</span>
          </div>
          <div className="alert-item info">
            <span className="alert-icon">ℹ️</span>
            <span className="alert-message">New security rule activated: block_suspicious</span>
            <span className="alert-time">15 minutes ago</span>
          </div>
          <div className="alert-item success">
            <span className="alert-icon">✅</span>
            <span className="alert-message">All systems healthy - no threats detected</span>
            <span className="alert-time">1 hour ago</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SecurityPanel;
