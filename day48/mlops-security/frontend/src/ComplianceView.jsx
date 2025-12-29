import React, { useState } from 'react';

function ComplianceView({ stats }) {
  const [isHovered, setIsHovered] = useState(false);

  if (!stats) {
    return <div style={styles.loading}>Loading compliance data...</div>;
  }

  const auditStats = stats.audit || {};
  const biasStats = stats.bias || {};

  const handleDownloadModelCard = async () => {
    try {
      const modelId = 'fraud_detection_v1';
      const response = await fetch(`http://localhost:8000/api/compliance/model-card/${modelId}/download`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Server error:', response.status, errorText);
        throw new Error(`Failed to download model card: ${response.status} ${response.statusText}`);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${modelId}_model_card.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading model card:', error);
      alert(`Failed to download model card: ${error.message}. Please check the console for details.`);
    }
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.sectionTitle}>Compliance & Audit</h2>

      <div style={styles.grid}>
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Audit Trail</h3>
          <div style={styles.metricRow}>
            <span style={styles.metricLabel}>Total Events:</span>
            <span style={styles.metricValue}>{auditStats.total_events || 0}</span>
          </div>
          <div style={styles.metricRow}>
            <span style={styles.metricLabel}>Chain Integrity:</span>
            <span style={{...styles.metricValue, color: '#4ade80'}}>✓ Verified</span>
          </div>
          <div style={styles.eventTypes}>
            <div style={styles.eventTypeLabel}>Event Types:</div>
            {Object.entries(auditStats.by_type || {}).map(([type, count]) => (
              <div key={type} style={styles.eventTypeRow}>
                <span style={styles.eventType}>{type.replace(/_/g, ' ')}</span>
                <span style={styles.eventCount}>{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Bias Monitoring</h3>
          <div style={styles.metricRow}>
            <span style={styles.metricLabel}>Models Analyzed:</span>
            <span style={styles.metricValue}>{biasStats.models_analyzed || 0}</span>
          </div>
          <div style={styles.metricRow}>
            <span style={styles.metricLabel}>Total Violations:</span>
            <span style={{...styles.metricValue, color: biasStats.total_violations > 0 ? '#ef4444' : '#4ade80'}}>
              {biasStats.total_violations || 0}
            </span>
          </div>
          <div style={styles.fairnessMetrics}>
            <div style={styles.metricItem}>
              <div style={styles.metricItemLabel}>Demographic Parity</div>
              <div style={styles.progressBar}>
                <div style={{...styles.progressFill, width: '87%', backgroundColor: '#fbbf24'}}></div>
              </div>
              <div style={styles.metricItemValue}>0.87 / 0.80 threshold</div>
            </div>
            <div style={styles.metricItem}>
              <div style={styles.metricItemLabel}>Equal Opportunity</div>
              <div style={styles.progressBar}>
                <div style={{...styles.progressFill, width: '95%', backgroundColor: '#4ade80'}}></div>
              </div>
              <div style={styles.metricItemValue}>0.95 / 0.90 threshold</div>
            </div>
          </div>
        </div>
      </div>

      <div style={styles.complianceFrameworks}>
        <h3 style={styles.subsectionTitle}>Compliance Frameworks</h3>
        <div style={styles.frameworkGrid}>
          {[
            { name: 'GDPR', status: 'Compliant', icon: '🇪🇺' },
            { name: 'SOC 2', status: 'Compliant', icon: '🔒' },
            { name: 'HIPAA', status: 'Pending Review', icon: '⚕️' },
            { name: 'ISO 27001', status: 'Compliant', icon: '📋' },
          ].map(framework => (
            <div key={framework.name} style={styles.frameworkCard}>
              <div style={styles.frameworkIcon}>{framework.icon}</div>
              <div style={styles.frameworkName}>{framework.name}</div>
              <div style={{
                ...styles.frameworkStatus,
                color: framework.status === 'Compliant' ? '#4ade80' : '#fbbf24'
              }}>
                {framework.status}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={styles.modelCardSection}>
        <h3 style={styles.subsectionTitle}>Model Documentation</h3>
        <div style={styles.modelCardPreview}>
          <div style={styles.modelCardHeader}>
            <span style={styles.modelCardTitle}>fraud_detection_v1</span>
            <button 
              style={{
                ...styles.downloadButton,
                backgroundColor: isHovered ? '#3a6ba5' : '#2d5a8c'
              }}
              onClick={handleDownloadModelCard}
              onMouseEnter={() => setIsHovered(true)}
              onMouseLeave={() => setIsHovered(false)}
            >
              Download Model Card
            </button>
          </div>
          <div style={styles.modelCardContent}>
            <div style={styles.modelCardRow}>
              <span style={styles.modelCardLabel}>Algorithm:</span>
              <span style={styles.modelCardValue}>XGBoost Classifier</span>
            </div>
            <div style={styles.modelCardRow}>
              <span style={styles.modelCardLabel}>Owner:</span>
              <span style={styles.modelCardValue}>ml-team</span>
            </div>
            <div style={styles.modelCardRow}>
              <span style={styles.modelCardLabel}>Training Samples:</span>
              <span style={styles.modelCardValue}>1,000,000</span>
            </div>
            <div style={styles.modelCardRow}>
              <span style={styles.modelCardLabel}>Performance (F1):</span>
              <span style={styles.modelCardValue}>0.90</span>
            </div>
            <div style={styles.modelCardRow}>
              <span style={styles.modelCardLabel}>Explainability:</span>
              <span style={styles.modelCardValue}>SHAP values available</span>
            </div>
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
    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
    gap: '1.5rem',
    marginBottom: '2rem',
  },
  card: {
    backgroundColor: '#1a1f2e',
    borderRadius: '12px',
    padding: '1.5rem',
    border: '1px solid #2a3142',
  },
  cardTitle: {
    fontSize: '1.3rem',
    color: '#e8eaed',
    marginBottom: '1rem',
    fontWeight: 600,
  },
  metricRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.75rem 0',
    borderBottom: '1px solid #2a3142',
  },
  metricLabel: {
    fontSize: '1rem',
    color: '#9aa5b8',
  },
  metricValue: {
    fontSize: '1.1rem',
    fontWeight: 600,
    color: '#e8eaed',
  },
  eventTypes: {
    marginTop: '1rem',
  },
  eventTypeLabel: {
    fontSize: '0.9rem',
    color: '#9aa5b8',
    marginBottom: '0.5rem',
  },
  eventTypeRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '0.5rem 0',
    fontSize: '0.9rem',
  },
  eventType: {
    color: '#b8d4ff',
    textTransform: 'capitalize',
  },
  eventCount: {
    color: '#6b7280',
  },
  fairnessMetrics: {
    marginTop: '1rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  metricItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  metricItemLabel: {
    fontSize: '0.9rem',
    color: '#9aa5b8',
  },
  progressBar: {
    width: '100%',
    height: '6px',
    backgroundColor: '#2a3142',
    borderRadius: '3px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    transition: 'width 0.5s ease',
  },
  metricItemValue: {
    fontSize: '0.85rem',
    color: '#6b7280',
  },
  complianceFrameworks: {
    marginBottom: '2rem',
  },
  frameworkGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
  },
  frameworkCard: {
    backgroundColor: '#1a1f2e',
    borderRadius: '8px',
    padding: '1.5rem',
    border: '1px solid #2a3142',
    textAlign: 'center',
  },
  frameworkIcon: {
    fontSize: '2.5rem',
    marginBottom: '0.5rem',
  },
  frameworkName: {
    fontSize: '1.1rem',
    color: '#e8eaed',
    fontWeight: 600,
    marginBottom: '0.5rem',
  },
  frameworkStatus: {
    fontSize: '0.9rem',
    fontWeight: 500,
  },
  modelCardSection: {},
  modelCardPreview: {
    backgroundColor: '#1a1f2e',
    borderRadius: '12px',
    padding: '1.5rem',
    border: '1px solid #2a3142',
  },
  modelCardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
    paddingBottom: '1rem',
    borderBottom: '1px solid #2a3142',
  },
  modelCardTitle: {
    fontSize: '1.2rem',
    color: '#e8eaed',
    fontWeight: 600,
  },
  downloadButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#2d5a8c',
    color: '#ffffff',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    fontWeight: 500,
    transition: 'background-color 0.2s ease',
  },
  modelCardContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  modelCardRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '0.5rem 0',
  },
  modelCardLabel: {
    fontSize: '0.95rem',
    color: '#9aa5b8',
  },
  modelCardValue: {
    fontSize: '0.95rem',
    color: '#e8eaed',
    fontWeight: 500,
  },
};

export default ComplianceView;
