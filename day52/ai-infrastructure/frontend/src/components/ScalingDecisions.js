import React, { useState, useEffect } from 'react';

function ScalingDecisions() {
  const [decisions, setDecisions] = useState([]);

  useEffect(() => {
    fetchDecisions();
    const interval = setInterval(fetchDecisions, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDecisions = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/scaling/decisions?hours=24');
      const data = await response.json();
      setDecisions(data.slice(0, 10));
    } catch (error) {
      console.error('Error fetching decisions:', error);
    }
  };

  return (
    <div className="scaling-decisions">
      {decisions.length === 0 ? (
        <div className="no-data">No scaling decisions yet</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Deployment</th>
              <th>Scaling</th>
              <th>Predicted Load</th>
              <th>Reason</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {decisions.map(decision => (
              <tr key={decision.id}>
                <td>{new Date(decision.timestamp).toLocaleTimeString()}</td>
                <td>{decision.deployment}</td>
                <td>
                  <span className="scaling-arrow">
                    {decision.current_replicas} → {decision.target_replicas}
                  </span>
                </td>
                <td>{decision.predicted_load.toFixed(1)}%</td>
                <td className="reason-cell">{decision.reason}</td>
                <td>
                  <span className={decision.executed ? 'executed' : 'pending'}>
                    {decision.executed ? '✓ Executed' : 'Pending'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default ScalingDecisions;
