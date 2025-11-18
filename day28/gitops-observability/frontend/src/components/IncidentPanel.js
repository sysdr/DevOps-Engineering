import React from 'react';

const IncidentPanel = ({ incidents }) => {
    const getSeverityStyles = (severity) => {
        switch (severity) {
            case 'critical':
                return { bg: '#fef2f2', border: '#fecaca', text: '#dc2626' };
            case 'warning':
                return { bg: '#fffbeb', border: '#fde68a', text: '#d97706' };
            default:
                return { bg: '#f0fdf4', border: '#bbf7d0', text: '#16a34a' };
        }
    };

    const formatTime = (timestamp) => {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b' }}>
                    Active Incidents
                </h2>
                <span style={{
                    fontSize: '12px',
                    padding: '4px 10px',
                    background: incidents?.length > 0 ? '#fef2f2' : '#f0fdf4',
                    color: incidents?.length > 0 ? '#dc2626' : '#16a34a',
                    borderRadius: '12px',
                    fontWeight: '500'
                }}>
                    {incidents?.length || 0} active
                </span>
            </div>

            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {incidents && incidents.length > 0 ? (
                    incidents.map((incident, idx) => {
                        const styles = getSeverityStyles(incident.severity);
                        return (
                            <div key={incident.id || idx} style={{
                                padding: '14px',
                                marginBottom: '12px',
                                background: styles.bg,
                                border: `1px solid ${styles.border}`,
                                borderRadius: '8px'
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                    <span style={{
                                        fontSize: '11px',
                                        fontWeight: '600',
                                        color: styles.text,
                                        textTransform: 'uppercase'
                                    }}>
                                        {incident.severity}
                                    </span>
                                    <span style={{ fontSize: '11px', color: '#64748b' }}>
                                        {formatTime(incident.created_at)}
                                    </span>
                                </div>
                                <div style={{ fontSize: '13px', fontWeight: '500', color: '#1e293b', marginBottom: '6px' }}>
                                    {incident.slo_name}
                                </div>
                                <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>
                                    Current: {incident.current_value?.toFixed(1)}% | Target: {incident.target_value}%
                                </div>
                                {incident.actions_taken && (
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                        {incident.actions_taken.map((action, i) => (
                                            <span key={i} style={{
                                                fontSize: '10px',
                                                padding: '2px 6px',
                                                background: 'white',
                                                borderRadius: '4px',
                                                color: '#64748b'
                                            }}>
                                                {action.replace(/_/g, ' ')}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })
                ) : (
                    <div style={{
                        textAlign: 'center',
                        padding: '40px',
                        color: '#94a3b8'
                    }}>
                        <div style={{ fontSize: '32px', marginBottom: '8px' }}>✓</div>
                        <div style={{ fontSize: '14px' }}>No active incidents</div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default IncidentPanel;
