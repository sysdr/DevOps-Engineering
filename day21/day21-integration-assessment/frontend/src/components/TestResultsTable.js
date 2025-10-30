import React from 'react';

const TestResultsTable = ({ results }) => {
  const getStatusBadge = (status) => {
    const badges = {
      passed: '✅ Passed',
      failed: '❌ Failed',
      running: '🔄 Running',
      pending: '⏳ Pending'
    };
    return badges[status] || status;
  };

  return (
    <div className="test-results-table">
      <h3>Test Results</h3>
      <table>
        <thead>
          <tr>
            <th>Test Name</th>
            <th>Status</th>
            <th>Duration</th>
            <th>Timestamp</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          {results.map(result => (
            <tr key={result.id} className={result.status}>
              <td>{result.name}</td>
              <td>
                <span className={`status-badge ${result.status}`}>
                  {getStatusBadge(result.status)}
                </span>
              </td>
              <td>{result.duration}s</td>
              <td>{new Date(result.timestamp).toLocaleTimeString()}</td>
              <td>{result.details}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TestResultsTable;
