import React, { useState } from 'react';

function DocGenerator() {
  const [code, setCode] = useState('');
  const [docs, setDocs] = useState(null);
  const [loading, setLoading] = useState(false);
  const [demoLoaded, setDemoLoaded] = useState(false);

  const sampleCode = `"""
User Management Module

This module provides comprehensive user management functionality
including authentication, authorization, and profile management.
"""

class UserManager:
    """
    Manages user operations including creation, authentication, and profile updates.
    
    This class handles all user-related operations and maintains
    user state throughout the application lifecycle.
    """
    
    def __init__(self, database):
        """
        Initialize the UserManager.
        
        Args:
            database: Database connection instance
        """
        self.db = database
        self.cache = {}
    
    def create_user(self, username: str, email: str, password: str) -> dict:
        """
        Create a new user account.
        
        Args:
            username: Unique username for the account
            email: User's email address
            password: Password (will be hashed)
        
        Returns:
            Dictionary containing user information and success status
        """
        # Implementation here
        return {"id": "123", "username": username}
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate user credentials.
        
        Args:
            username: Username to authenticate
            password: Password to verify
        
        Returns:
            True if authentication successful, False otherwise
        """
        # Authentication logic
        return True

def send_notification(user_id: str, message: str, channel: str = "email") -> bool:
    """
    Send notification to user via specified channel.
    
    Args:
        user_id: Target user identifier
        message: Notification message content
        channel: Communication channel (email, sms, push)
    
    Returns:
        True if notification sent successfully
    """
    # Send notification
    return True

# Configuration constants
MAX_LOGIN_ATTEMPTS = 5
SESSION_TIMEOUT = 3600
ALLOWED_DOMAINS = ["example.com", "example.org"]
`;

  // Auto-load demo data on mount
  React.useEffect(() => {
    if (!demoLoaded) {
      setCode(sampleCode);
      setDemoLoaded(true);
      // Auto-generate docs after a short delay
      setTimeout(() => {
        generateDocs();
      }, 500);
    }
  }, []);

  const generateDocs = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8004/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: 'sample.py',
          content: code,
          language: 'python'
        })
      });
      const data = await response.json();
      setDocs(data);
    } catch (error) {
      console.error('Documentation generation failed:', error);
      alert('Failed to generate docs. Make sure the service is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <h2>📚 Automated Documentation Generator</h2>
      <p style={{ color: '#718096', marginBottom: '1rem' }}>
        AI-powered documentation from your source code
      </p>

      <button
        onClick={() => setCode(sampleCode)}
        style={{
          background: '#e2e8f0',
          color: '#2d3748',
          border: 'none',
          padding: '0.5rem 1rem',
          borderRadius: '6px',
          cursor: 'pointer',
          marginBottom: '1rem'
        }}
      >
        Load Sample Code
      </button>

      <textarea
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="Paste your Python code here..."
      />

      <button
        className="primary"
        onClick={generateDocs}
        disabled={!code || loading}
      >
        {loading ? 'Generating...' : 'Generate Documentation'}
      </button>

      {docs && (
        <div className="results">
          <h2 style={{ marginBottom: '1rem' }}>{docs.title}</h2>
          <p style={{
            color: '#4a5568',
            padding: '1rem',
            background: '#edf2f7',
            borderRadius: '6px',
            marginBottom: '1.5rem'
          }}>
            {docs.description}
          </p>

          {docs.sections.map((section, idx) => (
            <div key={idx} className="doc-section">
              <h3>{section.title}</h3>
              {section.items && section.items.map((item, itemIdx) => (
                <div key={itemIdx} className="doc-item">
                  {item.name && (
                    <>
                      <div className="doc-item-name">{item.name}</div>
                      {item.description && (
                        <p style={{ color: '#4a5568', margin: '0.5rem 0' }}>
                          {item.description}
                        </p>
                      )}
                      {item.parameters && item.parameters.length > 0 && (
                        <div style={{ marginTop: '0.75rem' }}>
                          <strong style={{ fontSize: '0.9rem' }}>Parameters:</strong>
                          <ul style={{ marginLeft: '1.5rem', marginTop: '0.25rem' }}>
                            {item.parameters.map((param, pIdx) => (
                              <li key={pIdx} style={{ color: '#4a5568', marginTop: '0.25rem' }}>
                                <code style={{
                                  background: '#edf2f7',
                                  padding: '0.1rem 0.4rem',
                                  borderRadius: '3px'
                                }}>
                                  {param.name}
                                </code>
                                {param.type && <span> : {param.type}</span>}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {item.returns && (
                        <p style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>
                          <strong>Returns:</strong> {item.returns}
                        </p>
                      )}
                      {item.methods && (
                        <p style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>
                          <strong>Methods:</strong> {item.methods.join(', ')}
                        </p>
                      )}
                      {item.line && (
                        <p style={{ color: '#718096', fontSize: '0.8rem', marginTop: '0.5rem' }}>
                          Line {item.line}
                        </p>
                      )}
                    </>
                  )}
                  {item.value !== undefined && (
                    <div>
                      <strong>{item.name}</strong> = {item.value}
                    </div>
                  )}
                  {item.error && (
                    <div style={{ color: '#fc8181' }}>
                      ⚠️ {item.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))}

          <div style={{
            marginTop: '2rem',
            padding: '1rem',
            background: '#edf2f7',
            borderRadius: '6px',
            fontSize: '0.85rem',
            color: '#718096'
          }}>
            Generated at: {new Date(docs.generated_at).toLocaleString()}
          </div>
        </div>
      )}
    </div>
  );
}

export default DocGenerator;
