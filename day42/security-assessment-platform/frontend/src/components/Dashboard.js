import React from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './Dashboard.css';

const COLORS = ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#3b82f6', '#ec4899'];

function Dashboard({ data }) {
  // Add safety checks for undefined/null data
  if (!data) {
    return <div className="dashboard">Loading...</div>;
  }

  const { security_score, components, compliance } = data;

  // Prepare component scores for chart
  const componentChartData = components ? Object.entries(components).map(([name, comp]) => ({
    name: name.replace(/_/g, ' ').toUpperCase(),
    score: comp.total_score || 0,
    max: comp.max_score || 100
  })) : [];

  // Prepare compliance data
  const complianceData = compliance ? [
    { name: 'SOC 2', score: compliance.soc2?.compliance_score || 0 },
    { name: 'ISO 27001', score: compliance.iso27001?.compliance_score || 0 },
    { name: 'CIS', score: compliance.cis?.compliance_score || 0 }
  ] : [];

  // Calculate risk distribution
  const calculateRiskDistribution = () => {
    let critical = 0, high = 0, medium = 0, low = 0;
    
    if (components) {
      Object.values(components).forEach(comp => {
        if (comp.tests) {
          comp.tests.forEach(test => {
            if (test.score < 60) critical++;
            else if (test.score < 75) high++;
            else if (test.score < 90) medium++;
            else low++;
          });
        }
      });
    }

    return [
      { name: 'Critical', value: critical, color: '#ef4444' },
      { name: 'High', value: high, color: '#f59e0b' },
      { name: 'Medium', value: medium, color: '#eab308' },
      { name: 'Low', value: low, color: '#10b981' }
    ];
  };

  const riskData = calculateRiskDistribution();

  const getScoreColor = (score) => {
    if (score >= 90) return '#10b981';
    if (score >= 80) return '#3b82f6';
    if (score >= 70) return '#f59e0b';
    return '#ef4444';
  };

  // Safety check for security_score
  if (!security_score) {
    return <div className="dashboard">Loading...</div>;
  }

  return (
    <div className="dashboard">
      {/* Security Score Card */}
      <div className="score-card" style={{ borderColor: getScoreColor(security_score.total_score) }}>
        <h2>Security Posture Score</h2>
        <div className="score-display">
          <span className="score-value" style={{ color: getScoreColor(security_score.total_score) }}>
            {security_score.total_score}
          </span>
          <span className="score-grade">{security_score.grade}</span>
        </div>
        <div className="score-status">{security_score.status?.replace(/_/g, ' ').toUpperCase() || 'N/A'}</div>
      </div>

      {/* Component Scores */}
      <div className="section">
        <h2>Component Security Scores</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={componentChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Bar dataKey="score" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Risk Distribution */}
      <div className="section">
        <h2>Risk Distribution</h2>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={riskData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value }) => `${name}: ${value}`}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {riskData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Compliance Status */}
      {compliance && (
        <div className="section">
          <h2>Compliance Status</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={complianceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Bar dataKey="score" fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Component Details */}
      <div className="section">
        <h2>Detailed Test Results</h2>
        {components ? Object.entries(components).map(([name, comp]) => (
          <div key={name} className="component-detail">
            <h3>{name.replace(/_/g, ' ').toUpperCase()}</h3>
            <div className="component-score">
              Score: {comp.total_score}/{comp.max_score} ({((comp.total_score/comp.max_score)*100).toFixed(1)}%)
            </div>
            {comp.tests && (
              <div className="test-list">
                {comp.tests.map((test, idx) => (
                  <div key={idx} className={`test-item ${test.status}`}>
                    <div className="test-header">
                      <span className="test-name">{test.name}</span>
                      <span className={`test-status ${test.status}`}>
                        {test.status === 'passed' ? '✅' : '⚠️'} {test.status}
                      </span>
                    </div>
                    <div className="test-description">{test.description}</div>
                    <div className="test-details">{test.details}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )) : <div>No component data available</div>}
      </div>

      {/* Compliance Details */}
      {compliance && (
        <div className="section">
          <h2>Compliance Framework Details</h2>
          {Object.entries(compliance || {}).map(([framework, data]) => (
            <div key={framework} className="compliance-detail">
              <h3>{data.framework}</h3>
              <div className="compliance-score">
                Compliance Score: {data.compliance_score}% - {data.status.toUpperCase()}
              </div>
              <div className="control-list">
                {data.controls?.map((control, idx) => (
                  <div key={idx} className={`control-item ${control.status}`}>
                    <span className="control-id">{control.id}</span>
                    <span className="control-name">{control.name}</span>
                    <span className={`control-status ${control.status}`}>
                      {control.status === 'pass' ? '✅' : '❌'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Dashboard;
