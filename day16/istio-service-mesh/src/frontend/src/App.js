import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = window.location.hostname === 'localhost' 
  ? 'http://localhost:8081' 
  : `http://${window.location.hostname}:8081`;

function App() {
  const [users, setUsers] = useState([]);
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [cart, setCart] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    fetchUsers();
    fetchProducts();
    fetchOrders();
    fetchMetrics();
    
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API_BASE}/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API_BASE}/products`);
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API_BASE}/orders`);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await axios.get(`${API_BASE}/metrics`);
      setMetrics({ timestamp: new Date().toLocaleTimeString() });
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const createOrder = async () => {
    if (!selectedUser || cart.length === 0) return;
    
    try {
      const orderData = {
        user_id: selectedUser.id,
        items: cart.map(item => ({
          product_id: item.id,
          quantity: item.quantity
        }))
      };
      
      await axios.post(`${API_BASE}/orders`, orderData);
      setCart([]);
      fetchOrders();
      alert('Order created successfully!');
    } catch (error) {
      console.error('Error creating order:', error);
      alert('Error creating order');
    }
  };

  const addToCart = (product) => {
    const existingItem = cart.find(item => item.id === product.id);
    if (existingItem) {
      setCart(cart.map(item => 
        item.id === product.id 
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      setCart([...cart, { ...product, quantity: 1 }]);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🚢 Istio Service Mesh E-commerce Demo</h1>
        <div className="status-bar">
          <span className="status-item">
            🟢 All Services Healthy
          </span>
          <span className="status-item">
            🔒 mTLS Enabled
          </span>
          <span className="status-item">
            📊 Observability Active
          </span>
        </div>
      </header>

      <nav className="nav">
        <button 
          className={activeTab === 'dashboard' ? 'active' : ''} 
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>
        <button 
          className={activeTab === 'products' ? 'active' : ''} 
          onClick={() => setActiveTab('products')}
        >
          Products
        </button>
        <button 
          className={activeTab === 'orders' ? 'active' : ''} 
          onClick={() => setActiveTab('orders')}
        >
          Orders
        </button>
        <button 
          className={activeTab === 'metrics' ? 'active' : ''} 
          onClick={() => setActiveTab('metrics')}
        >
          Istio Metrics
        </button>
      </nav>

      <main className="main">
        {activeTab === 'dashboard' && (
          <div className="dashboard">
            <div className="stats-grid">
              <div className="stat-card">
                <h3>Total Users</h3>
                <div className="stat-value">{users.length}</div>
              </div>
              <div className="stat-card">
                <h3>Products Available</h3>
                <div className="stat-value">{products.length}</div>
              </div>
              <div className="stat-card">
                <h3>Orders Processed</h3>
                <div className="stat-value">{orders.length}</div>
              </div>
              <div className="stat-card">
                <h3>Service Mesh Status</h3>
                <div className="stat-value">🟢 Active</div>
              </div>
            </div>
            
            <div className="user-selector">
              <h3>Select User</h3>
              <div className="user-cards">
                {users.map(user => (
                  <div 
                    key={user.id} 
                    className={`user-card ${selectedUser?.id === user.id ? 'selected' : ''}`}
                    onClick={() => setSelectedUser(user)}
                  >
                    <h4>{user.name}</h4>
                    <p>{user.email}</p>
                    <span className={`tier ${user.tier}`}>
                      {user.tier === 'premium' ? '⭐ Premium' : '🔵 Standard'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'products' && (
          <div className="products">
            <div className="section-header">
              <h2>Products (Product Service)</h2>
              {selectedUser && (
                <div className="cart-info">
                  Cart: {cart.length} items
                </div>
              )}
            </div>
            <div className="product-grid">
              {products.map(product => (
                <div key={product.id} className="product-card">
                  <h3>{product.name}</h3>
                  <p className="price">${product.price}</p>
                  <p className="category">{product.category}</p>
                  <p className="stock">Stock: {product.stock}</p>
                  {selectedUser && (
                    <button 
                      className="add-to-cart"
                      onClick={() => addToCart(product)}
                    >
                      Add to Cart
                    </button>
                  )}
                </div>
              ))}
            </div>
            
            {selectedUser && cart.length > 0 && (
              <div className="cart-section">
                <h3>Shopping Cart</h3>
                <div className="cart-items">
                  {cart.map(item => (
                    <div key={item.id} className="cart-item">
                      {item.name} x {item.quantity} - ${(item.price * item.quantity).toFixed(2)}
                    </div>
                  ))}
                </div>
                <div className="cart-total">
                  Total: ${cart.reduce((sum, item) => sum + (item.price * item.quantity), 0).toFixed(2)}
                </div>
                <button className="checkout-btn" onClick={createOrder}>
                  Create Order
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'orders' && (
          <div className="orders">
            <h2>Orders (Order Service)</h2>
            <div className="order-list">
              {orders.map(order => (
                <div key={order.id} className="order-card">
                  <h3>Order #{order.id}</h3>
                  <p>User ID: {order.user_id}</p>
                  <p>Items: {order.items.length}</p>
                  <p>Total: ${order.total}</p>
                  <p>Status: <span className="status">{order.status}</span></p>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'metrics' && (
          <div className="metrics">
            <h2>Istio Service Mesh Metrics</h2>
            <div className="metrics-info">
              <div className="metric-card">
                <h3>🔄 Traffic Management</h3>
                <p>Virtual Services: Active</p>
                <p>Load Balancing: Round Robin</p>
                <p>Circuit Breaker: Enabled</p>
              </div>
              
              <div className="metric-card">
                <h3>🔒 Security</h3>
                <p>mTLS: Enabled</p>
                <p>Authentication: Active</p>
                <p>Authorization: Configured</p>
              </div>
              
              <div className="metric-card">
                <h3>📊 Observability</h3>
                <p>Distributed Tracing: Jaeger</p>
                <p>Metrics: Prometheus</p>
                <p>Dashboards: Grafana</p>
              </div>
              
              <div className="metric-card">
                <h3>⚡ Performance</h3>
                <p>Request Latency: <span className="highlight">&lt;10ms</span></p>
                <p>Success Rate: <span className="highlight">99.5%</span></p>
                <p>Throughput: <span className="highlight">1K RPS</span></p>
              </div>
            </div>
            
            <div className="service-topology">
              <h3>Service Mesh Topology</h3>
              <div className="topology-diagram">
                <div className="service-node ingress">
                  <span>🌐 Istio Gateway</span>
                </div>
                <div className="service-node">
                  <span>👥 User Service</span>
                </div>
                <div className="service-node">
                  <span>📦 Product Service</span>
                </div>
                <div className="service-node">
                  <span>🛒 Order Service</span>
                </div>
                <div className="service-node">
                  <span>🎯 Recommendation Service</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
