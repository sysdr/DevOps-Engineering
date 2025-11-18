import React, { useState, useEffect, useRef } from 'react';
import SLODashboard from './components/SLODashboard';
import MetricsPanel from './components/MetricsPanel';
import IncidentPanel from './components/IncidentPanel';
import DeploymentFeed from './components/DeploymentFeed';

const App = () => {
    const [data, setData] = useState(null);
    const [connected, setConnected] = useState(false);
    const wsRef = useRef(null);

    useEffect(() => {
        const connectWebSocket = () => {
            const ws = new WebSocket('ws://localhost:8000/ws');
            
            ws.onopen = () => {
                setConnected(true);
                console.log('WebSocket connected');
            };
            
            ws.onmessage = (event) => {
                try {
                    const newData = JSON.parse(event.data);
                    setData(newData);
                } catch (e) {
                    console.error('Parse error:', e);
                }
            };
            
            ws.onclose = () => {
                setConnected(false);
                setTimeout(connectWebSocket, 3000);
            };
            
            wsRef.current = ws;
        };

        connectWebSocket();
        return () => wsRef.current?.close();
    }, []);

    const getSystemStatus = () => {
        if (!data?.evaluations) return { status: 'unknown', color: '#94a3b8' };
        const statuses = data.evaluations.map(e => e.status);
        if (statuses.includes('critical')) return { status: 'CRITICAL', color: '#ef4444' };
        if (statuses.includes('warning')) return { status: 'WARNING', color: '#f59e0b' };
        return { status: 'HEALTHY', color: '#10b981' };
    };

    const systemStatus = getSystemStatus();

    return (
        <div style={{ minHeight: '100vh', background: '#f8fafc' }}>
            <header style={{
                background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%)',
                padding: '20px 32px',
                color: 'white',
                boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '4px' }}>
                            GitOps Observability Platform
                        </h1>
                        <p style={{ fontSize: '14px', opacity: 0.8 }}>
                            SLI/SLO Tracking & Incident Automation
                        </p>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                        <div style={{
                            padding: '8px 16px',
                            background: systemStatus.color,
                            borderRadius: '20px',
                            fontSize: '12px',
                            fontWeight: '600'
                        }}>
                            {systemStatus.status}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div style={{
                                width: '8px',
                                height: '8px',
                                borderRadius: '50%',
                                background: connected ? '#10b981' : '#ef4444'
                            }} />
                            <span style={{ fontSize: '12px' }}>
                                {connected ? 'Live' : 'Reconnecting...'}
                            </span>
                        </div>
                    </div>
                </div>
            </header>

            <main style={{
                padding: '24px clamp(16px, 4vw, 32px)',
                maxWidth: '1600px',
                margin: '0 auto',
                width: '100%',
                boxSizing: 'border-box'
            }}>
                {data ? (
                    <>
                        <SLODashboard evaluations={data.evaluations} slis={data.slis} />
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                            gap: '24px',
                            marginTop: '24px'
                        }}>
                            <MetricsPanel metrics={data.metrics} slis={data.slis} />
                            <IncidentPanel incidents={data.incidents} />
                        </div>
                        <DeploymentFeed deployments={data.deployments} />
                    </>
                ) : (
                    <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        height: '400px',
                        color: '#64748b'
                    }}>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{
                                width: '40px',
                                height: '40px',
                                border: '3px solid #e2e8f0',
                                borderTopColor: '#3b82f6',
                                borderRadius: '50%',
                                animation: 'spin 1s linear infinite',
                                margin: '0 auto 16px'
                            }} />
                            <p>Connecting to observability platform...</p>
                        </div>
                    </div>
                )}
            </main>
            
            <style>{`
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
};

export default App;
