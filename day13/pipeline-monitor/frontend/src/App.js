import React, { useState, useEffect } from 'react';
import './App.css';
import Dashboard from './components/Dashboard';
import BuildsList from './components/BuildsList';
import MetricsChart from './components/MetricsChart';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [wsConnection, setWsConnection] = useState(null);
  const [realTimeMetrics, setRealTimeMetrics] = useState({});

  useEffect(() => {
    // WebSocket connection for real-time metrics
    const ws = new WebSocket('ws://localhost:8000/ws/metrics');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setWsConnection(ws);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'metrics_update') {
        setRealTimeMetrics(data.data);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWsConnection(null);
    };

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <nav className="bg-white shadow-lg border-b-2 border-indigo-200">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-indigo-800">
                Pipeline Performance Monitor
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'dashboard'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-indigo-600 hover:bg-indigo-50'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveTab('builds')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'builds'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-indigo-600 hover:bg-indigo-50'
                }`}
              >
                Builds
              </button>
              <button
                onClick={() => setActiveTab('metrics')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'metrics'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-indigo-600 hover:bg-indigo-50'
                }`}
              >
                Metrics
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 px-4">
        <div className="mb-6">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-indigo-100">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-800">
                  Real-time Status
                </h2>
                <p className="text-gray-600">
                  {Object.keys(realTimeMetrics).length} active builds
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${
                  wsConnection ? 'bg-green-400' : 'bg-red-400'
                }`}></div>
                <span className="text-sm text-gray-600">
                  {wsConnection ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {activeTab === 'dashboard' && (
          <Dashboard realTimeMetrics={realTimeMetrics} />
        )}
        {activeTab === 'builds' && <BuildsList />}
        {activeTab === 'metrics' && <MetricsChart />}
      </main>
    </div>
  );
}

export default App;
