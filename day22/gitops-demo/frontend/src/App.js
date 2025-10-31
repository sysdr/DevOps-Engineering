import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  AppBar,
  Toolbar,
  Box,
  Paper,
  Alert
} from '@mui/material';
import {
  Sync as SyncIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Pending as PendingIcon
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

function App() {
  const [applications, setApplications] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchApplications();
    fetchMetrics();
    const interval = setInterval(() => {
      fetchApplications();
      fetchMetrics();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchApplications = async () => {
    try {
      const response = await axios.get('/applications');
      setApplications(response.data);
    } catch (error) {
      console.error('Error fetching applications:', error);
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await axios.get('/metrics');
      setMetrics(response.data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const handleSync = async (appName, environment) => {
    setLoading(true);
    try {
      await axios.post(`/sync/${appName}/${environment}`);
      setMessage(`Sync initiated for ${appName} in ${environment}`);
      setTimeout(() => setMessage(''), 3000);
      setTimeout(fetchApplications, 2000);
    } catch (error) {
      console.error('Error syncing application:', error);
      setMessage('Sync failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Synced': return 'success';
      case 'OutOfSync': return 'warning';
      case 'Progressing': return 'info';
      case 'Healthy': return 'success';
      case 'Degraded': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Synced':
      case 'Healthy': return <CheckIcon />;
      case 'OutOfSync':
      case 'Degraded': return <ErrorIcon />;
      default: return <PendingIcon />;
    }
  };

  const metricsData = [
    { name: 'Total Apps', value: metrics.applications_total || 0 },
    { name: 'Synced', value: metrics.applications_synced || 0 },
    { name: 'Out of Sync', value: metrics.applications_out_of_sync || 0 }
  ];

  return (
    <div style={{ backgroundColor: '#F5F7FA', minHeight: '100vh' }}>
      <AppBar position="static" sx={{ 
        background: 'linear-gradient(135deg, #2C3E50 0%, #34495E 100%)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
      }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600, letterSpacing: '0.5px' }}>
            GitOps Dashboard - Argo CD Demo
          </Typography>
          <Chip 
            label={`Sync Rate: ${Math.round(metrics.sync_success_rate || 0)}%`}
            color="success"
            variant="filled"
            sx={{ 
              backgroundColor: '#16A085',
              fontWeight: 500
            }}
          />
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4, backgroundColor: '#F5F7FA', minHeight: '100vh' }}>
        {message && (
          <Alert severity="info" sx={{ mb: 2 }}>
            {message}
          </Alert>
        )}

        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Paper sx={{ 
              p: 3, 
              textAlign: 'center', 
              background: 'linear-gradient(135deg, #5D6D7E 0%, #566573 100%)',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              transition: 'transform 0.2s',
              '&:hover': { transform: 'translateY(-4px)' }
            }}>
              <Typography variant="h4" sx={{ color: 'white', fontWeight: 700, mb: 1 }}>{metrics.applications_total || 0}</Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255,255,255,0.9)', fontWeight: 500 }}>Total Applications</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper sx={{ 
              p: 3, 
              textAlign: 'center', 
              background: 'linear-gradient(135deg, #16A085 0%, #138D75 100%)',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              transition: 'transform 0.2s',
              '&:hover': { transform: 'translateY(-4px)' }
            }}>
              <Typography variant="h4" sx={{ color: 'white', fontWeight: 700, mb: 1 }}>{metrics.applications_synced || 0}</Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255,255,255,0.9)', fontWeight: 500 }}>Synced Apps</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper sx={{ 
              p: 3, 
              textAlign: 'center', 
              background: 'linear-gradient(135deg, #E67E22 0%, #D35400 100%)',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              transition: 'transform 0.2s',
              '&:hover': { transform: 'translateY(-4px)' }
            }}>
              <Typography variant="h4" sx={{ color: 'white', fontWeight: 700, mb: 1 }}>{metrics.applications_out_of_sync || 0}</Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255,255,255,0.9)', fontWeight: 500 }}>Out of Sync</Typography>
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Paper sx={{ 
              p: 3,
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
            }}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: '#2C3E50', mb: 2 }}>
                GitOps Metrics
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={metricsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8E8E8" />
                  <XAxis dataKey="name" stroke="#7F8C8D" />
                  <YAxis stroke="#7F8C8D" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#FFFFFF',
                      border: '1px solid #E8E8E8',
                      borderRadius: '4px'
                    }}
                  />
                  <Line type="monotone" dataKey="value" stroke="#16A085" strokeWidth={3} dot={{ fill: '#16A085', r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: '#2C3E50', mt: 2 }}>
              Applications
            </Typography>
          </Grid>

          {applications.map((app, index) => (
            <Grid item xs={12} md={6} lg={4} key={index}>
              <Card sx={{ 
                height: '100%',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                border: '1px solid #E8E8E8',
                transition: 'all 0.3s ease',
                '&:hover': { 
                  boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
                  transform: 'translateY(-2px)'
                }
              }}>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: '#2C3E50' }}>{app.name}</Typography>
                    <Chip 
                      label={app.environment} 
                      size="small" 
                      sx={{ 
                        backgroundColor: '#16A085',
                        color: 'white',
                        fontWeight: 500
                      }} 
                    />
                  </Box>
                  
                  <Box mb={2}>
                    <Box display="flex" alignItems="center" mb={1}>
                      {getStatusIcon(app.sync_status)}
                      <Chip 
                        label={`Sync: ${app.sync_status}`}
                        color={getStatusColor(app.sync_status)}
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    </Box>
                    <Box display="flex" alignItems="center" mb={1}>
                      {getStatusIcon(app.health_status)}
                      <Chip 
                        label={`Health: ${app.health_status}`}
                        color={getStatusColor(app.health_status)}
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    </Box>
                  </Box>

                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Last Sync: {app.last_sync !== 'Never' ? new Date(app.last_sync).toLocaleString() : 'Never'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Revision: {app.git_revision}
                  </Typography>

                  <Button
                    variant="contained"
                    startIcon={<SyncIcon />}
                    onClick={() => handleSync(app.name, app.environment)}
                    disabled={loading}
                    fullWidth
                    sx={{ 
                      mt: 2,
                      backgroundColor: '#2C3E50',
                      color: 'white',
                      fontWeight: 500,
                      textTransform: 'none',
                      '&:hover': {
                        backgroundColor: '#34495E',
                      },
                      '&:disabled': {
                        backgroundColor: '#BDC3C7',
                      }
                    }}
                  >
                    Sync Now
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>
    </div>
  );
}

export default App;
