import React from 'react';
import './SchedulerMetrics.css';

function SchedulerMetrics({ metrics }) {
  const totalJobs = metrics.total_jobs_scheduled || 0;
  const migPct = totalJobs > 0 ? (metrics.mig_jobs / totalJobs * 100) : 0;
  const spotPct = totalJobs > 0 ? (metrics.spot_jobs / totalJobs * 100) : 0;
  const fullGpuPct = totalJobs > 0 ? (metrics.full_gpu_jobs / totalJobs * 100) : 0;

  return (
    <div className="scheduler-metrics">
      <h2>Scheduler Performance</h2>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon">📊</div>
          <div className="metric-value">{totalJobs}</div>
          <div className="metric-label">Total Jobs Scheduled</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-icon">💰</div>
          <div className="metric-value">${metrics.avg_cost_per_hour?.toFixed(2) || '0.00'}</div>
          <div className="metric-label">Avg Cost/Hour</div>
        </div>
      </div>

      <div className="job-distribution">
        <h3>Job Distribution by Resource Type</h3>
        <div className="distribution-bars">
          <div className="dist-bar">
            <div className="dist-header">
              <span className="dist-label">MIG Instances</span>
              <span className="dist-count">{metrics.mig_jobs} jobs ({migPct.toFixed(0)}%)</span>
            </div>
            <div className="dist-visual">
              <div className="dist-fill mig" style={{ width: `${migPct}%` }}></div>
            </div>
          </div>

          <div className="dist-bar">
            <div className="dist-header">
              <span className="dist-label">Spot Instances</span>
              <span className="dist-count">{metrics.spot_jobs} jobs ({spotPct.toFixed(0)}%)</span>
            </div>
            <div className="dist-visual">
              <div className="dist-fill spot" style={{ width: `${spotPct}%` }}></div>
            </div>
          </div>

          <div className="dist-bar">
            <div className="dist-header">
              <span className="dist-label">Full GPUs</span>
              <span className="dist-count">{metrics.full_gpu_jobs} jobs ({fullGpuPct.toFixed(0)}%)</span>
            </div>
            <div className="dist-visual">
              <div className="dist-fill full" style={{ width: `${fullGpuPct}%` }}></div>
            </div>
          </div>
        </div>
      </div>

      <div className="scheduler-insights">
        <h3>💡 Scheduler Insights</h3>
        <div className="insight-grid">
          <div className="insight-card">
            <div className="insight-title">Cost Efficiency</div>
            <div className="insight-text">
              {migPct > 50 
                ? `Excellent! ${migPct.toFixed(0)}% of jobs using cost-effective MIG instances`
                : `${spotPct > 30 
                    ? `Good spot usage at ${spotPct.toFixed(0)}%`
                    : 'Consider enabling MIG for smaller workloads'}`
              }
            </div>
          </div>
          <div className="insight-card">
            <div className="insight-title">Resource Utilization</div>
            <div className="insight-text">
              {totalJobs > 10 
                ? 'High cluster utilization - consider auto-scaling'
                : 'Cluster capacity available for new workloads'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SchedulerMetrics;
