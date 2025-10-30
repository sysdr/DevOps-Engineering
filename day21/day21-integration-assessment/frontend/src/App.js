import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import IntegrationTests from './pages/IntegrationTests';
import LoadTesting from './pages/LoadTesting';
import PerformanceMonitoring from './pages/PerformanceMonitoring';
import CostAnalysis from './pages/CostAnalysis';
import './App.css';

function App() {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="nav-brand">
            <h2>🚀 Phase 1 Assessment Dashboard</h2>
            <span className="timestamp">{currentTime.toLocaleString()}</span>
          </div>
          <div className="nav-links">
            <Link to="/" className="nav-link">Overview</Link>
            <Link to="/integration" className="nav-link">Integration Tests</Link>
            <Link to="/load-testing" className="nav-link">Load Testing</Link>
            <Link to="/monitoring" className="nav-link">Performance</Link>
            <Link to="/cost-analysis" className="nav-link">Cost Analysis</Link>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/integration" element={<IntegrationTests />} />
            <Route path="/load-testing" element={<LoadTesting />} />
            <Route path="/monitoring" element={<PerformanceMonitoring />} />
            <Route path="/cost-analysis" element={<CostAnalysis />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
