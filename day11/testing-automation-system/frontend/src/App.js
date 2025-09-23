import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import TestDashboard from './components/TestDashboard';
import QualityGates from './components/QualityGates';
import PerformanceMetrics from './components/PerformanceMetrics';
import ChaosEngineering from './components/ChaosEngineering';

const AppContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
`;

const Header = styled.header`
  text-align: center;
  color: white;
  margin-bottom: 30px;
  
  h1 {
    font-size: 2.5rem;
    margin-bottom: 10px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
  }
  
  p {
    font-size: 1.1rem;
    opacity: 0.9;
  }
`;

const Dashboard = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
`;

function App() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);
  
  const fetchDashboardData = async () => {
    try {
      const response = await fetch('http://localhost:8000/metrics/dashboard');
      const data = await response.json();
      setDashboardData(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <AppContainer>
        <Header>
          <h1>Loading Testing Automation Dashboard...</h1>
        </Header>
      </AppContainer>
    );
  }
  
  return (
    <AppContainer>
      <Header>
        <h1>🚀 Testing Automation & Quality Gates</h1>
        <p>Day 11: Comprehensive Testing Pipeline Dashboard</p>
      </Header>
      
      <Dashboard>
        <TestDashboard data={dashboardData} onRunTest={runTest} />
        <QualityGates gates={dashboardData?.quality_gates || []} />
        <PerformanceMetrics metrics={dashboardData?.metrics || {}} />
        <ChaosEngineering onInjectChaos={injectChaos} />
      </Dashboard>
    </AppContainer>
  );
  
  async function runTest(testType) {
    try {
      const response = await fetch(`http://localhost:8000/tests/run/${testType}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setTimeout(fetchDashboardData, 2000); // Refresh after 2 seconds
      }
    } catch (error) {
      console.error('Failed to run test:', error);
    }
  }
  
  async function injectChaos(faultType, duration = 30) {
    try {
      const response = await fetch(`http://localhost:8000/chaos/inject/${faultType}?duration=${duration}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setTimeout(fetchDashboardData, 2000);
      }
    } catch (error) {
      console.error('Failed to inject chaos:', error);
    }
  }
}

export default App;
