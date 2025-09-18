import React, { useState, useEffect } from 'react';
import './App.css';
import SecurityMetrics from './components/SecurityMetrics';
import ImageList from './components/ImageList';
import ActionsPanel from './components/ActionsPanel';

function App() {
  const [metrics, setMetrics] = useState({});
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);

  const refreshData = async () => {
    try {
      const [metricsResponse, imagesResponse] = await Promise.all([
        fetch('http://localhost:8000/api/security-metrics'),
        fetch('http://localhost:8000/api/images')
      ]);
      
      const metricsData = await metricsResponse.json();
      const imagesData = await imagesResponse.json();
      
      setMetrics(metricsData);
      setImages(imagesData.images);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="App">
      <header className="app-header">
        <h1>🔐 Artifact Security Dashboard</h1>
        <p>Day 10: Registry Security & Image Signing</p>
      </header>
      
      <div className="dashboard-container">
        {loading ? (
          <div className="loading">Loading security metrics...</div>
        ) : (
          <>
            <SecurityMetrics metrics={metrics} />
            <div className="main-content">
              <ImageList images={images} onRefresh={refreshData} />
              <ActionsPanel onRefresh={refreshData} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default App;
