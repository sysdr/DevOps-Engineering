import React from 'react';

const MetricsCard = ({ title, value, subtitle, trend, color }) => {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up': return '📈';
      case 'down': return '📉';
      case 'stable': return '➡️';
      default: return '';
    }
  };

  return (
    <div className={`metrics-card ${color}`}>
      <div className="metrics-header">
        <h3>{title}</h3>
        <span className="trend-icon">{getTrendIcon()}</span>
      </div>
      <div className="metrics-value">{value}</div>
      <div className="metrics-subtitle">{subtitle}</div>
    </div>
  );
};

export default MetricsCard;
