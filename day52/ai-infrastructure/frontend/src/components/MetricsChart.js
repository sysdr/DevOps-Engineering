import React, { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function MetricsChart({ metrics }) {
  const [chartData, setChartData] = useState([]);
  const [selectedMetric, setSelectedMetric] = useState('cpu_usage_percent');
  const maxDataPoints = 60; // Keep last 60 data points (10 minutes at 10s intervals)
  const chartDataRef = useRef([]);

  useEffect(() => {
    fetchHistory();
    // Refresh history every 30 seconds
    const historyInterval = setInterval(fetchHistory, 30000);
    return () => clearInterval(historyInterval);
  }, [selectedMetric]);

  useEffect(() => {
    // Update chart when real-time metrics arrive
    if (Object.keys(metrics).length > 0) {
      updateChartWithRealTimeData();
    }
  }, [metrics, selectedMetric]);

  const fetchHistory = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/metrics/history/${selectedMetric}?hours=1`);
      const data = await response.json();
      
      // Group by timestamp (round to nearest 10 seconds to handle slight timing differences)
      const groupedByTime = {};
      data.forEach(item => {
        const timestamp = new Date(item.timestamp);
        const timeKey = Math.floor(timestamp.getTime() / 10000) * 10000; // Round to 10 seconds
        if (!groupedByTime[timeKey]) {
          groupedByTime[timeKey] = {
            time: timestamp.toLocaleTimeString(),
            timestamp: timeKey
          };
        }
        groupedByTime[timeKey][item.node] = item.value;
      });

      // Convert to array and sort by timestamp
      const formatted = Object.values(groupedByTime)
        .sort((a, b) => a.timestamp - b.timestamp)
        .slice(-maxDataPoints); // Keep last N points
      
      chartDataRef.current = formatted;
      setChartData(formatted);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  const updateChartWithRealTimeData = () => {
    const now = new Date();
    const newDataPoint = {
      time: now.toLocaleTimeString(),
      timestamp: now.getTime()
    };

    // Get values for all nodes for the selected metric
    Object.entries(metrics).forEach(([node, nodeMetrics]) => {
      if (nodeMetrics[selectedMetric]) {
        newDataPoint[node] = nodeMetrics[selectedMetric].value;
      }
    });

    // Only add if we have at least one value
    if (Object.keys(newDataPoint).length > 1) {
      const updated = [...chartDataRef.current, newDataPoint]
        .slice(-maxDataPoints); // Keep last N points
      
      chartDataRef.current = updated;
      setChartData(updated);
    }
  };

  // Get unique node names from chart data
  const getNodeNames = () => {
    const nodes = new Set();
    chartData.forEach(point => {
      Object.keys(point).forEach(key => {
        if (key !== 'time' && key !== 'timestamp') {
          nodes.add(key);
        }
      });
    });
    return Array.from(nodes).sort();
  };

  const nodeColors = {
    'node-1': '#4CAF50',
    'node-2': '#2196F3',
    'node-3': '#FF9800',
    'node-4': '#9C27B0',
    'node-5': '#F44336'
  };

  const formatValue = (value) => {
    if (selectedMetric === 'network_bytes_sent') {
      return (value / 1024 / 1024).toFixed(2) + ' MB';
    }
    return value.toFixed(2);
  };

  return (
    <div className="metrics-chart">
      <div className="metric-selector">
        <select value={selectedMetric} onChange={(e) => setSelectedMetric(e.target.value)}>
          <option value="cpu_usage_percent">CPU Usage %</option>
          <option value="memory_usage_percent">Memory Usage %</option>
          <option value="network_bytes_sent">Network Sent (bytes)</option>
        </select>
      </div>

      {chartData.length > 0 ? (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#444" />
            <XAxis 
              dataKey="time" 
              stroke="#888"
              interval="preserveStartEnd"
              minTickGap={30}
            />
            <YAxis 
              stroke="#888"
              domain={['auto', 'auto']}
              label={{ value: selectedMetric === 'network_bytes_sent' ? 'Bytes' : '%', angle: -90, position: 'insideLeft', fill: '#888' }}
            />
            <Tooltip 
              contentStyle={{ 
                background: '#2a2a2a', 
                border: '1px solid #667eea',
                borderRadius: '8px',
                color: '#e0e0e0'
              }}
              formatter={(value) => formatValue(value)}
            />
            <Legend 
              wrapperStyle={{ paddingTop: '10px' }}
              iconType="line"
            />
            {getNodeNames().map((node, index) => (
              <Line
                key={node}
                type="monotone"
                dataKey={node}
                stroke={nodeColors[node] || `hsl(${index * 60}, 70%, 50%)`}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
                name={node}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="no-data" style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div>Loading metrics data...</div>
        </div>
      )}

      {Object.keys(metrics).length > 0 && (
        <div className="current-values">
          <h4>Current Values:</h4>
          {Object.entries(metrics)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([node, data]) => {
              const value = data[selectedMetric]?.value;
              return value !== undefined ? (
                <div key={node} className="node-metric">
                  <span className="node-name">{node}:</span>
                  <span className="metric-value">
                    {formatValue(value)}
                  </span>
                </div>
              ) : null;
            })}
        </div>
      )}
    </div>
  );
}

export default MetricsChart;
