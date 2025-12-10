import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE = 'http://localhost';

function App() {
  const [activeTab, setActiveTab] = useState('auth');
  const [authToken, setAuthToken] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  
  // Authentication state
  const [username, setUsername] = useState('alice@company.com');
  const [password, setPassword] = useState('alice123');
  const [authEvents, setAuthEvents] = useState([]);
  
  // Policy state
  const [policyEvents, setPolicyEvents] = useState([]);
  const [testResource, setTestResource] = useState('api/data/dev');
  const [testAction, setTestAction] = useState('GET');
  const [testNamespace, setTestNamespace] = useState('dev');
  
  // Resource access state
  const [accessLogs, setAccessLogs] = useState([]);
  const [resourceNamespace, setResourceNamespace] = useState('dev');
  const [resourceData, setResourceData] = useState(null);
  
  // Certificate state
  const [certificates, setCertificates] = useState([]);
  const [certEvents, setCertEvents] = useState([]);
  
  // Network policy state
  const [networkTests, setNetworkTests] = useState([]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (activeTab === 'auth') fetchAuthEvents();
      if (activeTab === 'policy') fetchPolicyEvents();
      if (activeTab === 'resources') fetchAccessLogs();
      if (activeTab === 'certs') fetchCertificates();
    }, 3000);
    return () => clearInterval(interval);
  }, [activeTab]);

  const fetchAuthEvents = async () => {
    try {
      const response = await fetch(`${API_BASE}:8001/auth/events`);
      const data = await response.json();
      setAuthEvents(data.events || []);
    } catch (error) {
      console.error('Failed to fetch auth events:', error);
    }
  };

  const fetchPolicyEvents = async () => {
    try {
      const response = await fetch(`${API_BASE}:8003/policy/events`);
      const data = await response.json();
      setPolicyEvents(data.events || []);
    } catch (error) {
      console.error('Failed to fetch policy events:', error);
    }
  };

  const fetchAccessLogs = async () => {
    try {
      const response = await fetch(`${API_BASE}:8002/api/access-logs`);
      const data = await response.json();
      setAccessLogs(data.logs || []);
    } catch (error) {
      console.error('Failed to fetch access logs:', error);
    }
  };

  const fetchCertificates = async () => {
    try {
      const [certResponse, eventResponse] = await Promise.all([
        fetch(`${API_BASE}:8004/certs/list`),
        fetch(`${API_BASE}:8004/certs/events`)
      ]);
      const certData = await certResponse.json();
      const eventData = await eventResponse.json();
      setCertificates(certData.certificates || []);
      setCertEvents(eventData.events || []);
    } catch (error) {
      console.error('Failed to fetch certificates:', error);
    }
  };

  const handleLogin = async () => {
    try {
      const response = await fetch(`${API_BASE}:8001/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      if (response.ok) {
        const data = await response.json();
        setAuthToken(data.access_token);
        setCurrentUser(data.user_info);
        alert('Login successful!');
        fetchAuthEvents();
      } else {
        alert('Login failed!');
      }
    } catch (error) {
      alert('Login error: ' + error.message);
    }
  };

  const handleLogout = () => {
    setAuthToken(null);
    setCurrentUser(null);
  };

  const testPolicyEvaluation = async () => {
    if (!currentUser) {
      alert('Please login first');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}:8003/policy/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user: currentUser,
          resource: testResource,
          action: testAction,
          namespace: testNamespace
        })
      });
      
      const data = await response.json();
      alert(`Policy Decision: ${data.allowed ? 'ALLOWED' : 'DENIED'}\nReason: ${data.reason}`);
      fetchPolicyEvents();
    } catch (error) {
      alert('Policy evaluation error: ' + error.message);
    }
  };

  const accessResource = async () => {
    if (!authToken) {
      alert('Please login first');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}:8002/api/data/${resourceNamespace}`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setResourceData(data);
        alert('Resource accessed successfully!');
      } else {
        const error = await response.json();
        alert(`Access denied: ${error.detail}`);
      }
      fetchAccessLogs();
    } catch (error) {
      alert('Resource access error: ' + error.message);
    }
  };

  const testNetworkPolicy = async (from, to, port) => {
    try {
      const response = await fetch(`${API_BASE}:8003/policy/network/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from_service: from, to_service: to, port })
      });
      
      const data = await response.json();
      setNetworkTests(prev => [...prev, {
        from, to, port,
        allowed: data.allowed,
        reason: data.reason,
        timestamp: new Date().toISOString()
      }]);
    } catch (error) {
      console.error('Network policy test error:', error);
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🔒 Zero-Trust Security Dashboard</h1>
        <p>Real-time monitoring of identity, policy, and certificate management</p>
      </header>

      <nav className="nav-tabs">
        <button 
          className={activeTab === 'auth' ? 'active' : ''} 
          onClick={() => setActiveTab('auth')}
        >
          Authentication
        </button>
        <button 
          className={activeTab === 'policy' ? 'active' : ''} 
          onClick={() => setActiveTab('policy')}
        >
          Policy Engine
        </button>
        <button 
          className={activeTab === 'resources' ? 'active' : ''} 
          onClick={() => setActiveTab('resources')}
        >
          Resource Access
        </button>
        <button 
          className={activeTab === 'certs' ? 'active' : ''} 
          onClick={() => setActiveTab('certs')}
        >
          Certificates
        </button>
        <button 
          className={activeTab === 'network' ? 'active' : ''} 
          onClick={() => setActiveTab('network')}
        >
          Network Policies
        </button>
      </nav>

      <div className="content">
        {/* Authentication Tab */}
        {activeTab === 'auth' && (
          <div className="tab-content">
            <div className="card">
              <h2>Identity & Authentication (OIDC)</h2>
              
              {!currentUser ? (
                <div className="login-form">
                  <select 
                    value={username} 
                    onChange={(e) => setUsername(e.target.value)}
                    className="input-field"
                  >
                    <option value="alice@company.com">Alice (Developer)</option>
                    <option value="bob@company.com">Bob (Operator)</option>
                    <option value="eve@company.com">Eve (Viewer)</option>
                  </select>
                  <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input-field"
                  />
                  <button onClick={handleLogin} className="btn-primary">
                    Login with OIDC
                  </button>
                  <p className="hint">Passwords: alice123, bob123, eve123</p>
                </div>
              ) : (
                <div className="user-info">
                  <div className="status-badge success">Authenticated</div>
                  <p><strong>User:</strong> {currentUser.full_name}</p>
                  <p><strong>Email:</strong> {currentUser.username}</p>
                  <p><strong>Groups:</strong> {currentUser.groups.join(', ')}</p>
                  <p><strong>Roles:</strong> {currentUser.roles.join(', ')}</p>
                  <button onClick={handleLogout} className="btn-secondary">Logout</button>
                </div>
              )}
            </div>

            <div className="card">
              <h2>Authentication Events (Real-time)</h2>
              <div className="events-list">
                {authEvents.slice(-10).reverse().map((event, idx) => (
                  <div 
                    key={idx} 
                    className={`event-item ${event.success ? 'success' : 'failure'}`}
                  >
                    <div className="event-time">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </div>
                    <div className="event-details">
                      <strong>{event.event_type}</strong>
                      <span>{event.username}</span>
                      <span className={`status ${event.success ? 'success' : 'failure'}`}>
                        {event.success ? '✓ Success' : '✗ Failed'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Policy Engine Tab */}
        {activeTab === 'policy' && (
          <div className="tab-content">
            <div className="card">
              <h2>Policy Evaluation (OPA)</h2>
              {currentUser ? (
                <div className="policy-test">
                  <p><strong>Testing as:</strong> {currentUser.username}</p>
                  <input
                    type="text"
                    placeholder="Resource (e.g., api/data/dev)"
                    value={testResource}
                    onChange={(e) => setTestResource(e.target.value)}
                    className="input-field"
                  />
                  <select 
                    value={testAction} 
                    onChange={(e) => setTestAction(e.target.value)}
                    className="input-field"
                  >
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="DELETE">DELETE</option>
                  </select>
                  <select 
                    value={testNamespace} 
                    onChange={(e) => setTestNamespace(e.target.value)}
                    className="input-field"
                  >
                    <option value="dev">dev</option>
                    <option value="prod">prod</option>
                  </select>
                  <button onClick={testPolicyEvaluation} className="btn-primary">
                    Evaluate Policy
                  </button>
                </div>
              ) : (
                <p className="warning">Please login to test policy evaluation</p>
              )}
            </div>

            <div className="card">
              <h2>Policy Decisions (Real-time)</h2>
              <div className="events-list">
                {policyEvents.slice(-10).reverse().map((event, idx) => (
                  <div 
                    key={idx} 
                    className={`event-item ${event.allowed ? 'success' : 'failure'}`}
                  >
                    <div className="event-time">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </div>
                    <div className="event-details">
                      <strong>{event.user}</strong>
                      <span>{event.action} {event.resource}</span>
                      <span className={`status ${event.allowed ? 'success' : 'failure'}`}>
                        {event.allowed ? '✓ Allowed' : '✗ Denied'}
                      </span>
                      <small>{event.reason}</small>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Resource Access Tab */}
        {activeTab === 'resources' && (
          <div className="tab-content">
            <div className="card">
              <h2>Protected Resource Access</h2>
              {authToken ? (
                <div className="resource-access">
                  <p><strong>Accessing as:</strong> {currentUser.username}</p>
                  <select 
                    value={resourceNamespace} 
                    onChange={(e) => setResourceNamespace(e.target.value)}
                    className="input-field"
                  >
                    <option value="dev">Development Namespace</option>
                    <option value="prod">Production Namespace</option>
                  </select>
                  <button onClick={accessResource} className="btn-primary">
                    Access Resource
                  </button>
                  
                  {resourceData && (
                    <div className="resource-data">
                      <h3>Retrieved Data:</h3>
                      <pre>{JSON.stringify(resourceData, null, 2)}</pre>
                    </div>
                  )}
                </div>
              ) : (
                <p className="warning">Please login to access resources</p>
              )}
            </div>

            <div className="card">
              <h2>Access Logs (Audit Trail)</h2>
              <div className="events-list">
                {accessLogs.slice(-10).reverse().map((log, idx) => (
                  <div 
                    key={idx} 
                    className={`event-item ${log.allowed ? 'success' : 'failure'}`}
                  >
                    <div className="event-time">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </div>
                    <div className="event-details">
                      <strong>{log.user}</strong>
                      <span>{log.action} {log.resource}</span>
                      <span>Namespace: {log.namespace}</span>
                      <span className={`status ${log.allowed ? 'success' : 'failure'}`}>
                        {log.allowed ? '✓ Allowed' : '✗ Denied'}
                      </span>
                      {log.reason && <small>{log.reason}</small>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Certificates Tab */}
        {activeTab === 'certs' && (
          <div className="tab-content">
            <div className="card">
              <h2>Certificate Management (cert-manager)</h2>
              <div className="cert-grid">
                {certificates.map((cert, idx) => {
                  const expiryHours = cert.time_until_expiry_seconds / 3600;
                  const isExpiring = expiryHours < 6;
                  
                  return (
                    <div key={idx} className={`cert-card ${isExpiring ? 'expiring' : ''}`}>
                      <h3>{cert.cert_id}</h3>
                      <div className="cert-status">
                        <span className={`status-badge ${cert.status.toLowerCase()}`}>
                          {cert.status}
                        </span>
                      </div>
                      <div className="cert-details">
                        <p><strong>Issued:</strong> {new Date(cert.issued_at).toLocaleString()}</p>
                        <p><strong>Expires:</strong> {new Date(cert.expires_at).toLocaleString()}</p>
                        <p><strong>Time Left:</strong> {expiryHours.toFixed(1)} hours</p>
                        <div className="progress-bar">
                          <div 
                            className="progress-fill" 
                            style={{width: `${cert.percentage_elapsed}%`}}
                          ></div>
                        </div>
                        <p className="progress-text">{cert.percentage_elapsed}% elapsed</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="card">
              <h2>Certificate Events</h2>
              <div className="events-list">
                {certEvents.slice(-10).reverse().map((event, idx) => (
                  <div key={idx} className="event-item">
                    <div className="event-time">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </div>
                    <div className="event-details">
                      <strong>{event.event}</strong>
                      {event.service && <span>Service: {event.service}</span>}
                      {event.subject && <span>{event.subject}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Network Policies Tab */}
        {activeTab === 'network' && (
          <div className="tab-content">
            <div className="card">
              <h2>Network Policy Testing</h2>
              <p>Test micro-segmentation rules between services</p>
              <div className="network-tests">
                <button 
                  onClick={() => testNetworkPolicy('frontend', 'api-gateway', 8080)}
                  className="btn-primary"
                >
                  Test: frontend → api-gateway:8080
                </button>
                <button 
                  onClick={() => testNetworkPolicy('api-gateway', 'auth-service', 8001)}
                  className="btn-primary"
                >
                  Test: api-gateway → auth-service:8001
                </button>
                <button 
                  onClick={() => testNetworkPolicy('frontend', 'database', 5432)}
                  className="btn-primary"
                >
                  Test: frontend → database:5432 (Should Deny)
                </button>
                <button 
                  onClick={() => testNetworkPolicy('resource-service', 'database', 5432)}
                  className="btn-primary"
                >
                  Test: resource-service → database:5432
                </button>
              </div>
            </div>

            <div className="card">
              <h2>Network Policy Results</h2>
              <div className="events-list">
                {networkTests.slice(-10).reverse().map((test, idx) => (
                  <div 
                    key={idx} 
                    className={`event-item ${test.allowed ? 'success' : 'failure'}`}
                  >
                    <div className="event-time">
                      {new Date(test.timestamp).toLocaleTimeString()}
                    </div>
                    <div className="event-details">
                      <strong>{test.from} → {test.to}:{test.port}</strong>
                      <span className={`status ${test.allowed ? 'success' : 'failure'}`}>
                        {test.allowed ? '✓ Allowed' : '✗ Blocked'}
                      </span>
                      <small>{test.reason}</small>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
