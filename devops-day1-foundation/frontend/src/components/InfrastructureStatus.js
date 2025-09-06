import React, { useState, useEffect } from 'react';

const InfrastructureStatus = () => {
  const [infrastructure, setInfrastructure] = useState(null);

  useEffect(() => {
    const fetchInfrastructure = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/infrastructure/status');
        const data = await response.json();
        setInfrastructure(data);
      } catch (error) {
        console.error('Error fetching infrastructure:', error);
      }
    };

    fetchInfrastructure();
    const interval = setInterval(fetchInfrastructure, 15000);
    return () => clearInterval(interval);
  }, []);

  if (!infrastructure) return <div className="loading">Loading infrastructure status...</div>;

  return (
    <div className="infrastructure-container">
      <div className="infrastructure-grid">
        <div className="infra-card">
          <h3>VPC Configuration</h3>
          <div className="infra-details">
            <p><strong>VPC ID:</strong> {infrastructure.vpc.id}</p>
            <p><strong>Status:</strong> <span className="status-badge available">{infrastructure.vpc.status}</span></p>
            <p><strong>Subnets:</strong> {infrastructure.vpc.subnets}</p>
            <p><strong>Route Tables:</strong> {infrastructure.vpc.route_tables}</p>
            <p><strong>Security Groups:</strong> {infrastructure.vpc.security_groups}</p>
          </div>
        </div>
        
        <div className="infra-card">
          <h3>EC2 Instances</h3>
          <div className="instance-list">
            {infrastructure.ec2_instances.map((instance) => (
              <div key={instance.id} className="instance-item">
                <div className="instance-id">{instance.id}</div>
                <div className="instance-meta">
                  <span className="instance-type">{instance.type}</span>
                  <span className="instance-state">{instance.state}</span>
                  <span className="az">{instance.az}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="infra-card">
          <h3>Load Balancers</h3>
          <div className="lb-list">
            {infrastructure.load_balancers.map((lb) => (
              <div key={lb.name} className="lb-item">
                <div className="lb-name">{lb.name}</div>
                <div className="lb-meta">
                  <span className="lb-type">{lb.type}</span>
                  <span className="lb-state">{lb.state}</span>
                  <span className="targets">Targets: {lb.targets}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="infra-card">
          <h3>Security Compliance</h3>
          <div className="compliance-score">
            <div className="score-circle">
              <span className="score">{infrastructure.security_compliance.score}</span>
            </div>
            <div className="compliance-details">
              <p>✅ Passed: {infrastructure.security_compliance.passed_checks}</p>
              <p>❌ Failed: {infrastructure.security_compliance.failed_checks}</p>
              <p>Last Scan: {new Date(infrastructure.security_compliance.last_scan).toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InfrastructureStatus;
