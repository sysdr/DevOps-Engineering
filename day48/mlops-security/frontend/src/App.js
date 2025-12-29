import React, { useState, useEffect } from 'react';
import SecurityDashboard from './SecurityDashboard';
import GovernancePanel from './GovernancePanel';
import ComplianceView from './ComplianceView';

function App() {
  const [activeTab, setActiveTab] = useState('security');
  const [stats, setStats] = useState(null);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    // Fetch initial stats
    fetch('http://localhost:8000/api/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error('Error fetching stats:', err));

    // Setup WebSocket for real-time updates
    const websocket = new WebSocket('ws://localhost:8000/ws/stats');
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStats(data);
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    setWs(websocket);

    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, []);

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>MLOps Security & Governance Platform</h1>
        <p style={styles.subtitle}>Production-Grade ML Trust & Safety</p>
      </header>

      <nav style={styles.nav}>
        <button
          style={{...styles.tab, ...(activeTab === 'security' ? styles.activeTab : {})}}
          onClick={() => setActiveTab('security')}
        >
          Security Dashboard
        </button>
        <button
          style={{...styles.tab, ...(activeTab === 'governance' ? styles.activeTab : {})}}
          onClick={() => setActiveTab('governance')}
        >
          Governance
        </button>
        <button
          style={{...styles.tab, ...(activeTab === 'compliance' ? styles.activeTab : {})}}
          onClick={() => setActiveTab('compliance')}
        >
          Compliance
        </button>
      </nav>

      <main style={styles.main}>
        {activeTab === 'security' && <SecurityDashboard stats={stats?.security} />}
        {activeTab === 'governance' && <GovernancePanel stats={stats?.governance} />}
        {activeTab === 'compliance' && <ComplianceView stats={stats} />}
      </main>

      <footer style={styles.footer}>
        <div style={styles.statusIndicator}>
          <span style={styles.statusDot}></span>
          System Active | Audit Chain: {stats?.audit?.total_events || 0} events
        </div>
      </footer>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#0a0e1a',
    color: '#e8eaed',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  header: {
    background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a8c 100%)',
    padding: '2rem',
    borderBottom: '3px solid #4a90e2',
  },
  title: {
    margin: 0,
    fontSize: '2.5rem',
    fontWeight: 700,
    color: '#ffffff',
  },
  subtitle: {
    margin: '0.5rem 0 0 0',
    fontSize: '1.1rem',
    color: '#b8d4ff',
  },
  nav: {
    display: 'flex',
    gap: '1rem',
    padding: '1rem 2rem',
    backgroundColor: '#141820',
    borderBottom: '1px solid #2a3142',
  },
  tab: {
    padding: '0.75rem 1.5rem',
    border: 'none',
    borderRadius: '8px',
    backgroundColor: 'transparent',
    color: '#9aa5b8',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: 500,
    transition: 'all 0.3s ease',
  },
  activeTab: {
    backgroundColor: '#2d5a8c',
    color: '#ffffff',
  },
  main: {
    padding: '2rem',
    minHeight: 'calc(100vh - 250px)',
  },
  footer: {
    padding: '1rem 2rem',
    backgroundColor: '#141820',
    borderTop: '1px solid #2a3142',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    color: '#9aa5b8',
  },
  statusDot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    backgroundColor: '#4ade80',
    animation: 'pulse 2s infinite',
  },
};

export default App;
