import React, { useState, useEffect } from 'react';
import './App.css';
import Dashboard from './components/Dashboard';

function App() {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Fetch initial data
    fetch('http://localhost:8000/api/dashboard/overview')
      .then(res => res.json())
      .then(setData)
      .catch(console.error);

    // WebSocket connection for real-time updates with reconnection logic
    let ws = null;
    let reconnectTimeout = null;
    let isMounted = true;
    let isConnecting = false;
    const maxReconnectDelay = 30000; // 30 seconds max
    let reconnectDelay = 1000; // Start with 1 second

    const connect = () => {
      if (!isMounted || isConnecting) return;
      
      // Close existing connection if any
      if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
        try {
          ws.close(1000, 'Reconnecting');
        } catch (e) {
          // Ignore errors when closing
        }
      }

      isConnecting = true;

      try {
        ws = new WebSocket('ws://localhost:8000/ws');
        
        ws.onopen = () => {
          isConnecting = false;
          setConnected(true);
          reconnectDelay = 1000; // Reset delay on successful connection
          console.log('WebSocket connected');
        };
        
        ws.onmessage = (event) => {
          try {
            const update = JSON.parse(event.data);
            setData(update);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };
        
        ws.onerror = (error) => {
          isConnecting = false;
          // Don't log errors for connections that are closing/closed
          if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) {
            console.error('WebSocket error:', error);
          }
          setConnected(false);
        };
        
        ws.onclose = (event) => {
          isConnecting = false;
          setConnected(false);
          
          // Code 1006 is abnormal closure (connection lost without close frame)
          // Code 1000 is normal closure
          if (event.code === 1000) {
            console.log('WebSocket disconnected normally');
          } else {
            console.log(`WebSocket disconnected (code: ${event.code})`);
            
            // Only reconnect if component is still mounted and it wasn't a normal closure
            if (isMounted && event.code !== 1000) {
              // Exponential backoff for reconnection
              reconnectTimeout = setTimeout(() => {
                if (isMounted && !isConnecting) {
                  console.log(`Attempting to reconnect in ${reconnectDelay}ms...`);
                  connect();
                  reconnectDelay = Math.min(reconnectDelay * 2, maxReconnectDelay);
                }
              }, reconnectDelay);
            }
          }
        };
      } catch (error) {
        isConnecting = false;
        console.error('Error creating WebSocket:', error);
        setConnected(false);
        
        // Retry connection after delay
        if (isMounted) {
          reconnectTimeout = setTimeout(() => {
            if (isMounted && !isConnecting) {
              connect();
              reconnectDelay = Math.min(reconnectDelay * 2, maxReconnectDelay);
            }
          }, reconnectDelay);
        }
      }
    };

    // Small delay to ensure backend is ready
    const initialTimeout = setTimeout(() => {
      if (isMounted) {
        connect();
      }
    }, 100);

    return () => {
      isMounted = false;
      isConnecting = false;
      
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      
      if (initialTimeout) {
        clearTimeout(initialTimeout);
      }
      
      if (ws) {
        // Only close if connection is open or connecting
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          try {
            ws.close(1000, 'Component unmounting');
          } catch (e) {
            // Ignore errors when closing
          }
        }
      }
    };
  }, []);

  return (
    <div className="App">
      <Dashboard data={data} connected={connected} />
    </div>
  );
}

export default App;
