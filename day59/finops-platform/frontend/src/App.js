import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import CostBreakdown from './components/CostBreakdown';
import Recommendations from './components/Recommendations';
import Alerts from './components/Alerts';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [costData, setCostData] = useState(null);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    let websocket = null;
    let reconnectTimeout = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const reconnectDelay = 3000; // 3 seconds
    let isComponentMounted = true;

    const connectWebSocket = () => {
      // Don't reconnect if component is unmounted
      if (!isComponentMounted) {
        return;
      }

      try {
        // Close and cleanup existing connection if any
        if (websocket) {
          const state = websocket.readyState;
          if (state === WebSocket.OPEN || state === WebSocket.CONNECTING) {
            websocket.onopen = null;
            websocket.onmessage = null;
            websocket.onerror = null;
            websocket.onclose = null;
            if (state === WebSocket.OPEN) {
              websocket.close(1000, 'Reconnecting');
            }
          }
          websocket = null;
        }

        console.log(`Attempting to connect WebSocket (attempt ${reconnectAttempts + 1})...`);
        websocket = new WebSocket('ws://localhost:8000/ws/cost-stream');
        
        websocket.onopen = (event) => {
          console.log('WebSocket connected successfully');
          reconnectAttempts = 0; // Reset on successful connection
          setWs(websocket);
        };
        
        websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setCostData(data);
            console.log('WebSocket message received:', data);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error, event.data);
          }
        };

        websocket.onerror = (error) => {
          console.error('WebSocket error event:', {
            readyState: websocket?.readyState,
            url: websocket?.url,
            error
          });
          // onerror doesn't provide detailed error info, check onclose for more details
        };

        websocket.onclose = (event) => {
          console.log('WebSocket closed:', {
            code: event.code,
            reason: event.reason || 'No reason provided',
            wasClean: event.wasClean,
            readyState: websocket?.readyState
          });
          
          setWs(null);
          
          // Don't reconnect if it was a normal closure (code 1000) or component unmounting
          if (!isComponentMounted || event.code === 1000) {
            return;
          }
          
          // Try to reconnect if not a normal closure and we haven't exceeded max attempts
          if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts}) in ${reconnectDelay}ms...`);
            reconnectTimeout = setTimeout(() => {
              if (isComponentMounted) {
                connectWebSocket();
              }
            }, reconnectDelay);
          } else {
            console.error('Max reconnection attempts reached. WebSocket will not reconnect.');
          }
        };
      } catch (error) {
        console.error('Error creating WebSocket connection:', error);
        // Try to reconnect after delay
        if (isComponentMounted && reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++;
          reconnectTimeout = setTimeout(() => {
            if (isComponentMounted) {
              connectWebSocket();
            }
          }, reconnectDelay);
        }
      }
    };

    // Small delay before initial connection to ensure backend is ready
    const initialDelay = setTimeout(() => {
      if (isComponentMounted) {
        connectWebSocket();
      }
    }, 500);

    // Fetch initial data via HTTP as fallback
    fetchCostData();

    // Cleanup function
    return () => {
      isComponentMounted = false;
      clearTimeout(initialDelay);
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (websocket) {
        // Clean up event handlers
        websocket.onopen = null;
        websocket.onmessage = null;
        websocket.onerror = null;
        websocket.onclose = null;
        // Only close if connection is open or connecting
        if (websocket.readyState === WebSocket.OPEN || websocket.readyState === WebSocket.CONNECTING) {
          websocket.close(1000, 'Component unmounting');
        }
      }
    };
  }, []);

  const fetchCostData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/cost/namespaces');
      const data = await response.json();
      setCostData(data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🏦 FinOps Platform</h1>
        <p className="subtitle">Real-time Cost Intelligence & Optimization</p>
      </header>

      <nav className="tab-navigation">
        <button 
          className={activeTab === 'dashboard' ? 'active' : ''}
          onClick={() => setActiveTab('dashboard')}
        >
          📊 Dashboard
        </button>
        <button 
          className={activeTab === 'breakdown' ? 'active' : ''}
          onClick={() => setActiveTab('breakdown')}
        >
          💰 Cost Breakdown
        </button>
        <button 
          className={activeTab === 'recommendations' ? 'active' : ''}
          onClick={() => setActiveTab('recommendations')}
        >
          💡 Recommendations
        </button>
        <button 
          className={activeTab === 'alerts' ? 'active' : ''}
          onClick={() => setActiveTab('alerts')}
        >
          🚨 Alerts
        </button>
      </nav>

      <main className="app-content">
        {activeTab === 'dashboard' && <Dashboard costData={costData} />}
        {activeTab === 'breakdown' && <CostBreakdown />}
        {activeTab === 'recommendations' && <Recommendations />}
        {activeTab === 'alerts' && <Alerts />}
      </main>

      <footer className="app-footer">
        <p>FinOps Platform v1.0 | Last updated: {new Date().toLocaleTimeString()}</p>
      </footer>
    </div>
  );
}

export default App;
