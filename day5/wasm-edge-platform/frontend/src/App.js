import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import './App.css';

function App() {
  const [status, setStatus] = useState({});
  const [computeResult, setComputeResult] = useState(null);
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [edgeData, setEdgeData] = useState({});
  const [loading, setLoading] = useState(false);

  // Form state
  const [operation, setOperation] = useState('add');
  const [values, setValues] = useState('1,2,3,4,5');
  const [edgeLocation, setEdgeLocation] = useState('edge-us-west');

  useEffect(() => {
    fetchStatus();
    fetchEdgeData();
    const interval = setInterval(() => {
      fetchStatus();
      fetchEdgeData();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await axios.get('/api/edge/status');
      setStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch status:', error);
    }
  };

  const fetchEdgeData = async () => {
    try {
      const response = await axios.get('/api/edge/data');
      setEdgeData(response.data);
    } catch (error) {
      console.error('Failed to fetch edge data:', error);
    }
  };

  const handleCompute = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/compute', {
        operation,
        values: values.split(',').map(v => parseFloat(v.trim())),
        edge_location: edgeLocation
      });
      setComputeResult(response.data);
    } catch (error) {
      console.error('Computation failed:', error);
    }
    setLoading(false);
  };

  const runBenchmark = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/performance/benchmark');
      setBenchmarkData(response.data.benchmark_results);
    } catch (error) {
      console.error('Benchmark failed:', error);
    }
    setLoading(false);
  };

  const chartData = benchmarkData ? Object.entries(benchmarkData).map(([op, data]) => ({
    operation: op,
    wasm: data.wasm_time_ms,
    python: data.python_time_ms,
    speedup: data.speedup
  })) : [];

  return (
    <div className="App">
      <header className="App-header">
        <h1>🚀 WASM Edge Computing Platform</h1>
        <p>Ultra-low latency edge computing with WebAssembly</p>
      </header>

      <div className="dashboard">
        {/* Status Cards */}
        <div className="status-grid">
          <div className="status-card">
            <h3>Edge Locations</h3>
            <div className="status-value">{status.edge_locations || 0}</div>
          </div>
          <div className="status-card">
            <h3>Pending Syncs</h3>
            <div className="status-value">{status.pending_syncs || 0}</div>
          </div>
          <div className="status-card">
            <h3>Total Computations</h3>
            <div className="status-value">{status.total_computations || 0}</div>
          </div>
          <div className="status-card">
            <h3>WASM Runtime</h3>
            <div className={`status-indicator ${status.wasm_runtime_active ? 'active' : 'inactive'}`}>
              {status.wasm_runtime_active ? 'Active' : 'Fallback'}
            </div>
          </div>
        </div>

        {/* Compute Section */}
        <div className="compute-section">
          <h2>Edge Computation</h2>
          <div className="compute-form">
            <div className="form-group">
              <label>Operation:</label>
              <select value={operation} onChange={(e) => setOperation(e.target.value)}>
                <option value="add">Addition</option>
                <option value="multiply">Multiplication</option>
                <option value="average">Average</option>
              </select>
            </div>
            <div className="form-group">
              <label>Values (comma-separated):</label>
              <input 
                type="text" 
                value={values} 
                onChange={(e) => setValues(e.target.value)}
                placeholder="1,2,3,4,5"
              />
            </div>
            <div className="form-group">
              <label>Edge Location:</label>
              <select value={edgeLocation} onChange={(e) => setEdgeLocation(e.target.value)}>
                <option value="edge-us-west">US West</option>
                <option value="edge-us-east">US East</option>
                <option value="edge-eu-west">EU West</option>
                <option value="edge-asia">Asia Pacific</option>
              </select>
            </div>
            <button onClick={handleCompute} disabled={loading} className="compute-btn">
              {loading ? 'Computing...' : 'Execute on Edge'}
            </button>
          </div>

          {computeResult && (
            <div className="result-card">
              <h3>Computation Result</h3>
              <div className="result-details">
                <p><strong>Result:</strong> {computeResult.result}</p>
                <p><strong>Execution Time:</strong> {computeResult.execution_time_ms}ms</p>
                <p><strong>Runtime:</strong> {computeResult.runtime}</p>
                <p><strong>Edge Location:</strong> {computeResult.edge_location}</p>
              </div>
            </div>
          )}
        </div>

        {/* Benchmark Section */}
        <div className="benchmark-section">
          <h2>Performance Benchmark</h2>
          <button onClick={runBenchmark} disabled={loading} className="benchmark-btn">
            Run WASM vs Python Benchmark
          </button>

          {benchmarkData && (
            <div className="chart-container">
              <h3>Execution Time Comparison (ms)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="operation" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="wasm" fill="#4CAF50" name="WASM" />
                  <Bar dataKey="python" fill="#FF9800" name="Python" />
                </BarChart>
              </ResponsiveContainer>
              
              <h3>Speedup Factor</h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="operation" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="speedup" stroke="#2196F3" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Edge Data */}
        {edgeData.recent_computations && Object.keys(edgeData.recent_computations).length > 0 && (
          <div className="edge-data-section">
            <h2>Recent Edge Computations</h2>
            <div className="computations-grid">
              {Object.entries(edgeData.recent_computations).slice(-6).map(([key, comp]) => (
                <div key={key} className="computation-card">
                  <h4>{comp.operation}</h4>
                  <p><strong>Result:</strong> {comp.result}</p>
                  <p><strong>Location:</strong> {comp.edge_location}</p>
                  <p><strong>Time:</strong> {new Date(comp.timestamp * 1000).toLocaleTimeString()}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
