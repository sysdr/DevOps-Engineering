import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Dashboard = ({ realTimeMetrics }) => {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [summaryRes, trendsRes] = await Promise.all([
        axios.get('http://localhost:8000/api/metrics/summary'),
        axios.get('http://localhost:8000/api/metrics/trends')
      ]);
      
      setSummary(summaryRes.data);
      setTrends(trendsRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">Total Builds</p>
                <p className="text-2xl font-bold text-gray-900">{summary.total_builds}</p>
              </div>
              <div className="ml-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 text-xl">📊</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-gray-900">{summary.success_rate}%</p>
              </div>
              <div className="ml-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 text-xl">✅</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-yellow-500">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">Avg Duration</p>
                <p className="text-2xl font-bold text-gray-900">{summary.avg_duration}s</p>
              </div>
              <div className="ml-4">
                <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <span className="text-yellow-600 text-xl">⏱️</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">Total Cost</p>
                <p className="text-2xl font-bold text-gray-900">${summary.total_cost}</p>
              </div>
              <div className="ml-4">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <span className="text-purple-600 text-xl">💰</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Real-time Active Builds */}
      {Object.keys(realTimeMetrics).length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Active Builds</h3>
          <div className="space-y-4">
            {Object.entries(realTimeMetrics).map(([buildId, metrics]) => (
              <div key={buildId} className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium text-gray-800">Build {buildId}</h4>
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                    Running
                  </span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">CPU:</span>
                    <span className="ml-1 font-semibold">{metrics.cpu_percent?.toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Memory:</span>
                    <span className="ml-1 font-semibold">{metrics.memory_percent?.toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Disk Read:</span>
                    <span className="ml-1 font-semibold">{metrics.disk_read_mb?.toFixed(1)} MB</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Network:</span>
                    <span className="ml-1 font-semibold">{metrics.network_sent_mb?.toFixed(1)} MB</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Performance Trends */}
      {trends && trends.build_times && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Build Performance</h3>
          <div className="space-y-3">
            {trends.build_times.slice(-5).map((build, index) => (
              <div key={build.build_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium text-gray-700">
                  Build {build.build_id.slice(-8)}
                </span>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-600">
                    Duration: {build.duration.toFixed(1)}s
                  </span>
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-indigo-600 h-2 rounded-full"
                      style={{ width: `${Math.min(100, (build.duration / 60) * 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
