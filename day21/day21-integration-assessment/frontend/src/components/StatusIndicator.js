import React from 'react';

const StatusIndicator = ({ title, status, description }) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'active': return '🟢';
      case 'running': return '🔄';
      case 'completed': return '✅';
      case 'failed': return '❌';
      case 'warning': return '⚠️';
      default: return '⚪';
    }
  };

  const getStatusText = () => {
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  return (
    <div className={`status-indicator ${status}`}>
      <div className="status-icon">{getStatusIcon()}</div>
      <div className="status-content">
        <h3>{title}</h3>
        <p className="status-text">{getStatusText()}</p>
        <p className="status-description">{description}</p>
      </div>
    </div>
  );
};

export default StatusIndicator;
