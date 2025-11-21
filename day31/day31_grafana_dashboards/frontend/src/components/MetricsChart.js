import React, { useState, useEffect, useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const DEMO_POINTS = 12;

const createDemoSeries = () => {
  const timestamps = [];
  const premiumSeries = [];
  const registrationSeries = [];
  const now = Date.now();

  for (let i = DEMO_POINTS - 1; i >= 0; i -= 1) {
    const ts = new Date(now - i * 60000);
    timestamps.push(ts.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    const premium = 250 + Math.sin((DEMO_POINTS - i) / 2) * 35 + Math.random() * 15;
    const registrations = 900 + (DEMO_POINTS - i) * 25 + Math.random() * 25;
    premiumSeries.push(Math.round(premium));
    registrationSeries.push(Math.round(registrations));
  }

  const totals = {
    totalActiveUsers: Math.round(premiumSeries[premiumSeries.length - 1] + 1850),
    premiumActiveUsers: premiumSeries[premiumSeries.length - 1],
    totalRegistrations: Math.round(registrationSeries[registrationSeries.length - 1] + 3100),
    organicRegistrations: registrationSeries[registrationSeries.length - 1]
  };

  return {
    timestamps,
    activeUsers: premiumSeries,
    registrations: registrationSeries,
    totals
  };
};

const alignSeries = (series, targetLength, filler = 0) => {
  if (!targetLength) return [];
  if (!series.length) {
    return Array(targetLength).fill(filler);
  }
  if (series.length === targetLength) {
    return series;
  }
  if (series.length > targetLength) {
    return series.slice(series.length - targetLength);
  }
  const padValue = filler ?? series[0] ?? 0;
  const padding = Array(targetLength - series.length).fill(padValue);
  return [...padding, ...series];
};

function MetricsChart() {
  const demoSeries = useMemo(() => createDemoSeries(), []);
  const [metrics, setMetrics] = useState({
    activeUsers: [],
    registrations: [],
    timestamps: [],
    totalActiveUsers: 0,
    totalRegistrations: 0,
    premiumActiveUsers: 0,
    organicRegistrations: 0
  });
  const [hasLiveData, setHasLiveData] = useState(false);

  const maxDataPoints = 20;

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 2000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8000/metrics');
      const text = await response.text();
      
      const activeMatches = [...text.matchAll(/business_active_users{tier="([^"]+)"}\s+([\d.]+)/g)];
      const registrationMatches = [...text.matchAll(/business_user_registrations_total{source="([^"]+)"}\s+([\d.]+)/g)];

      const premiumActive = activeMatches.find(match => match[1] === 'premium');
      const totalActiveUsers = activeMatches.reduce((sum, match) => sum + parseFloat(match[2] || 0), 0);

      const organicRegistrations = registrationMatches.find(match => match[1] === 'organic');
      const totalRegistrations = registrationMatches.reduce((sum, match) => sum + parseFloat(match[2] || 0), 0);
      
      const timestamp = new Date().toLocaleTimeString();
      
      setMetrics(prev => {
        const premiumValue = premiumActive ? parseFloat(premiumActive[2]) : prev.premiumActiveUsers;
        const organicValue = organicRegistrations ? parseFloat(organicRegistrations[2]) : prev.organicRegistrations;
        const newData = {
          activeUsers: [...prev.activeUsers, premiumValue].slice(-maxDataPoints),
          registrations: [...prev.registrations, organicValue].slice(-maxDataPoints),
          timestamps: [...prev.timestamps, timestamp].slice(-maxDataPoints),
          totalActiveUsers,
          totalRegistrations,
          premiumActiveUsers: premiumValue,
          organicRegistrations: organicValue
        };
        return newData;
      });

      if (!hasLiveData && activeMatches.length) {
        setHasLiveData(true);
      }
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const labels = metrics.timestamps.length ? metrics.timestamps : demoSeries.timestamps;

  const liveActiveData = metrics.activeUsers.length
    ? alignSeries(metrics.activeUsers, labels.length, null)
    : Array(labels.length).fill(null);
  const liveRegistrationData = metrics.registrations.length
    ? alignSeries(metrics.registrations, labels.length, null)
    : Array(labels.length).fill(null);

  const demoActiveData = alignSeries(demoSeries.activeUsers, labels.length, demoSeries.activeUsers[0]);
  const demoRegistrationData = alignSeries(demoSeries.registrations, labels.length, demoSeries.registrations[0]);

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Active Premium Users (Live)',
        data: liveActiveData,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.4,
        spanGaps: true
      },
      {
        label: 'Total Registrations (Live)',
        data: liveRegistrationData,
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.4,
        spanGaps: true
      },
      {
        label: 'Active Premium Users (Demo)',
        data: demoActiveData,
        borderColor: 'rgba(102, 126, 234, 0.7)',
        backgroundColor: 'rgba(102, 126, 234, 0.08)',
        tension: 0.4,
        borderDash: [8, 6],
        pointRadius: 0,
        borderWidth: 1.5
      },
      {
        label: 'Total Registrations (Demo)',
        data: demoRegistrationData,
        borderColor: 'rgba(255, 206, 86, 0.7)',
        backgroundColor: 'rgba(255, 206, 86, 0.1)',
        tension: 0.4,
        borderDash: [8, 6],
        pointRadius: 0,
        borderWidth: 1.5
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
      title: { display: true, text: 'Live Business Metrics' }
    },
    scales: {
      y: { beginAtZero: true }
    },
    animation: { duration: 500 }
  };

  const formatNumber = (value) => Number(value || 0).toLocaleString();
  const totals = {
    totalActiveUsers: hasLiveData ? metrics.totalActiveUsers : demoSeries.totals.totalActiveUsers,
    premiumActiveUsers: hasLiveData ? metrics.premiumActiveUsers : demoSeries.totals.premiumActiveUsers,
    totalRegistrations: hasLiveData ? metrics.totalRegistrations : demoSeries.totals.totalRegistrations,
    organicRegistrations: hasLiveData ? metrics.organicRegistrations : demoSeries.totals.organicRegistrations
  };

  return (
    <div className="metrics-chart">
      <div style={{ height: '400px' }}>
        <Line data={chartData} options={options} />
      </div>
      {!hasLiveData && (
        <p className="metrics-demo-note">
          Showing baseline demo data until live metrics connect...
        </p>
      )}
      <div className="metrics-summary">
        <div className="metric-card metric-card--highlight">
          <h4>Live Active Users</h4>
          <p className="metric-value">
            {formatNumber(totals.totalActiveUsers)}
          </p>
          <span className="metric-subtitle">All tiers combined</span>
        </div>
        <div className="metric-card">
          <h4>Premium Active Users</h4>
          <p className="metric-value">
            {formatNumber(totals.premiumActiveUsers)}
          </p>
          <span className="metric-subtitle">Real-time premium load</span>
        </div>
        <div className="metric-card metric-card--highlight">
          <h4>Total Registrations</h4>
          <p className="metric-value">
            {formatNumber(totals.totalRegistrations)}
          </p>
          <span className="metric-subtitle">Across all acquisition sources</span>
        </div>
        <div className="metric-card">
          <h4>Organic Registrations</h4>
          <p className="metric-value">
            {formatNumber(totals.organicRegistrations)}
          </p>
          <span className="metric-subtitle">Latest organic total</span>
        </div>
      </div>
    </div>
  );
}

export default MetricsChart;
