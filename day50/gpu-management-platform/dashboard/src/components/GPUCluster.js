import React from 'react';
import './GPUCluster.css';

function GPUCluster({ gpus }) {
  return (
    <div className="gpu-cluster">
      <h2>GPU Cluster Status</h2>
      <div className="gpu-grid">
        {gpus.map(gpu => (
          <div key={gpu.gpu_id} className="gpu-card">
            <div className="gpu-header">
              <h3>GPU {gpu.gpu_id}</h3>
              <div className={`status-badge ${gpu.mig_enabled ? 'mig-enabled' : 'full-gpu'}`}>
                {gpu.mig_enabled ? 'MIG' : 'Full'}
              </div>
            </div>
            
            <div className="gpu-info">
              <div className="info-row">
                <span className="info-label">Model:</span>
                <span className="info-value">{gpu.name.substring(0, 25)}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Memory:</span>
                <span className="info-value">{(gpu.total_memory / 1024).toFixed(0)} GB</span>
              </div>
              <div className="info-row">
                <span className="info-label">Utilization:</span>
                <span className="info-value">{gpu.utilization.toFixed(1)}%</span>
              </div>
              <div className="info-row">
                <span className="info-label">Temperature:</span>
                <span className="info-value">{gpu.temperature}°C</span>
              </div>
            </div>

            <div className="utilization-bar">
              <div 
                className="utilization-fill"
                style={{ width: `${gpu.utilization}%` }}
              />
            </div>

            {gpu.mig_enabled && gpu.mig_instances.length > 0 && (
              <div className="mig-instances">
                <h4>MIG Instances ({gpu.mig_instances.length})</h4>
                <div className="instance-grid">
                  {gpu.mig_instances.map(instance => (
                    <div 
                      key={instance.id} 
                      className={`instance-badge ${instance.allocated ? 'allocated' : 'free'}`}
                    >
                      <div className="instance-profile">{instance.profile}</div>
                      <div className="instance-status">
                        {instance.allocated ? `${instance.utilization.toFixed(0)}%` : 'Free'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default GPUCluster;
