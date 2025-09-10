const { useState, useEffect } = React;

function Dashboard() {
    const [metrics, setMetrics] = useState({});
    const [containers, setContainers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [building, setBuilding] = useState(false);
    const [scanning, setScanning] = useState(false);
    const [benchmarks, setBenchmarks] = useState(null);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            const [metricsRes, containersRes] = await Promise.all([
                fetch('http://localhost:5000/api/metrics'),
                fetch('http://localhost:5000/api/containers')
            ]);

            if (metricsRes.ok) {
                const metricsData = await metricsRes.json();
                setMetrics(metricsData);
            }

            if (containersRes.ok) {
                const containersData = await containersRes.json();
                setContainers(containersData.containers || []);
            }

            setLoading(false);
            setError(null);
        } catch (err) {
            setError('Failed to fetch data from backend');
            setLoading(false);
        }
    };

    const buildImage = async () => {
        setBuilding(true);
        try {
            const response = await fetch('http://localhost:5000/api/build', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: 'demo-app', arch: 'amd64'})
            });
            
            if (response.ok) {
                alert('Build completed successfully!');
                fetchData();
            } else {
                alert('Build failed');
            }
        } catch (err) {
            alert('Build request failed');
        }
        setBuilding(false);
    };

    const scanImage = async () => {
        setScanning(true);
        try {
            const response = await fetch('http://localhost:5000/api/scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({image_name: 'demo-app:amd64'})
            });
            
            if (response.ok) {
                const result = await response.json();
                alert(`Scan completed. Found vulnerabilities: ${result.vulnerabilities ? 'Yes' : 'No'}`);
            } else {
                alert('Scan failed');
            }
        } catch (err) {
            alert('Scan request failed');
        }
        setScanning(false);
    };

    const fetchBenchmarks = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/benchmark');
            if (response.ok) {
                const data = await response.json();
                setBenchmarks(data);
                alert(`Podman vs Docker Benchmarks:\nPodman: ${data.podman.startup_time}s startup, ${data.podman.memory_overhead}MB overhead\nDocker: ${data.docker.startup_time}s startup, ${data.docker.memory_overhead}MB overhead`);
            }
        } catch (err) {
            alert('Failed to fetch benchmarks');
        }
    };

    if (loading) {
        return <div className="loading">Loading dashboard...</div>;
    }

    return (
        <div className="dashboard">
            <div className="header">
                <h1>🚀 Container Revolution Dashboard</h1>
                <p>Podman-Powered Container Platform with Security Scanning</p>
            </div>

            {error && <div className="error">{error}</div>}

            <div className="metrics-grid">
                <div className="metric-card">
                    <div className="metric-title">CPU Usage</div>
                    <div className="metric-value">{metrics.cpu?.toFixed(1) || '0'}</div>
                    <div className="metric-unit">%</div>
                </div>
                <div className="metric-card">
                    <div className="metric-title">Memory Usage</div>
                    <div className="metric-value">{metrics.memory?.toFixed(1) || '0'}</div>
                    <div className="metric-unit">%</div>
                </div>
                <div className="metric-card">
                    <div className="metric-title">Active Containers</div>
                    <div className="metric-value">{metrics.containers || 0}</div>
                    <div className="metric-unit">running</div>
                </div>
                <div className="metric-card">
                    <div className="metric-title">Platform</div>
                    <div className="metric-value">Podman</div>
                    <div className="metric-unit">rootless</div>
                </div>
            </div>

            <div className="controls-section">
                <h2 className="section-title">Container Operations</h2>
                <div className="controls-grid">
                    <button 
                        className="control-button" 
                        onClick={buildImage}
                        disabled={building}
                    >
                        {building ? 'Building...' : '🔨 Build Multi-Arch Image'}
                    </button>
                    <button 
                        className="control-button" 
                        onClick={scanImage}
                        disabled={scanning}
                    >
                        {scanning ? 'Scanning...' : '🔍 Security Scan'}
                    </button>
                    <button className="control-button" onClick={fetchBenchmarks}>
                        📊 View Benchmarks
                    </button>
                    <button className="control-button">
                        🔐 Registry Push
                    </button>
                </div>
            </div>

            <div className="containers-section">
                <h2 className="section-title">Running Containers</h2>
                <div className="container-list">
                    {containers.length === 0 ? (
                        <p>No containers running</p>
                    ) : (
                        containers.map((container, index) => (
                            <div key={index} className="container-item">
                                <div className="container-name">
                                    {container.Names?.[0] || 'Unknown'}
                                </div>
                                <span className={`container-status status-${container.State || 'unknown'}`}>
                                    {container.State || 'Unknown'}
                                </span>
                                <p>{container.Image || 'No image info'}</p>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<Dashboard />);
