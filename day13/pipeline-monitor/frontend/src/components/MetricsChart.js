import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const MetricsChart = () => {
  const [chartData, setChartData] = useState(null);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    fetchMetricsData();
    const interval = setInterval(fetchMetricsData, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchMetricsData = async () => {
    try {
      const [trendsRes, summaryRes] = await Promise.all([
        axios.get('http://localhost:8000/api/metrics/trends'),
        axios.get('http://localhost:8000/api/metrics/summary')
      ]);

      if (trendsRes.data.build_times) {
        const buildTimes = trendsRes.data.build_times.slice(-10);
        
        setChartData({
          labels: buildTimes.map(b => `Build ${b.build_id.slice(-6)}`),
          datasets: [
            {
              label: 'Build Duration (seconds)',
              data: buildTimes.map(b => b.duration),
              borderColor: 'rgb(99, 102, 241)',
              backgroundColor: 'rgba(99, 102, 241, 0.1)',
              borderWidth: 2,
              fill: true,
              tension: 0.4,
            },
          ],
        });
      }

      setSummary(summaryRes.data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Build Performance Trends',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Duration (seconds)',
        },
      },
    },
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Performance Analytics</h2>
      
      {/* Performance Insights */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Performance Insights</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Fastest Build:</span>
                <span className="font-semibold">{summary.min_duration}s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Slowest Build:</span>
                <span className="font-semibold">{summary.max_duration}s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Average Cost:</span>
                <span className="font-semibold">${summary.avg_cost_per_build}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Builds Today:</span>
                <span className="font-semibold">{summary.builds_last_24h}</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Optimization Recommendations</h3>
            <div className="space-y-2">
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  💡 Consider implementing dependency caching to reduce build times
                </p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-sm text-green-800">
                  ✅ Good success rate - maintain current quality practices
                </p>
              </div>
              <div className="p-3 bg-yellow-50 rounded-lg">
                <p className="text-sm text-yellow-800">
                  ⚡ Monitor resource usage during peak hours for optimization
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chart */}
      {chartData && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <Line data={chartData} options={chartOptions} />
        </div>
      )}
    </div>
  );
};

export default MetricsChart;
