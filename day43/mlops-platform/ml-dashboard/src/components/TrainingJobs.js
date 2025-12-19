import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TrainingJobs = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    experimentName: 'fraud_detection',
    modelType: 'random_forest',
    nEstimators: 100,
    maxDepth: 10
  });

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await axios.get('http://localhost:8000/jobs');
      setJobs(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch jobs');
    }
  };

  const submitJob = async () => {
    setLoading(true);
    try {
      const request = {
        experiment_name: formData.experimentName,
        model_type: formData.modelType,
        hyperparameters: {
          n_estimators: parseInt(formData.nEstimators),
          max_depth: parseInt(formData.maxDepth),
          random_state: 42
        },
        dataset_config: {
          n_samples: 1000,
          n_features: 20
        },
        tags: {
          submitted_by: 'dashboard',
          env: 'development'
        }
      };

      await axios.post('http://localhost:8000/train', request);
      setShowForm(false);
      fetchJobs();
      setError(null);
    } catch (err) {
      setError('Failed to submit training job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>Training Jobs</h2>
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ New Training Job'}
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {showForm && (
          <div style={{ marginTop: '1.5rem', padding: '1.5rem', background: 'rgba(102, 126, 234, 0.05)', borderRadius: '12px' }}>
            <h3 style={{ marginBottom: '1rem' }}>Submit Training Job</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#4b5563' }}>Experiment Name</label>
                <input
                  type="text"
                  value={formData.experimentName}
                  onChange={(e) => setFormData({ ...formData, experimentName: e.target.value })}
                  style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #d1d5db' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#4b5563' }}>Model Type</label>
                <select
                  value={formData.modelType}
                  onChange={(e) => setFormData({ ...formData, modelType: e.target.value })}
                  style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #d1d5db' }}
                >
                  <option value="random_forest">Random Forest</option>
                  <option value="gradient_boosting">Gradient Boosting</option>
                  <option value="logistic_regression">Logistic Regression</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#4b5563' }}>N Estimators</label>
                <input
                  type="number"
                  value={formData.nEstimators}
                  onChange={(e) => setFormData({ ...formData, nEstimators: e.target.value })}
                  style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #d1d5db' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#4b5563' }}>Max Depth</label>
                <input
                  type="number"
                  value={formData.maxDepth}
                  onChange={(e) => setFormData({ ...formData, maxDepth: e.target.value })}
                  style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #d1d5db' }}
                />
              </div>
            </div>
            <button
              className="btn btn-primary"
              onClick={submitJob}
              disabled={loading}
              style={{ marginTop: '1rem' }}
            >
              {loading ? 'Submitting...' : 'Submit Job'}
            </button>
          </div>
        )}

        <div style={{ marginTop: '2rem' }}>
          <table>
            <thead>
              <tr>
                <th>Job ID</th>
                <th>Status</th>
                <th>Created At</th>
                <th>Metrics</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.job_id}>
                  <td><code>{job.job_id.substring(0, 8)}</code></td>
                  <td>
                    <span className={`status-badge status-${job.status}`}>
                      {job.status}
                    </span>
                  </td>
                  <td>{new Date(job.created_at).toLocaleString()}</td>
                  <td>
                    {job.metrics && Object.keys(job.metrics).length > 0 ? (
                      <div style={{ fontSize: '0.85rem' }}>
                        Accuracy: {(job.metrics.accuracy * 100).toFixed(1)}%
                      </div>
                    ) : (
                      '-'
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {jobs.length === 0 && (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>
              No training jobs yet. Submit your first job!
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TrainingJobs;
