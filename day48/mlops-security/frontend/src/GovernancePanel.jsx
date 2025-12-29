import React from 'react';

function GovernancePanel({ stats }) {
  if (!stats) {
    return <div style={styles.loading}>Loading governance data...</div>;
  }

  const stateData = stats.by_state || {};
  const totalWorkflows = stats.total_workflows || 0;

  const stateInfo = {
    draft: { label: 'Draft', color: '#6b7280', icon: '📝' },
    data_validated: { label: 'Data Validated', color: '#3b82f6', icon: '✓' },
    performance_approved: { label: 'Performance Approved', color: '#8b5cf6', icon: '📊' },
    security_cleared: { label: 'Security Cleared', color: '#06b6d4', icon: '🔒' },
    compliance_verified: { label: 'Compliance Verified', color: '#10b981', icon: '📋' },
    approved: { label: 'Approved', color: '#22c55e', icon: '✓✓' },
    deployed: { label: 'Deployed', color: '#4ade80', icon: '🚀' },
    rejected: { label: 'Rejected', color: '#ef4444', icon: '✗' },
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.sectionTitle}>Governance Workflows</h2>

      <div style={styles.summaryCard}>
        <div style={styles.summaryItem}>
          <div style={styles.summaryLabel}>Total Workflows</div>
          <div style={styles.summaryValue}>{totalWorkflows}</div>
        </div>
        <div style={styles.summaryItem}>
          <div style={styles.summaryLabel}>Active</div>
          <div style={styles.summaryValue}>
            {Object.keys(stateData).filter(s => !['deployed', 'rejected'].includes(s)).reduce((sum, s) => sum + stateData[s], 0)}
          </div>
        </div>
        <div style={styles.summaryItem}>
          <div style={styles.summaryLabel}>Deployed</div>
          <div style={styles.summaryValue}>{stateData.deployed || 0}</div>
        </div>
        <div style={styles.summaryItem}>
          <div style={styles.summaryLabel}>Rejected</div>
          <div style={styles.summaryValue}>{stateData.rejected || 0}</div>
        </div>
      </div>

      <div style={styles.stateGrid}>
        {Object.entries(stateInfo).map(([state, info]) => {
          const count = stateData[state] || 0;
          return (
            <div key={state} style={{...styles.stateCard, borderLeftColor: info.color}}>
              <div style={styles.stateHeader}>
                <span style={styles.stateIcon}>{info.icon}</span>
                <span style={styles.stateLabel}>{info.label}</span>
              </div>
              <div style={styles.stateCount}>{count}</div>
              <div style={styles.stateProgress}>
                <div style={{
                  ...styles.stateProgressBar,
                  width: `${totalWorkflows > 0 ? (count / totalWorkflows * 100) : 0}%`,
                  backgroundColor: info.color
                }}></div>
              </div>
            </div>
          );
        })}
      </div>

      <div style={styles.workflowStages}>
        <h3 style={styles.subsectionTitle}>Approval Pipeline</h3>
        <div style={styles.pipeline}>
          {['Draft', 'Data Validation', 'Performance Review', 'Security Audit', 'Compliance Check', 'Stakeholder Approval', 'Deployed'].map((stage, idx) => (
            <React.Fragment key={stage}>
              <div style={styles.pipelineStage}>
                <div style={styles.stageDot}></div>
                <div style={styles.stageName}>{stage}</div>
              </div>
              {idx < 6 && <div style={styles.pipelineArrow}>→</div>}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '1400px',
    margin: '0 auto',
  },
  loading: {
    textAlign: 'center',
    padding: '3rem',
    fontSize: '1.2rem',
    color: '#9aa5b8',
  },
  sectionTitle: {
    fontSize: '2rem',
    marginBottom: '2rem',
    color: '#e8eaed',
    fontWeight: 600,
  },
  subsectionTitle: {
    fontSize: '1.5rem',
    marginBottom: '1rem',
    color: '#e8eaed',
    fontWeight: 600,
  },
  summaryCard: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1.5rem',
    marginBottom: '2rem',
    backgroundColor: '#1a1f2e',
    padding: '2rem',
    borderRadius: '12px',
    border: '1px solid #2a3142',
  },
  summaryItem: {
    textAlign: 'center',
  },
  summaryLabel: {
    fontSize: '0.9rem',
    color: '#9aa5b8',
    marginBottom: '0.5rem',
  },
  summaryValue: {
    fontSize: '2.5rem',
    fontWeight: 700,
    color: '#e8eaed',
  },
  stateGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: '1rem',
    marginBottom: '2rem',
  },
  stateCard: {
    backgroundColor: '#1a1f2e',
    borderRadius: '8px',
    padding: '1.5rem',
    border: '1px solid #2a3142',
    borderLeft: '4px solid',
  },
  stateHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '1rem',
  },
  stateIcon: {
    fontSize: '1.2rem',
  },
  stateLabel: {
    fontSize: '0.85rem',
    color: '#9aa5b8',
  },
  stateCount: {
    fontSize: '2rem',
    fontWeight: 700,
    color: '#e8eaed',
    marginBottom: '0.5rem',
  },
  stateProgress: {
    width: '100%',
    height: '4px',
    backgroundColor: '#2a3142',
    borderRadius: '2px',
    overflow: 'hidden',
  },
  stateProgressBar: {
    height: '100%',
    transition: 'width 0.5s ease',
  },
  workflowStages: {
    backgroundColor: '#1a1f2e',
    borderRadius: '12px',
    padding: '2rem',
    border: '1px solid #2a3142',
  },
  pipeline: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    overflowX: 'auto',
    padding: '1rem 0',
  },
  pipelineStage: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '0.5rem',
    minWidth: '100px',
  },
  stageDot: {
    width: '16px',
    height: '16px',
    borderRadius: '50%',
    backgroundColor: '#4ade80',
    border: '2px solid #0f1419',
  },
  stageName: {
    fontSize: '0.85rem',
    color: '#9aa5b8',
    textAlign: 'center',
  },
  pipelineArrow: {
    fontSize: '1.5rem',
    color: '#4a5568',
  },
};

export default GovernancePanel;
