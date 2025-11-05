import React, { useState, useEffect } from 'react';
import './SealedSecretsInfo.css';

function SealedSecretsInfo() {
  const [certData, setCertData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCertificate();
  }, []);

  const fetchCertificate = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/sealed-secrets-cert');
      const data = await response.json();
      setCertData(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch certificate:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading sealed secrets info...</div>;
  }

  if (!certData) {
    return <div className="error">Failed to load certificate data</div>;
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(certData.certificate);
    alert('Certificate copied to clipboard!');
  };

  return (
    <div className="sealed-secrets-info">
      <div className="section-header">
        <h2>Sealed Secrets Controller</h2>
        <span className="controller-status">🟢 Running</span>
      </div>

      <div className="info-cards">
        <div className="info-card">
          <h3>🔑 What is Sealed Secrets?</h3>
          <p>
            Sealed Secrets allows you to encrypt Kubernetes Secrets so they can be safely 
            stored in Git repositories. Only the cluster's Sealed Secrets controller can decrypt them.
          </p>
        </div>

        <div className="info-card">
          <h3>🔒 How It Works</h3>
          <ol>
            <li>Fetch the public certificate from the cluster</li>
            <li>Use kubeseal CLI to encrypt your secrets</li>
            <li>Commit the encrypted SealedSecret to Git</li>
            <li>Controller automatically decrypts when applied to cluster</li>
          </ol>
        </div>

        <div className="info-card">
          <h3>✅ Benefits</h3>
          <ul>
            <li>Store secrets in Git safely</li>
            <li>Full GitOps workflow for secrets</li>
            <li>Audit trail through Git history</li>
            <li>No external dependencies</li>
          </ul>
        </div>
      </div>

      <div className="cert-section">
        <div className="cert-header">
          <h3>Public Certificate</h3>
          <button onClick={copyToClipboard} className="copy-button">
            📋 Copy Certificate
          </button>
        </div>
        <div className="cert-details">
          <div className="cert-info">
            <span className="cert-label">Algorithm:</span>
            <span className="cert-value">{certData.algorithm}</span>
          </div>
          <div className="cert-info">
            <span className="cert-label">Usage:</span>
            <span className="cert-value">{certData.usage}</span>
          </div>
        </div>
        <pre className="cert-content">
          {certData.certificate}
        </pre>
      </div>

      <div className="usage-guide">
        <h3>📖 Usage Guide</h3>
        <div className="code-block">
          <div className="code-header">1. Install kubeseal CLI</div>
          <code>wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/kubeseal</code>
        </div>
        
        <div className="code-block">
          <div className="code-header">2. Create a standard Kubernetes Secret</div>
          <code>kubectl create secret generic my-secret --from-literal=password=mysecret --dry-run=client -o yaml {'>'} secret.yaml</code>
        </div>
        
        <div className="code-block">
          <div className="code-header">3. Seal the secret</div>
          <code>kubeseal --cert=pub-cert.pem {'<'} secret.yaml {'>'} sealed-secret.yaml</code>
        </div>
        
        <div className="code-block">
          <div className="code-header">4. Commit to Git and apply</div>
          <code>git add sealed-secret.yaml && git commit -m "Add sealed secret"</code>
        </div>
      </div>
    </div>
  );
}

export default SealedSecretsInfo;
