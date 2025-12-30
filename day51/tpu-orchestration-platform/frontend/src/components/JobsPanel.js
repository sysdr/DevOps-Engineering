import React from 'react';

function JobsPanel({ jobs }) {
  return (
    <div className="panel">
      <h2>Training Jobs</h2>
      
      <div className="jobs-section">
        <h3>Active ({jobs.active?.length || 0})</h3>
        {jobs.active?.map(job => (
          <div key={job.job_id} className="job-card active">
            <div className="job-header">
              <span className="job-model">{job.model}</span>
              <span className="job-status">{job.status}</span>
            </div>
            <div className="job-details">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${job.progress}%` }}
                />
              </div>
              <div className="job-info">
                <span>TPU: {job.tpu_pod}</span>
                <span>Cost: ${job.cost?.toFixed(2)}</span>
              </div>
            </div>
          </div>
        )) || <p className="empty">No active jobs</p>}
      </div>

      <div className="jobs-section">
        <h3>Queued ({jobs.queued?.length || 0})</h3>
        {jobs.queued?.slice(0, 5).map(job => (
          <div key={job.job_id} className="job-card queued">
            <span className="job-model">{job.model}</span>
            <span className="job-priority">Priority: {job.priority}</span>
          </div>
        )) || <p className="empty">No queued jobs</p>}
      </div>

      <div className="jobs-section">
        <h3>Completed (Last 5)</h3>
        {jobs.completed?.slice(0, 5).map(job => (
          <div key={job.job_id} className="job-card completed">
            <span className="job-model">{job.model}</span>
            <span className="job-cost">${job.cost?.toFixed(2)}</span>
          </div>
        )) || <p className="empty">No completed jobs</p>}
      </div>
    </div>
  );
}

export default JobsPanel;
