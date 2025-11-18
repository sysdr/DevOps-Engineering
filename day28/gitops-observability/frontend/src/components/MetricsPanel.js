import React from 'react';

const MetricsPanel = ({ metrics, slis }) => {
    const formatNumber = (num) => {
        if (typeof num !== 'number') return '0';
        return num.toFixed(1);
    };

    return (
        <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px', color: '#1e293b' }}>
                System Metrics
            </h2>

            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '16px',
                marginBottom: '24px'
            }}>
                <MetricCard
                    title="Success Rate"
                    value={`${slis?.success_rate?.value || 0}%`}
                    subtitle={`${slis?.success_rate?.successful || 0}/${slis?.success_rate?.total || 0} deployments`}
                    color="#10b981"
                />
                <MetricCard
                    title="Avg Sync Latency"
                    value={`${((slis?.sync_latency?.avg_ms || 0) / 1000).toFixed(1)}s`}
                    subtitle={`P99: ${((slis?.sync_latency_p99 || 0) / 1000).toFixed(1)}s`}
                    color="#3b82f6"
                />
                <MetricCard
                    title="Throughput"
                    value={`${slis?.throughput?.per_hour || 0}/hr`}
                    subtitle="Deployment frequency"
                    color="#8b5cf6"
                />
                <MetricCard
                    title="Error Rate"
                    value={formatNumber(slis?.error_rate || 0)}
                    subtitle="Errors per collection"
                    color="#f59e0b"
                />
            </div>

            <h3 style={{ fontSize: '14px', fontWeight: '500', marginBottom: '12px', color: '#475569' }}>
                Resource Utilization
            </h3>
            
            <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '24px'
            }}>
                <ResourceBar
                    label="CPU"
                    value={slis?.resource_saturation?.cpu || 0}
                    max={slis?.resource_saturation?.cpu_max || 0}
                />
                <ResourceBar
                    label="Memory"
                    value={slis?.resource_saturation?.memory || 0}
                    max={slis?.resource_saturation?.memory_max || 0}
                />
            </div>
        </div>
    );
};

const MetricCard = ({ title, value, subtitle, color }) => (
    <div style={{
        padding: '16px',
        background: '#f8fafc',
        borderRadius: '8px',
        borderLeft: `3px solid ${color}`
    }}>
        <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>{title}</div>
        <div style={{ fontSize: '24px', fontWeight: '600', color: '#1e293b' }}>{value}</div>
        <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>{subtitle}</div>
    </div>
);

const ResourceBar = ({ label, value, max }) => (
    <div style={{ flex: '1 1 220px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
            <span style={{ color: '#64748b' }}>{label}</span>
            <span style={{ color: '#1e293b', fontWeight: '500' }}>{value.toFixed(1)}%</span>
        </div>
        <div style={{ height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{
                height: '100%',
                width: `${value}%`,
                background: value > 80 ? '#ef4444' : value > 60 ? '#f59e0b' : '#10b981',
                transition: 'width 0.3s ease'
            }} />
        </div>
        <div style={{ fontSize: '10px', color: '#94a3b8', marginTop: '4px' }}>
            Max: {max.toFixed(1)}%
        </div>
    </div>
);

export default MetricsPanel;
