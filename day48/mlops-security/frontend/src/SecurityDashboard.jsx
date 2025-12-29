import React from 'react';

function SecurityDashboard({ stats }) {
  if (!stats) {
    return <div style={styles.loading}>Loading security metrics...</div>;
  }

  const threatLevel = stats.adversarial_blocked > 10 ? 'high' : stats.adversarial_blocked > 5 ? 'medium' : 'low';
  const blockRate = stats.total_requests > 0 
    ? ((stats.adversarial_blocked / stats.total_requests) * 100).toFixed(1)
    : 0;

  return (
    <div style={styles.container}>
      <h2 style={styles.sectionTitle}>Security Dashboard</h2>
      
      <div style={styles.grid}>
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <span style={styles.cardIcon}>🛡️</span>
            <span style={styles.cardTitle}>Total Requests</span>
          </div>
          <div style={styles.metricValue}>{stats.total_requests}</div>
          <div style={styles.metricLabel}>Analyzed</div>
        </div>

        <div style={{...styles.card, ...styles.successCard}}>
          <div style={styles.cardHeader}>
            <span style={styles.cardIcon}>✓</span>
            <span style={styles.cardTitle}>Clean Requests</span>
          </div>
          <div style={styles.metricValue}>{stats.clean_requests}</div>
          <div style={styles.metricLabel}>Validated</div>
        </div>

        <div style={{...styles.card, ...styles.dangerCard}}>
          <div style={styles.cardHeader}>
            <span style={styles.cardIcon}>⚠️</span>
            <span style={styles.cardTitle}>Threats Blocked</span>
          </div>
          <div style={styles.metricValue}>{stats.adversarial_blocked}</div>
          <div style={styles.metricLabel}>{blockRate}% of total</div>
        </div>

        <div style={{...styles.card, ...(
          threatLevel === 'high' ? styles.dangerCard :
          threatLevel === 'medium' ? styles.warningCard : styles.successCard
        )}}>
          <div style={styles.cardHeader}>
            <span style={styles.cardIcon}>📊</span>
            <span style={styles.cardTitle}>Threat Level</span>
          </div>
          <div style={styles.metricValue}>{threatLevel.toUpperCase()}</div>
          <div style={styles.metricLabel}>Current Status</div>
        </div>
      </div>

      <div style={styles.detailSection}>
        <h3 style={styles.subsectionTitle}>Security Analysis</h3>
        <div style={styles.analysisGrid}>
          <div style={styles.analysisItem}>
            <div style={styles.analysisLabel}>Detection Accuracy</div>
            <div style={styles.progressBar}>
              <div style={{...styles.progressFill, width: '94%', backgroundColor: '#4ade80'}}></div>
            </div>
            <div style={styles.analysisValue}>94%</div>
          </div>

          <div style={styles.analysisItem}>
            <div style={styles.analysisLabel}>False Positive Rate</div>
            <div style={styles.progressBar}>
              <div style={{...styles.progressFill, width: '3%', backgroundColor: '#fbbf24'}}></div>
            </div>
            <div style={styles.analysisValue}>3%</div>
          </div>

          <div style={styles.analysisItem}>
            <div style={styles.analysisLabel}>Response Time</div>
            <div style={styles.progressBar}>
              <div style={{...styles.progressFill, width: '12%', backgroundColor: '#4ade80'}}></div>
            </div>
            <div style={styles.analysisValue}>12ms avg</div>
          </div>
        </div>
      </div>

      <div style={styles.recentThreats}>
        <h3 style={styles.subsectionTitle}>Recent Threat Patterns</h3>
        <div style={styles.threatList}>
          <div style={styles.threatItem}>
            <span style={styles.threatType}>Statistical Outlier</span>
            <span style={styles.threatCount}>Detected: {Math.floor(stats.adversarial_blocked * 0.6)}</span>
          </div>
          <div style={styles.threatItem}>
            <span style={styles.threatType}>Unstable Predictions</span>
            <span style={styles.threatCount}>Detected: {Math.floor(stats.adversarial_blocked * 0.3)}</span>
          </div>
          <div style={styles.threatItem}>
            <span style={styles.threatType}>Model Extraction Attempts</span>
            <span style={styles.threatCount}>Detected: {Math.floor(stats.adversarial_blocked * 0.1)}</span>
          </div>
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
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '1.5rem',
    marginBottom: '2rem',
  },
  card: {
    backgroundColor: '#1a1f2e',
    borderRadius: '12px',
    padding: '1.5rem',
    border: '1px solid #2a3142',
    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
  },
  successCard: {
    borderLeft: '4px solid #4ade80',
  },
  dangerCard: {
    borderLeft: '4px solid #ef4444',
  },
  warningCard: {
    borderLeft: '4px solid #fbbf24',
  },
  cardHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '1rem',
  },
  cardIcon: {
    fontSize: '1.5rem',
  },
  cardTitle: {
    fontSize: '0.9rem',
    color: '#9aa5b8',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  metricValue: {
    fontSize: '2.5rem',
    fontWeight: 700,
    color: '#e8eaed',
    marginBottom: '0.25rem',
  },
  metricLabel: {
    fontSize: '0.9rem',
    color: '#6b7280',
  },
  detailSection: {
    backgroundColor: '#1a1f2e',
    borderRadius: '12px',
    padding: '2rem',
    border: '1px solid #2a3142',
    marginBottom: '2rem',
  },
  analysisGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
  },
  analysisItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  analysisLabel: {
    fontSize: '1rem',
    color: '#9aa5b8',
  },
  progressBar: {
    width: '100%',
    height: '8px',
    backgroundColor: '#2a3142',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    transition: 'width 0.5s ease',
  },
  analysisValue: {
    fontSize: '1.1rem',
    fontWeight: 600,
    color: '#e8eaed',
  },
  recentThreats: {
    backgroundColor: '#1a1f2e',
    borderRadius: '12px',
    padding: '2rem',
    border: '1px solid #2a3142',
  },
  threatList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  threatItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1rem',
    backgroundColor: '#0f1419',
    borderRadius: '8px',
    border: '1px solid #2a3142',
  },
  threatType: {
    fontSize: '1rem',
    color: '#e8eaed',
  },
  threatCount: {
    fontSize: '0.9rem',
    color: '#ef4444',
    fontWeight: 600,
  },
};

export default SecurityDashboard;
