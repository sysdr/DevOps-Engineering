import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Box,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  CircularProgress
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [users, setUsers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [circuitBreakers, setCircuitBreakers] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Form states
  const [userForm, setUserForm] = useState({ email: '', full_name: '', is_active: true });
  const [orderForm, setOrderForm] = useState({ 
    user_id: '', 
    items: [{ product_id: 1, quantity: 1, price: 29.99 }], 
    total_amount: 29.99 
  });

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchCircuitBreakers, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [usersRes, ordersRes, notificationsRes, cbRes] = await Promise.all([
        axios.get(`${API_BASE}/users/`),
        axios.get(`${API_BASE}/orders/`),
        axios.get(`${API_BASE}/notifications/`),
        axios.get(`${API_BASE}/circuit-breakers/`)
      ]);
      
      setUsers(usersRes.data);
      setOrders(ordersRes.data);
      setNotifications(notificationsRes.data);
      setCircuitBreakers(cbRes.data);
      setError('');
    } catch (err) {
      setError('Failed to fetch data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchCircuitBreakers = async () => {
    try {
      const response = await axios.get(`${API_BASE}/circuit-breakers/`);
      setCircuitBreakers(response.data);
    } catch (err) {
      console.error('Failed to fetch circuit breaker status:', err);
    }
  };

  const createUser = async () => {
    try {
      await axios.post(`${API_BASE}/users/`, userForm);
      setUserForm({ email: '', full_name: '', is_active: true });
      fetchData();
    } catch (err) {
      setError('Failed to create user: ' + err.message);
    }
  };

  const createOrder = async () => {
    try {
      await axios.post(`${API_BASE}/orders/`, orderForm);
      setOrderForm({ 
        user_id: '', 
        items: [{ product_id: 1, quantity: 1, price: 29.99 }], 
        total_amount: 29.99 
      });
      fetchData();
    } catch (err) {
      setError('Failed to create order: ' + err.message);
    }
  };

  const getCircuitBreakerColor = (state) => {
    switch (state) {
      case 'closed': return 'success';
      case 'open': return 'error';
      case 'half_open': return 'warning';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)', py: 4 }}>
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom sx={{ 
        background: 'linear-gradient(45deg, #FF6B9D 30%, #C9789D 60%, #FFD93D 90%)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        fontWeight: 'bold',
        textAlign: 'center',
        mb: 4
      }}>
        Microservices Communication Dashboard
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Circuit Breaker Status */}
      <Card sx={{ mb: 4, background: 'linear-gradient(135deg, #FF6B9D 0%, #C9789D 100%)' }}>
        <CardContent>
          <Typography variant="h5" sx={{ color: 'white', mb: 2, fontWeight: 'bold' }}>
            Circuit Breaker Status
          </Typography>
          <Grid container spacing={2}>
            {Object.entries(circuitBreakers).map(([service, status]) => (
              <Grid item xs={12} md={4} key={service}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography sx={{ color: 'white', flexGrow: 1 }}>
                    {service.replace('-', ' ').toUpperCase()}
                  </Typography>
                  <Chip 
                    label={status.state.toUpperCase()} 
                    color={getCircuitBreakerColor(status.state)}
                    size="small"
                  />
                  <Typography sx={{ color: 'white', fontSize: '0.875rem' }}>
                    Failures: {status.failure_count}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Create User */}
        <Grid item xs={12} md={6}>
          <Card sx={{ background: 'linear-gradient(135deg, #FF6B9D 0%, #FF9A9E 100%)', boxShadow: '0 8px 16px rgba(255, 107, 157, 0.3)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: 'white', mb: 2, fontWeight: 'bold' }}>
                Create User
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  label="Email"
                  value={userForm.email}
                  onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                  variant="outlined"
                  size="small"
                  sx={{ 
                    '& .MuiOutlinedInput-root': { 
                      backgroundColor: 'rgba(255,255,255,0.9)' 
                    } 
                  }}
                />
                <TextField
                  label="Full Name"
                  value={userForm.full_name}
                  onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })}
                  variant="outlined"
                  size="small"
                  sx={{ 
                    '& .MuiOutlinedInput-root': { 
                      backgroundColor: 'rgba(255,255,255,0.9)' 
                    } 
                  }}
                />
                <Button 
                  variant="contained" 
                  onClick={createUser}
                  sx={{ 
                    backgroundColor: 'rgba(255,255,255,0.2)', 
                    '&:hover': { backgroundColor: 'rgba(255,255,255,0.3)' }
                  }}
                >
                  Create User
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Create Order */}
        <Grid item xs={12} md={6}>
          <Card sx={{ background: 'linear-gradient(135deg, #FFD93D 0%, #FFA500 100%)', boxShadow: '0 8px 16px rgba(255, 217, 61, 0.3)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: 'white', mb: 2, fontWeight: 'bold' }}>
                Create Order
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  label="User ID"
                  type="number"
                  value={orderForm.user_id}
                  onChange={(e) => setOrderForm({ ...orderForm, user_id: e.target.value })}
                  variant="outlined"
                  size="small"
                  sx={{ 
                    '& .MuiOutlinedInput-root': { 
                      backgroundColor: 'rgba(255,255,255,0.9)' 
                    } 
                  }}
                />
                <TextField
                  label="Total Amount"
                  type="number"
                  value={orderForm.total_amount}
                  onChange={(e) => setOrderForm({ ...orderForm, total_amount: parseFloat(e.target.value) })}
                  variant="outlined"
                  size="small"
                  sx={{ 
                    '& .MuiOutlinedInput-root': { 
                      backgroundColor: 'rgba(255,255,255,0.9)' 
                    } 
                  }}
                />
                <Button 
                  variant="contained" 
                  onClick={createOrder}
                  sx={{ 
                    backgroundColor: 'rgba(255,255,255,0.2)', 
                    '&:hover': { backgroundColor: 'rgba(255,255,255,0.3)' }
                  }}
                >
                  Create Order
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Users Table */}
        <Grid item xs={12} md={4}>
          <Card sx={{ background: 'linear-gradient(135deg, #6BCB77 0%, #4CAF50 100%)', color: 'white' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ color: 'white', fontWeight: 'bold' }}>Users ({users.length})</Typography>
              <TableContainer component={Paper} sx={{ maxHeight: 300 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>ID</TableCell>
                      <TableCell>Email</TableCell>
                      <TableCell>Name</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {users.slice(0, 5).map((user) => (
                      <TableRow key={user.id}>
                        <TableCell>{user.id}</TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>{user.full_name}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Orders Table */}
        <Grid item xs={12} md={4}>
          <Card sx={{ background: 'linear-gradient(135deg, #4D96FF 0%, #2196F3 100%)', color: 'white' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ color: 'white', fontWeight: 'bold' }}>Orders ({orders.length})</Typography>
              <TableContainer component={Paper} sx={{ maxHeight: 300 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>ID</TableCell>
                      <TableCell>User</TableCell>
                      <TableCell>Amount</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {orders.slice(0, 5).map((order) => (
                      <TableRow key={order.id}>
                        <TableCell>{order.id}</TableCell>
                        <TableCell>{order.user_id}</TableCell>
                        <TableCell>${order.total_amount}</TableCell>
                        <TableCell>
                          <Chip label={order.status} size="small" color="primary" />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Notifications Table */}
        <Grid item xs={12} md={4}>
          <Card sx={{ background: 'linear-gradient(135deg, #FF6B9D 0%, #C9789D 100%)', color: 'white' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ color: 'white', fontWeight: 'bold' }}>Notifications ({notifications.length})</Typography>
              <TableContainer component={Paper} sx={{ maxHeight: 300 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>User</TableCell>
                      <TableCell>Title</TableCell>
                      <TableCell>Type</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {notifications.slice(0, 5).map((notification) => (
                      <TableRow key={notification.id}>
                        <TableCell>{notification.user_id}</TableCell>
                        <TableCell>{notification.title}</TableCell>
                        <TableCell>
                          <Chip label={notification.type} size="small" color="secondary" />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3, textAlign: 'center' }}>
        <Button 
          variant="contained" 
          onClick={fetchData} 
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
          sx={{ 
            background: 'linear-gradient(135deg, #FF6B9D 0%, #C9789D 100%)',
            color: 'white',
            fontWeight: 'bold',
            px: 4,
            py: 1.5,
            boxShadow: '0 4px 12px rgba(255, 107, 157, 0.4)',
            '&:hover': { 
              background: 'linear-gradient(135deg, #C9789D 0%, #FF6B9D 100%)',
              boxShadow: '0 6px 16px rgba(255, 107, 157, 0.6)'
            }
          }}
        >
          {loading ? 'Refreshing...' : 'Refresh Data'}
        </Button>
      </Box>
    </Container>
    </Box>
  );
}

export default App;
