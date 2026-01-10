import React, { useState, useEffect } from 'react';

function Recommendations() {
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/optimize/recommendations');
      setRecommendations(response.ok ? await response.json() : []);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div>
      <div className="card">
        <h2>💡 Optimization Recommendations</h2>
        <p style={{color: '#718096', marginBottom: '1.5rem'}}>
          {recommendations.length} opportunities identified for cost savings
        </p>

        {recommendations.map((rec) => (
          <div key={rec.id} className="recommendation-card">
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'start'}}>
              <div style={{flex: 1}}>
                <h3 style={{margin: '0 0 0.5rem 0', color: '#2d3748'}}>
                  {rec.type === 'rightsizing' && '📏 Rightsizing Opportunity'}
                  {rec.type === 'commitment' && '📋 Commitment Optimization'}
                  {rec.type === 'idle_cleanup' && '🧹 Idle Resource Cleanup'}
                  {rec.type === 'storage_optimization' && '💾 Storage Optimization'}
                </h3>
                <p style={{margin: '0.5rem 0', fontWeight: '600'}}>{rec.resource}</p>
                <p style={{color: '#718096', margin: '0.5rem 0'}}>{rec.reason}</p>
                
                {rec.current_cpu && (
                  <div style={{marginTop: '1rem', fontSize: '0.875rem'}}>
                    <p>Current: {rec.current_cpu} CPU, {rec.current_memory} Memory</p>
                    <p>Recommended: {rec.recommended_cpu} CPU, {rec.recommended_memory} Memory</p>
                  </div>
                )}
                
                <div style={{marginTop: '0.5rem'}}>
                  <span className="status-badge success">
                    Confidence: {(rec.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              
              <div style={{textAlign: 'right', marginLeft: '1rem'}}>
                <div className="savings-highlight">
                  ${rec.savings_monthly.toFixed(2)}
                </div>
                <p style={{color: '#718096', fontSize: '0.875rem'}}>monthly savings</p>
              </div>
            </div>
          </div>
        ))}

        <div style={{marginTop: '2rem', padding: '1.5rem', background: '#f7fafc', borderRadius: '8px'}}>
          <h3>Total Potential Savings</h3>
          <div style={{fontSize: '2rem', color: '#38a169', fontWeight: 'bold'}}>
            ${recommendations.reduce((sum, rec) => sum + rec.savings_monthly, 0).toFixed(2)}/month
          </div>
          <p style={{color: '#718096'}}>
            Annual impact: ${(recommendations.reduce((sum, rec) => sum + rec.savings_monthly, 0) * 12).toFixed(2)}
          </p>
        </div>
      </div>
    </div>
  );
}

export default Recommendations;
