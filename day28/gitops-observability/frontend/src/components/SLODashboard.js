import React from 'react';

const SLODashboard = ({ evaluations, slis }) => {
    if (!evaluations || !evaluations.length) return null;

    const getStatusColor = (status) => {
        switch (status) {
            case 'critical': return '#ef4444';
            case 'warning': return '#f59e0b';
            default: return '#10b981';
        }
    };

    const getBudgetBarColor = (percent) => {
        if (percent < 20) return '#ef4444';
        if (percent < 50) return '#f59e0b';
        return '#10b981';
    };

    return (
        <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px', color: '#1e293b' }}>
                Service Level Objectives
            </h2>
            
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                gap: '20px'
            }}>
                {evaluations.map((evaluation) => (
                    <div key={evaluation.slo_id} style={{
                        padding: '20px',
                        border: '1px solid #e2e8f0',
                        borderRadius: '8px',
                        borderLeft: `4px solid ${getStatusColor(evaluation.status)}`
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                            <h3 style={{ fontSize: '14px', fontWeight: '500', color: '#475569' }}>
                                {evaluation.slo_name}
                            </h3>
                            <span style={{
                                fontSize: '11px',
                                padding: '2px 8px',
                                borderRadius: '10px',
                                background: `${getStatusColor(evaluation.status)}20`,
                                color: getStatusColor(evaluation.status),
                                fontWeight: '500'
                            }}>
                                {evaluation.status.toUpperCase()}
                            </span>
                        </div>
                        
                        <div style={{ marginBottom: '16px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>
                                <span>Current</span>
                                <span>Target: {evaluation.target}%</span>
                            </div>
                            <div style={{ fontSize: '28px', fontWeight: '600', color: '#1e293b' }}>
                                {evaluation.current}%
                            </div>
                        </div>
                        
                        <div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#64748b', marginBottom: '6px' }}>
                                <span>Error Budget Remaining</span>
                                <span>{evaluation.error_budget_percent.toFixed(1)}%</span>
                            </div>
                            <div style={{ height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                                <div style={{
                                    height: '100%',
                                    width: `${evaluation.error_budget_percent}%`,
                                    background: getBudgetBarColor(evaluation.error_budget_percent),
                                    transition: 'width 0.3s ease'
                                }} />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SLODashboard;
