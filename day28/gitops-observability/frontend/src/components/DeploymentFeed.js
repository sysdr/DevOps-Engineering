import React from 'react';

const DeploymentFeed = ({ deployments }) => {
    const formatTime = (timestamp) => {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    };

    return (
        <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '24px',
            marginTop: '24px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px', color: '#1e293b' }}>
                Recent Deployments
            </h2>

            <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                    <thead>
                        <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
                            <th style={{ textAlign: 'left', padding: '12px 16px', color: '#64748b', fontWeight: '500' }}>Time</th>
                            <th style={{ textAlign: 'left', padding: '12px 16px', color: '#64748b', fontWeight: '500' }}>Application</th>
                            <th style={{ textAlign: 'left', padding: '12px 16px', color: '#64748b', fontWeight: '500' }}>Environment</th>
                            <th style={{ textAlign: 'left', padding: '12px 16px', color: '#64748b', fontWeight: '500' }}>Status</th>
                            <th style={{ textAlign: 'left', padding: '12px 16px', color: '#64748b', fontWeight: '500' }}>Duration</th>
                            <th style={{ textAlign: 'left', padding: '12px 16px', color: '#64748b', fontWeight: '500' }}>Sync Attempts</th>
                        </tr>
                    </thead>
                    <tbody>
                        {deployments && deployments.slice(0, 10).map((deployment, idx) => (
                            <tr key={deployment.id || idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                                <td style={{ padding: '12px 16px', color: '#64748b' }}>
                                    {formatTime(deployment.timestamp)}
                                </td>
                                <td style={{ padding: '12px 16px', fontWeight: '500', color: '#1e293b' }}>
                                    {deployment.app}
                                </td>
                                <td style={{ padding: '12px 16px' }}>
                                    <span style={{
                                        fontSize: '11px',
                                        padding: '2px 8px',
                                        borderRadius: '4px',
                                        background: deployment.environment === 'production' ? '#dbeafe' : '#f3e8ff',
                                        color: deployment.environment === 'production' ? '#2563eb' : '#9333ea'
                                    }}>
                                        {deployment.environment}
                                    </span>
                                </td>
                                <td style={{ padding: '12px 16px' }}>
                                    <span style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: '6px'
                                    }}>
                                        <span style={{
                                            width: '8px',
                                            height: '8px',
                                            borderRadius: '50%',
                                            background: deployment.status === 'success' ? '#10b981' : '#ef4444'
                                        }} />
                                        {deployment.status}
                                    </span>
                                </td>
                                <td style={{ padding: '12px 16px', color: '#64748b' }}>
                                    {(deployment.duration_ms / 1000).toFixed(1)}s
                                </td>
                                <td style={{ padding: '12px 16px', color: '#64748b' }}>
                                    {deployment.sync_attempts}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default DeploymentFeed;
