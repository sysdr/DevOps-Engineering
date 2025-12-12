import React, { useState, useEffect } from 'react';

const API_URL = 'http://localhost:8000';

function App() {
  const [secrets, setSecrets] = useState([]);
  const [certificates, setCertificates] = useState([]);
  const [leases, setLeases] = useState([]);
  const [k8sSecrets, setK8sSecrets] = useState({});
  const [auditLogs, setAuditLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [newSecret, setNewSecret] = useState({ path: '', key: '', value: '' });
  const [newCert, setNewCert] = useState({ domain: '', issuer: 'letsencrypt' });
  const [newDynamicCred, setNewDynamicCred] = useState({ role: 'readonly', ttl_hours: 24 });

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, certsRes, leasesRes, k8sRes, auditRes] = await Promise.all([
        fetch(`${API_URL}/stats`),
        fetch(`${API_URL}/certificates`),
        fetch(`${API_URL}/dynamic/leases`),
        fetch(`${API_URL}/external-secrets/k8s`),
        fetch(`${API_URL}/vault/audit?limit=20`)
      ]);

      setStats(await statsRes.json());
      const certsData = await certsRes.json();
      setCertificates(certsData.certificates || []);
      const leasesData = await leasesRes.json();
      setLeases(leasesData.leases || []);
      const k8sData = await k8sRes.json();
      setK8sSecrets(k8sData.secrets || {});
      const auditData = await auditRes.json();
      setAuditLogs(auditData.logs || []);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const createSecret = async () => {
    try {
      await fetch(`${API_URL}/vault/secrets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path: newSecret.path,
          data: { [newSecret.key]: newSecret.value }
        })
      });
      setNewSecret({ path: '', key: '', value: '' });
      loadData();
    } catch (error) {
      console.error('Error creating secret:', error);
    }
  };

  const issueCertificate = async () => {
    try {
      await fetch(`${API_URL}/certificates/issue`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newCert)
      });
      setNewCert({ domain: '', issuer: 'letsencrypt' });
      loadData();
    } catch (error) {
      console.error('Error issuing certificate:', error);
    }
  };

  const generateDynamicCreds = async () => {
    try {
      await fetch(`${API_URL}/dynamic/database`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newDynamicCred)
      });
      loadData();
    } catch (error) {
      console.error('Error generating credentials:', error);
    }
  };

  const renewCertificate = async (domain) => {
    try {
      await fetch(`${API_URL}/certificates/${domain}/renew`, { method: 'POST' });
      loadData();
    } catch (error) {
      console.error('Error renewing certificate:', error);
    }
  };

  const revokeLease = async (leaseId) => {
    try {
      await fetch(`${API_URL}/dynamic/leases/${leaseId}`, { method: 'DELETE' });
      loadData();
    } catch (error) {
      console.error('Error revoking lease:', error);
    }
  };

  const getDaysUntilExpiry = (expiresAt) => {
    const days = Math.floor((new Date(expiresAt) - new Date()) / (1000 * 60 * 60 * 24));
    return days;
  };

  const getExpiryColor = (days) => {
    if (days < 7) return '#ff4444';
    if (days < 30) return '#ffaa00';
    return '#00cc66';
  };

  return (
    <div style={{ 
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      backgroundColor: '#0a0e1a',
      color: '#e0e6ed',
      minHeight: '100vh',
      padding: '20px'
    }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{
          background: 'linear-gradient(135deg, #1a2332 0%, #0f1419 100%)',
          padding: '30px',
          borderRadius: '12px',
          marginBottom: '20px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
        }}>
          <h1 style={{ margin: '0 0 10px 0', fontSize: '32px', fontWeight: '600' }}>
            🔐 Secrets Management System
          </h1>
          <p style={{ margin: 0, color: '#8892a6', fontSize: '16px' }}>
            Enterprise-grade secrets, certificates, and dynamic credentials
          </p>
        </div>

        {/* Statistics Cards */}
        {stats && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '15px',
            marginBottom: '20px'
          }}>
            <StatCard
              title="Vault Secrets"
              value={stats.vault.total_secrets}
              subtitle={`${stats.vault.total_versions} versions`}
              icon="🔑"
              color="#4a9eff"
            />
            <StatCard
              title="Certificates"
              value={stats.certificates.total}
              subtitle={`${stats.certificates.expiring_soon} expiring`}
              icon="📜"
              color="#00cc66"
            />
            <StatCard
              title="Active Leases"
              value={stats.dynamic_secrets.active_leases}
              subtitle="Dynamic credentials"
              icon="⚡"
              color="#ff6b35"
            />
            <StatCard
              title="K8s Secrets"
              value={stats.k8s_secrets.synced}
              subtitle="Synced secrets"
              icon="☸️"
              color="#9b59b6"
            />
            <StatCard
              title="Rotations"
              value={stats.rotation.total_rotations}
              subtitle={`${stats.rotation.policies} policies`}
              icon="🔄"
              color="#f39c12"
            />
            <StatCard
              title="Audit Logs"
              value={stats.vault.total_audit_logs}
              subtitle="Total events"
              icon="📋"
              color="#1abc9c"
            />
          </div>
        )}

        {/* Tabs */}
        <div style={{
          display: 'flex',
          gap: '10px',
          marginBottom: '20px',
          borderBottom: '2px solid #1a2332',
          paddingBottom: '10px'
        }}>
          {['overview', 'secrets', 'certificates', 'dynamic', 'audit'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '10px 20px',
                background: activeTab === tab ? '#4a9eff' : 'transparent',
                color: activeTab === tab ? '#fff' : '#8892a6',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s'
              }}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{
          background: '#1a2332',
          padding: '25px',
          borderRadius: '12px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
        }}>
          {activeTab === 'overview' && (
            <OverviewTab
              certificates={certificates}
              leases={leases}
              k8sSecrets={k8sSecrets}
              getDaysUntilExpiry={getDaysUntilExpiry}
              getExpiryColor={getExpiryColor}
            />
          )}

          {activeTab === 'secrets' && (
            <SecretsTab
              newSecret={newSecret}
              setNewSecret={setNewSecret}
              createSecret={createSecret}
              k8sSecrets={k8sSecrets}
            />
          )}

          {activeTab === 'certificates' && (
            <CertificatesTab
              certificates={certificates}
              newCert={newCert}
              setNewCert={setNewCert}
              issueCertificate={issueCertificate}
              renewCertificate={renewCertificate}
              getDaysUntilExpiry={getDaysUntilExpiry}
              getExpiryColor={getExpiryColor}
            />
          )}

          {activeTab === 'dynamic' && (
            <DynamicTab
              leases={leases}
              newDynamicCred={newDynamicCred}
              setNewDynamicCred={setNewDynamicCred}
              generateDynamicCreds={generateDynamicCreds}
              revokeLease={revokeLease}
            />
          )}

          {activeTab === 'audit' && (
            <AuditTab auditLogs={auditLogs} />
          )}
        </div>
      </div>
    </div>
  );
}

const StatCard = ({ title, value, subtitle, icon, color }) => (
  <div style={{
    background: 'linear-gradient(135deg, #1a2332 0%, #0f1419 100%)',
    padding: '20px',
    borderRadius: '10px',
    borderLeft: `4px solid ${color}`,
    boxShadow: '0 2px 10px rgba(0,0,0,0.2)'
  }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div>
        <div style={{ color: '#8892a6', fontSize: '13px', marginBottom: '5px' }}>{title}</div>
        <div style={{ fontSize: '28px', fontWeight: '600', marginBottom: '5px' }}>{value}</div>
        <div style={{ color: '#8892a6', fontSize: '12px' }}>{subtitle}</div>
      </div>
      <div style={{ fontSize: '32px' }}>{icon}</div>
    </div>
  </div>
);

const OverviewTab = ({ certificates, leases, k8sSecrets, getDaysUntilExpiry, getExpiryColor }) => (
  <div style={{ display: 'grid', gap: '20px' }}>
    <Section title="Expiring Certificates">
      {certificates.filter(c => getDaysUntilExpiry(c.expires_at) < 30).length === 0 ? (
        <p style={{ color: '#8892a6', margin: 0 }}>All certificates valid for 30+ days</p>
      ) : (
        certificates
          .filter(c => getDaysUntilExpiry(c.expires_at) < 30)
          .map((cert, i) => {
            const days = getDaysUntilExpiry(cert.expires_at);
            return (
              <div key={i} style={{
                padding: '12px',
                background: '#0f1419',
                borderRadius: '6px',
                marginBottom: '8px',
                borderLeft: `3px solid ${getExpiryColor(days)}`
              }}>
                <div style={{ fontWeight: '500' }}>{cert.domain}</div>
                <div style={{ color: '#8892a6', fontSize: '13px', marginTop: '4px' }}>
                  Expires in {days} days • {cert.issuer}
                </div>
              </div>
            );
          })
      )}
    </Section>

    <Section title="Active Dynamic Credentials">
      <div style={{ color: '#8892a6', fontSize: '14px' }}>
        {leases.length} active lease{leases.length !== 1 ? 's' : ''} • Auto-expiring credentials
      </div>
    </Section>

    <Section title="Synced Kubernetes Secrets">
      <div style={{ color: '#8892a6', fontSize: '14px' }}>
        {Object.keys(k8sSecrets).length} secret{Object.keys(k8sSecrets).length !== 1 ? 's' : ''} synced from Vault
      </div>
    </Section>
  </div>
);

const SecretsTab = ({ newSecret, setNewSecret, createSecret, k8sSecrets }) => (
  <div>
    <Section title="Create New Secret">
      <div style={{ display: 'grid', gap: '12px', maxWidth: '600px' }}>
        <Input
          placeholder="Secret path (e.g., database/prod/password)"
          value={newSecret.path}
          onChange={e => setNewSecret({ ...newSecret, path: e.target.value })}
        />
        <Input
          placeholder="Key (e.g., password)"
          value={newSecret.key}
          onChange={e => setNewSecret({ ...newSecret, key: e.target.value })}
        />
        <Input
          placeholder="Value"
          type="password"
          value={newSecret.value}
          onChange={e => setNewSecret({ ...newSecret, value: e.target.value })}
        />
        <Button onClick={createSecret}>Create Secret</Button>
      </div>
    </Section>

    <Section title="Synced Kubernetes Secrets">
      {Object.entries(k8sSecrets).length === 0 ? (
        <p style={{ color: '#8892a6', margin: 0 }}>No secrets synced yet</p>
      ) : (
        Object.entries(k8sSecrets).map(([key, secret]) => (
          <div key={key} style={{
            padding: '12px',
            background: '#0f1419',
            borderRadius: '6px',
            marginBottom: '8px'
          }}>
            <div style={{ fontWeight: '500' }}>{key}</div>
            <div style={{ color: '#8892a6', fontSize: '13px', marginTop: '4px' }}>
              Source: {secret.source} • Version: {secret.version} • Synced: {new Date(secret.synced_at).toLocaleString()}
            </div>
          </div>
        ))
      )}
    </Section>
  </div>
);

const CertificatesTab = ({ certificates, newCert, setNewCert, issueCertificate, renewCertificate, getDaysUntilExpiry, getExpiryColor }) => (
  <div>
    <Section title="Issue New Certificate">
      <div style={{ display: 'grid', gap: '12px', maxWidth: '600px' }}>
        <Input
          placeholder="Domain (e.g., app.example.com)"
          value={newCert.domain}
          onChange={e => setNewCert({ ...newCert, domain: e.target.value })}
        />
        <select
          value={newCert.issuer}
          onChange={e => setNewCert({ ...newCert, issuer: e.target.value })}
          style={{
            padding: '10px',
            background: '#0f1419',
            border: '1px solid #2a3441',
            borderRadius: '6px',
            color: '#e0e6ed',
            fontSize: '14px'
          }}
        >
          <option value="letsencrypt">Let's Encrypt (Public)</option>
          <option value="vault-pki">Vault PKI (Internal)</option>
        </select>
        <Button onClick={issueCertificate}>Issue Certificate</Button>
      </div>
    </Section>

    <Section title="Active Certificates">
      {certificates.length === 0 ? (
        <p style={{ color: '#8892a6', margin: 0 }}>No certificates issued yet</p>
      ) : (
        certificates.map((cert, i) => {
          const days = getDaysUntilExpiry(cert.expires_at);
          return (
            <div key={i} style={{
              padding: '15px',
              background: '#0f1419',
              borderRadius: '6px',
              marginBottom: '10px',
              borderLeft: `3px solid ${getExpiryColor(days)}`
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ fontWeight: '500', fontSize: '15px' }}>{cert.domain}</div>
                  <div style={{ color: '#8892a6', fontSize: '13px', marginTop: '4px' }}>
                    Issuer: {cert.issuer} • Serial: {cert.serial_number}
                  </div>
                  <div style={{ color: getExpiryColor(days), fontSize: '13px', marginTop: '4px' }}>
                    {days > 0 ? `Expires in ${days} days` : `Expired ${Math.abs(days)} days ago`}
                  </div>
                </div>
                {days < 30 && (
                  <button
                    onClick={() => renewCertificate(cert.domain)}
                    style={{
                      padding: '6px 12px',
                      background: '#4a9eff',
                      color: '#fff',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    Renew
                  </button>
                )}
              </div>
            </div>
          );
        })
      )}
    </Section>
  </div>
);

const DynamicTab = ({ leases, newDynamicCred, setNewDynamicCred, generateDynamicCreds, revokeLease }) => (
  <div>
    <Section title="Generate Dynamic Credentials">
      <div style={{ display: 'grid', gap: '12px', maxWidth: '600px' }}>
        <select
          value={newDynamicCred.role}
          onChange={e => setNewDynamicCred({ ...newDynamicCred, role: e.target.value })}
          style={{
            padding: '10px',
            background: '#0f1419',
            border: '1px solid #2a3441',
            borderRadius: '6px',
            color: '#e0e6ed',
            fontSize: '14px'
          }}
        >
          <option value="readonly">Read-Only Database Access</option>
          <option value="readwrite">Read-Write Database Access</option>
          <option value="admin">Admin Database Access</option>
        </select>
        <Input
          placeholder="TTL (hours)"
          type="number"
          value={newDynamicCred.ttl_hours}
          onChange={e => setNewDynamicCred({ ...newDynamicCred, ttl_hours: parseInt(e.target.value) })}
        />
        <Button onClick={generateDynamicCreds}>Generate Credentials</Button>
      </div>
    </Section>

    <Section title="Active Leases">
      {leases.length === 0 ? (
        <p style={{ color: '#8892a6', margin: 0 }}>No active leases</p>
      ) : (
        leases.map((lease, i) => (
          <div key={i} style={{
            padding: '15px',
            background: '#0f1419',
            borderRadius: '6px',
            marginBottom: '10px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: '500', fontSize: '15px', marginBottom: '8px' }}>
                  {lease.role.toUpperCase()} • {lease.credentials.username}
                </div>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '8px',
                  fontSize: '13px',
                  color: '#8892a6'
                }}>
                  <div>Host: {lease.credentials.host}:{lease.credentials.port}</div>
                  <div>Database: {lease.credentials.database}</div>
                  <div>Expires: {new Date(lease.expires_at).toLocaleString()}</div>
                </div>
              </div>
              <button
                onClick={() => revokeLease(lease.lease_id)}
                style={{
                  padding: '6px 12px',
                  background: '#ff4444',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  marginLeft: '12px'
                }}
              >
                Revoke
              </button>
            </div>
          </div>
        ))
      )}
    </Section>
  </div>
);

const AuditTab = ({ auditLogs }) => (
  <Section title="Recent Audit Logs">
    {auditLogs.length === 0 ? (
      <p style={{ color: '#8892a6', margin: 0 }}>No audit logs yet</p>
    ) : (
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #2a3441' }}>
              <th style={{ padding: '10px', textAlign: 'left', color: '#8892a6', fontSize: '13px' }}>Timestamp</th>
              <th style={{ padding: '10px', textAlign: 'left', color: '#8892a6', fontSize: '13px' }}>Operation</th>
              <th style={{ padding: '10px', textAlign: 'left', color: '#8892a6', fontSize: '13px' }}>Path</th>
              <th style={{ padding: '10px', textAlign: 'left', color: '#8892a6', fontSize: '13px' }}>Status</th>
              <th style={{ padding: '10px', textAlign: 'left', color: '#8892a6', fontSize: '13px' }}>Details</th>
            </tr>
          </thead>
          <tbody>
            {auditLogs.slice().reverse().map((log, i) => (
              <tr key={i} style={{ borderBottom: '1px solid #2a3441' }}>
                <td style={{ padding: '10px', fontSize: '13px' }}>
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td style={{ padding: '10px', fontSize: '13px' }}>
                  <span style={{
                    padding: '3px 8px',
                    background: '#0f1419',
                    borderRadius: '3px',
                    fontSize: '12px'
                  }}>
                    {log.operation}
                  </span>
                </td>
                <td style={{ padding: '10px', fontSize: '13px', color: '#8892a6' }}>{log.path}</td>
                <td style={{ padding: '10px', fontSize: '13px' }}>
                  <span style={{
                    padding: '3px 8px',
                    background: log.status === 'success' ? '#00cc6644' : '#ff444444',
                    color: log.status === 'success' ? '#00cc66' : '#ff4444',
                    borderRadius: '3px',
                    fontSize: '12px'
                  }}>
                    {log.status}
                  </span>
                </td>
                <td style={{ padding: '10px', fontSize: '13px', color: '#8892a6' }}>{log.details}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )}
  </Section>
);

const Section = ({ title, children }) => (
  <div style={{ marginBottom: '25px' }}>
    <h3 style={{ margin: '0 0 15px 0', fontSize: '18px', fontWeight: '600' }}>{title}</h3>
    {children}
  </div>
);

const Input = ({ ...props }) => (
  <input
    {...props}
    style={{
      padding: '10px',
      background: '#0f1419',
      border: '1px solid #2a3441',
      borderRadius: '6px',
      color: '#e0e6ed',
      fontSize: '14px',
      outline: 'none'
    }}
  />
);

const Button = ({ onClick, children }) => (
  <button
    onClick={onClick}
    style={{
      padding: '10px 20px',
      background: '#4a9eff',
      color: '#fff',
      border: 'none',
      borderRadius: '6px',
      cursor: 'pointer',
      fontSize: '14px',
      fontWeight: '500',
      transition: 'all 0.2s'
    }}
  >
    {children}
  </button>
);

export default App;
