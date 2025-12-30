import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import JobsPanel from './components/JobsPanel';
import MetricsPanel from './components/MetricsPanel';
import CostPanel from './components/CostPanel';

function App() {
  const [jobs, setJobs] = useState({ queued: [], active: [], completed: [] });
  const [metrics, setMetrics] = useState({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const isMountedRef = useRef(true);
  const connectedRef = useRef(false); // Track connection state in ref

  // Debug: Log when connected state changes
  useEffect(() => {
    console.log('Connected state changed to:', connected);
  }, [connected]);

  useEffect(() => {
    // Fetch initial jobs
    const fetchJobs = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/jobs');
        const data = await res.json();
        console.log('Fetched jobs:', data);
        setJobs(data);
      } catch (err) {
        console.error('Failed to fetch jobs:', err);
      }
    };
    
    fetchJobs();
    
    // Refresh jobs periodically to get queued and completed updates
    const jobsInterval = setInterval(fetchJobs, 5000);

    // WebSocket for real-time metrics
    const connectWebSocket = () => {
      // Clear any existing reconnection timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      // Don't create a new connection if one already exists and is connecting/open
      if (wsRef.current) {
        const state = wsRef.current.readyState;
        if (state === WebSocket.CONNECTING || state === WebSocket.OPEN) {
          console.log('WebSocket already exists, state:', state);
          return;
        }
        // Clean up closed/failed connection
        try {
          wsRef.current.onclose = null;
          wsRef.current.onerror = null;
          wsRef.current.onopen = null;
          wsRef.current.onmessage = null;
        } catch (e) {
          // Ignore
        }
        wsRef.current = null;
      }

      try {
        const wsUrl = 'ws://localhost:8000/ws/metrics';
        console.log('Connecting to WebSocket:', wsUrl);
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;
        
        ws.onopen = (event) => {
          console.log('✓ WebSocket connected successfully!');
          console.log('WebSocket readyState:', ws.readyState);
          // Update ref immediately
          connectedRef.current = true;
          // Force state update
          setConnected(true);
          console.log('setConnected(true) called, current state should be true');
        };
        
        ws.onmessage = (event) => {
          // Ensure we're connected when receiving messages
          if (!connectedRef.current) {
            connectedRef.current = true;
            setConnected(true);
            console.log('Set connected to true on first message');
          }
          
          try {
            const data = JSON.parse(event.data);
            console.log('Received WebSocket data:', data);
            setMetrics(data);
            
            // Update jobs from metrics - merge with existing jobs
            if (data.jobs) {
              setJobs(prev => ({
                ...prev,
                active: data.jobs,
                // Keep queued and completed from initial fetch
                queued: prev.queued || [],
                completed: prev.completed || []
              }));
            }
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          console.error('WebSocket state:', ws.readyState);
        };
        
        ws.onclose = (event) => {
          console.log('WebSocket closed', {
            code: event.code,
            reason: event.reason || 'No reason',
            wasClean: event.wasClean
          });
          
          connectedRef.current = false;
          setConnected(false);
          
          // Clear the ref
          if (wsRef.current === ws) {
            wsRef.current = null;
          }
          
          // Reconnect if not a normal closure (code 1000) or going away (1001)
          if (event.code !== 1000 && event.code !== 1001 && isMountedRef.current) {
            console.log('Will reconnect in 3 seconds...');
            reconnectTimeoutRef.current = setTimeout(() => {
              if (isMountedRef.current) {
                connectWebSocket();
              }
            }, 3000);
          }
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        if (isMountedRef.current) {
          setConnected(false);
          // Retry after 3 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current) {
              connectWebSocket();
            }
          }, 3000);
        }
      }
    };

    // Small delay to ensure component is fully mounted
    const connectTimer = setTimeout(() => {
      connectWebSocket();
    }, 100);

    return () => {
      clearTimeout(connectTimer);
      if (typeof jobsInterval !== 'undefined') {
        clearInterval(jobsInterval);
      }
      isMountedRef.current = false;
      
      // Clear reconnection timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      
      // Close WebSocket
      if (wsRef.current) {
        try {
          // Don't remove handlers - let them fire naturally
          // Just close the connection
          if (wsRef.current.readyState === WebSocket.OPEN || 
              wsRef.current.readyState === WebSocket.CONNECTING) {
            wsRef.current.close(1000, 'Component unmounting');
          }
        } catch (e) {
          // Ignore errors
        }
        wsRef.current = null;
      }
    };
  }, []);

  // Debug render
  console.log('App render - connected state:', connected);

  return (
    <div className="App">
      <header className="header">
        <h1>🚀 TPU Orchestration Platform</h1>
        <div className={`status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '● Connected' : '○ Disconnected'}
        </div>
      </header>

      <div className="dashboard">
        <div className="panel-row">
          <JobsPanel jobs={jobs} />
          <MetricsPanel metrics={metrics} />
        </div>
        <div className="panel-row">
          <CostPanel metrics={metrics} />
        </div>
      </div>
    </div>
  );
}

export default App;
