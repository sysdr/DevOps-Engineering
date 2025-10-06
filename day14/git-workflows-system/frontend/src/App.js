import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell
} from 'recharts';
import { 
  GitBranch, GitMerge, Shield, Package, Database, 
  Activity, CheckCircle, AlertTriangle, Clock
} from 'lucide-react';
import './App.css';

function App() {
  const [workflowStatus, setWorkflowStatus] = useState({});
  const [analytics, setAnalytics] = useState({});
  const [mergeQueue, setMergeQueue] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    fetchData();
    connectWebSocket();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const connectWebSocket = () => {
    const websocket = new WebSocket('ws://localhost:8000/ws');
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type) {
        addNotification(data);
        fetchData(); // Refresh data on updates
      }
    };
    
    setWs(websocket);
  };

  const fetchData = async () => {
    try {
      const [statusRes, analyticsRes] = await Promise.all([
        axios.get('/api/workflow/status'),
        axios.get('/api/workflow/analytics')
      ]);
      
      setWorkflowStatus(statusRes.data);
      setAnalytics(analyticsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const addNotification = (data) => {
    const notification = {
      id: Date.now(),
      type: data.type,
      message: formatNotificationMessage(data),
      timestamp: new Date().toLocaleTimeString()
    };
    
    setNotifications(prev => [notification, ...prev.slice(0, 4)]);
  };

  const formatNotificationMessage = (data) => {
    switch (data.type) {
      case 'branch_protection_created':
        return `Branch protection rule created for ${data.data.branch}`;
      case 'merge_queue_updated':
        return `Added ${data.data.branch} to merge queue`;
      case 'merge_completed':
        return `Successfully merged ${data.data.branch}`;
      case 'dependency_updated':
        return `Updated ${data.data.package} to ${data.data.to_version}`;
      case 'lfs_file_tracked':
        return `LFS tracking added for ${data.data.path}`;
      default:
        return 'Workflow event occurred';
    }
  };

  const handleBranchProtection = async () => {
    try {
      await axios.post('/api/workflow/branch-protection', {
        branch: 'main',
        require_reviews: 2,
        require_status_checks: true
      });
    } catch (error) {
      console.error('Error creating branch protection:', error);
    }
  };

  const handleMergeRequest = async () => {
    try {
      await axios.post('/api/workflow/merge-queue', {
        branch: `feature/update-${Date.now()}`,
        target: 'main',
        author: 'developer@company.com'
      });
    } catch (error) {
      console.error('Error adding to merge queue:', error);
    }
  };

  const handleProcessMerge = async () => {
    try {
      await axios.post('/api/workflow/process-merge-queue');
    } catch (error) {
      console.error('Error processing merge queue:', error);
    }
  };

  const handleDependencyUpdate = async () => {
    try {
      await axios.post('/api/workflow/dependency-update');
    } catch (error) {
      console.error('Error updating dependency:', error);
    }
  };

  const handleLfsTrack = async () => {
    try {
      await axios.post('/api/workflow/lfs-track', {
        path: 'assets/large-file.bin',
        size: Math.floor(Math.random() * 1000000),
        type: 'binary'
      });
    } catch (error) {
      console.error('Error tracking LFS file:', error);
    }
  };

  const chartData = [
    { name: 'Merges', value: analytics.merge_queue?.success_rate || 0 },
    { name: 'Protection', value: analytics.branch_protection?.enforcement_rate || 0 },
    { name: 'Dependencies', value: 85 },
    { name: 'LFS', value: 92 }
  ];

  const COLORS = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      <div className="container mx-auto px-6 py-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Git Workflows Manager
          </h1>
          <p className="text-slate-300 mt-2">Enterprise-grade Git workflow automation and monitoring</p>
        </header>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatusCard 
            icon={<GitBranch />} 
            title="Branches" 
            value={workflowStatus.branches || 0}
            color="bg-blue-500"
          />
          <StatusCard 
            icon={<GitMerge />} 
            title="Merge Queue" 
            value={workflowStatus.merge_queue_size || 0}
            color="bg-green-500"
          />
          <StatusCard 
            icon={<Shield />} 
            title="Protection Rules" 
            value={workflowStatus.protection_rules || 0}
            color="bg-purple-500"
          />
          <StatusCard 
            icon={<Package />} 
            title="Dependencies" 
            value={workflowStatus.dependencies || 0}
            color="bg-orange-500"
          />
        </div>

        {/* Action Buttons */}
        <div className="bg-slate-800/50 rounded-xl p-6 mb-8 backdrop-blur-sm border border-slate-700">
          <h2 className="text-xl font-semibold mb-4">Workflow Actions</h2>
          <div className="flex flex-wrap gap-4">
            <ActionButton onClick={handleBranchProtection} icon={<Shield />}>
              Add Branch Protection
            </ActionButton>
            <ActionButton onClick={handleMergeRequest} icon={<GitMerge />}>
              Create Merge Request
            </ActionButton>
            <ActionButton onClick={handleProcessMerge} icon={<CheckCircle />}>
              Process Merge Queue
            </ActionButton>
            <ActionButton onClick={handleDependencyUpdate} icon={<Package />}>
              Update Dependencies
            </ActionButton>
            <ActionButton onClick={handleLfsTrack} icon={<Database />}>
              Track LFS File
            </ActionButton>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-slate-800/50 rounded-xl p-6 backdrop-blur-sm border border-slate-700">
            <h3 className="text-lg font-semibold mb-4">Workflow Health</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-slate-800/50 rounded-xl p-6 backdrop-blur-sm border border-slate-700">
            <h3 className="text-lg font-semibold mb-4">Activity Timeline</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: '1px solid #374151',
                    borderRadius: '8px'
                  }} 
                />
                <Line type="monotone" dataKey="value" stroke="#10B981" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-slate-800/50 rounded-xl p-6 backdrop-blur-sm border border-slate-700">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Live Activity Feed
          </h3>
          <div className="space-y-3">
            {notifications.length === 0 ? (
              <p className="text-slate-400">No recent activity</p>
            ) : (
              notifications.map(notification => (
                <div key={notification.id} className="flex items-center gap-3 p-3 bg-slate-700/50 rounded-lg">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span className="flex-1">{notification.message}</span>
                  <span className="text-xs text-slate-400">{notification.timestamp}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const StatusCard = ({ icon, title, value, color }) => (
  <div className="bg-slate-800/50 rounded-xl p-6 backdrop-blur-sm border border-slate-700">
    <div className="flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        {React.cloneElement(icon, { className: "w-6 h-6" })}
      </div>
      <div>
        <h3 className="text-2xl font-bold">{value}</h3>
        <p className="text-slate-400">{title}</p>
      </div>
    </div>
  </div>
);

const ActionButton = ({ children, onClick, icon }) => (
  <button
    onClick={onClick}
    className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 px-4 py-2 rounded-lg transition-all duration-200 transform hover:scale-105"
  >
    {React.cloneElement(icon, { className: "w-4 h-4" })}
    {children}
  </button>
);

export default App;
