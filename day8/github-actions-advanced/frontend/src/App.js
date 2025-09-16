import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const USER_SERVICE_URL = process.env.REACT_APP_USER_SERVICE_URL || 'http://localhost:8001';

function App() {
  const [apiData, setApiData] = useState(null);
  const [users, setUsers] = useState([]);
  const [userStats, setUserStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch API data
      const apiResponse = await axios.get(`${API_URL}/api/data`);
      setApiData(apiResponse.data);

      // Fetch users
      const usersResponse = await axios.get(`${API_URL}/api/users`);
      setUsers(usersResponse.data.users);

      // Fetch user stats
      const statsResponse = await axios.get(`${USER_SERVICE_URL}/stats`);
      setUserStats(statsResponse.data);

    } catch (err) {
      setError('Failed to fetch data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchData();
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <div className="error">
          {error}
          <button onClick={handleRefresh}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🚀 DevOps Dashboard</h1>
        <p>Day 8: GitHub Actions Advanced Patterns</p>
        <button onClick={handleRefresh} className="refresh-btn">
          Refresh Data
        </button>
      </header>

      <main className="app-main">
        <div className="dashboard-grid">
          
          {/* API Service Status */}
          <div className="card">
            <h2>📊 API Service</h2>
            {apiData && (
              <div>
                <p className="status">
                  Status: <span className="success">Active</span>
                  {apiData.cached && <span className="cached">• Cached</span>}
                </p>
                <p>Message: {apiData.message}</p>
                {apiData.data && (
                  <div className="data-preview">
                    <p>Total Items: {apiData.data.total}</p>
                    <div className="items-grid">
                      {apiData.data.items.map(item => (
                        <div key={item.id} className={`item ${item.status}`}>
                          {item.name}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* User Statistics */}
          <div className="card">
            <h2>👥 User Statistics</h2>
            {userStats && (
              <div className="stats-grid">
                <div className="stat">
                  <div className="stat-value">{userStats.total_users}</div>
                  <div className="stat-label">Total Users</div>
                </div>
                <div className="stat">
                  <div className="stat-value success">{userStats.active_users}</div>
                  <div className="stat-label">Active</div>
                </div>
                <div className="stat">
                  <div className="stat-value warning">{userStats.inactive_users}</div>
                  <div className="stat-label">Inactive</div>
                </div>
              </div>
            )}
          </div>

          {/* Users List */}
          <div className="card users-card">
            <h2>📋 User Management</h2>
            <div className="users-list">
              {users.map(user => (
                <div key={user.id} className={`user-item ${!user.active ? 'inactive' : ''}`}>
                  <div className="user-info">
                    <div className="user-name">{user.name}</div>
                    <div className="user-email">{user.email}</div>
                  </div>
                  <div className="user-meta">
                    <span className={`role ${user.role}`}>{user.role}</span>
                    <span className={`status ${user.active ? 'active' : 'inactive'}`}>
                      {user.active ? '✅' : '❌'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* System Health */}
          <div className="card">
            <h2>💚 System Health</h2>
            <div className="health-indicators">
              <div className="health-item">
                <span className="indicator success"></span>
                <span>API Service</span>
              </div>
              <div className="health-item">
                <span className="indicator success"></span>
                <span>User Service</span>
              </div>
              <div className="health-item">
                <span className="indicator success"></span>
                <span>Cache Layer</span>
              </div>
              <div className="health-item">
                <span className="indicator success"></span>
                <span>Frontend</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>🎯 Advanced CI/CD Patterns with Caching, OIDC, and Matrix Builds</p>
      </footer>
    </div>
  );
}

export default App;
