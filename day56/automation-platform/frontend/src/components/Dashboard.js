import React from 'react';
import './Dashboard.css';

function Dashboard({ data, connected }) {
  if (!data) {
    return (
      <div className="dashboard">
        <div className="loading">Loading automation platform...</div>
      </div>
    );
  }

  const { workflows, healing, chaos, incidents, scheduler } = data;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🤖 Automation Orchestration Platform</h1>
        <div className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '● Live' : '○ Disconnected'}
        </div>
      </header>

      <div className="metrics-grid">
        {/* Workflow Orchestration */}
        <div className="metric-card">
          <h2>⚙️ Workflow Orchestration</h2>
          <div className="metric-value">{workflows.total}</div>
          <div className="metric-label">Total Workflows</div>
          <div className="metric-details">
            <div className="detail-row">
              <span>Active:</span>
              <span className="detail-value active">{workflows.active}</span>
            </div>
            <div className="detail-row">
              <span>Completed:</span>
              <span className="detail-value completed">{workflows.completed}</span>
            </div>
            <div className="detail-row">
              <span>Failed:</span>
              <span className="detail-value failed">{workflows.failed}</span>
            </div>
          </div>
        </div>

        {/* Self-Healing */}
        <div className="metric-card">
          <h2>🔧 Self-Healing</h2>
          <div className="metric-value">{healing.total_actions}</div>
          <div className="metric-label">Healing Actions</div>
          <div className="metric-details">
            <div className="detail-row">
              <span>Success Rate:</span>
              <span className="detail-value">{healing.success_rate.toFixed(1)}%</span>
            </div>
            <div className="detail-row">
              <span>Successful:</span>
              <span className="detail-value completed">{healing.successful_actions}</span>
            </div>
          </div>
          {healing.recent_actions && healing.recent_actions.length > 0 && (
            <div className="recent-actions">
              <h4>Recent Actions:</h4>
              {healing.recent_actions.slice(0, 3).map((action, idx) => (
                <div key={idx} className="action-item">
                  {action.action} - {action.success ? '✓' : '✗'}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Chaos Engineering */}
        <div className="metric-card">
          <h2>💥 Chaos Engineering</h2>
          <div className="metric-value">{chaos.total_experiments}</div>
          <div className="metric-label">Total Experiments</div>
          <div className="metric-details">
            <div className="detail-row">
              <span>Pass Rate:</span>
              <span className="detail-value">{chaos.pass_rate.toFixed(1)}%</span>
            </div>
            <div className="detail-row">
              <span>Passed:</span>
              <span className="detail-value completed">{chaos.passed}</span>
            </div>
            <div className="detail-row">
              <span>Failed:</span>
              <span className="detail-value failed">{chaos.failed}</span>
            </div>
          </div>
        </div>

        {/* Incident Response */}
        <div className="metric-card">
          <h2>🚨 Incident Response</h2>
          <div className="metric-value">{incidents.total_incidents}</div>
          <div className="metric-label">Total Incidents</div>
          <div className="metric-details">
            <div className="detail-row">
              <span>Active:</span>
              <span className="detail-value active">{incidents.active_incidents}</span>
            </div>
            <div className="detail-row">
              <span>Auto-Resolved:</span>
              <span className="detail-value">{incidents.auto_resolution_rate.toFixed(1)}%</span>
            </div>
          </div>
          {incidents.recent_incidents && incidents.recent_incidents.length > 0 && (
            <div className="recent-actions">
              <h4>Recent Incidents:</h4>
              {incidents.recent_incidents.slice(0, 3).map((incident, idx) => (
                <div key={idx} className="action-item">
                  {incident.description} - {incident.auto_resolved ? '✓ Auto' : '⚠ Manual'}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* AI Scheduler */}
        <div className="metric-card">
          <h2>🧠 AI Scheduler</h2>
          <div className="metric-value">{scheduler.scheduled_workflows}</div>
          <div className="metric-label">Scheduled Workflows</div>
          <div className="metric-details">
            <div className="detail-row">
              <span>Current Load:</span>
              <span className="detail-value">{(scheduler.current_load * 100).toFixed(1)}%</span>
            </div>
            <div className="detail-row">
              <span>Efficiency:</span>
              <span className="detail-value">{(scheduler.optimization_efficiency * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* System Overview */}
        <div className="metric-card wide">
          <h2>📊 System Overview</h2>
          <div className="overview-grid">
            <div className="overview-item">
              <div className="overview-label">Automation Level</div>
              <div className="progress-bar">
                <div className="progress-fill" style={{width: '94%'}}></div>
              </div>
              <div className="overview-value">94% Automated</div>
            </div>
            <div className="overview-item">
              <div className="overview-label">Platform Health</div>
              <div className="progress-bar">
                <div className="progress-fill health" style={{width: '99%'}}></div>
              </div>
              <div className="overview-value">99% Healthy</div>
            </div>
            <div className="overview-item">
              <div className="overview-label">Resource Utilization</div>
              <div className="progress-bar">
                <div className="progress-fill resource" style={{width: `${scheduler.current_load * 100}%`}}></div>
              </div>
              <div className="overview-value">{(scheduler.current_load * 100).toFixed(0)}% Utilized</div>
            </div>
          </div>
        </div>
      </div>

      <footer className="dashboard-footer">
        <p>Netflix-Scale Automation Platform | Real-time Monitoring & Self-Healing</p>
      </footer>
    </div>
  );
}

export default Dashboard;
