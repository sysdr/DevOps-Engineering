import React, { useState, useEffect } from 'react';
import axios from 'axios';

const GovernanceWorkflow = () => {
  const [modelId, setModelId] = useState('');
  const [owner, setOwner] = useState('');
  const [status, setStatus] = useState(null);
  const [pendingReviews, setPendingReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const fetchPendingReviews = async () => {
    try {
      const response = await axios.get('http://localhost:8004/api/v1/governance/pending');
      setPendingReviews(response.data.workflows);
    } catch (err) {
      console.error('Failed to fetch pending reviews:', err);
      setError(err.response?.data?.detail || 'Failed to load pending reviews.');
    }
  };

  useEffect(() => {
    fetchPendingReviews();
    const interval = setInterval(fetchPendingReviews, 30000);
    return () => clearInterval(interval);
  }, []);

  const submitModel = async () => {
    setError(null);
    setSuccess(null);

    if (!modelId.trim() || !owner.trim()) {
      setError('Please enter model ID and owner email.');
      return;
    }

    const emailPattern = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
    if (!emailPattern.test(owner.trim())) {
      setError('Please enter a valid owner email.');
      return;
    }

    setLoading(true);
    setStatus(null);
    try {
      await axios.post('http://localhost:8004/api/v1/governance/submit', {
        model_id: modelId.trim(),
        owner: owner.trim()
      });

      // Simulate bias analysis, then update governance state
      setTimeout(async () => {
        try {
          const biasResult = await axios.post('http://localhost:8001/api/v1/bias/analyze', {
            model_id: modelId.trim(),
            dataset_id: 'test-dataset-1'
          });

          await axios.post(
            `http://localhost:8004/api/v1/governance/bias-result?model_id=${modelId.trim()}&passed=${biasResult.data.passed}`
          );
          
          const statusResponse = await axios.get(`http://localhost:8004/api/v1/governance/status/${modelId.trim()}`);
          setStatus(statusResponse.data);
          setSuccess('Model submitted and bias analysis completed.');
          fetchPendingReviews();
        } catch (err) {
          setError(err.response?.data?.detail || 'Failed to complete bias analysis.');
        } finally {
          setLoading(false);
        }
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit model.');
      setLoading(false);
    }
  };

  const submitReview = async (modelId, decision) => {
    try {
      await axios.post('http://localhost:8004/api/v1/governance/review', {
        model_id: modelId,
        reviewer: 'reviewer@company.com',
        decision: decision,
        comments: `${decision} by automated demo`
      });

      const statusResponse = await axios.get(`http://localhost:8004/api/v1/governance/status/${modelId}`);
      setStatus(statusResponse.data);
      fetchPendingReviews();
    } catch (err) {
      alert('Failed to submit review: ' + err.message);
    }
  };

  const getStateColor = (state) => {
    if (state.includes('pending')) return '#ffa94d';
    if (state === 'approved') return '#51cf66';
    if (state === 'rejected') return '#ff6b6b';
    return '#667eea';
  };

  return (
    <div>
      <h2 className="section-title">Governance Workflow Management</h2>

      <div className="card">
        <h3>Submit New Model for Review</h3>
        {error && (
          <div className="error" style={{ marginBottom: '10px' }}>
            {error}
          </div>
        )}
        {success && (
          <div className="success" style={{ marginBottom: '10px' }}>
            {success}
          </div>
        )}
        <div style={{ marginBottom: '15px' }}>
          <input
            type="text"
            value={modelId}
            onChange={(e) => setModelId(e.target.value)}
            placeholder="Model ID (e.g., fraud-detection-v1)"
            style={{
              width: '250px',
              padding: '10px',
              fontSize: '1em',
              borderRadius: '6px',
              border: '2px solid #dee2e6',
              marginRight: '10px'
            }}
          />
          <input
            type="text"
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
            placeholder="Owner Email"
            style={{
              width: '250px',
              padding: '10px',
              fontSize: '1em',
              borderRadius: '6px',
              border: '2px solid #dee2e6',
              marginRight: '10px'
            }}
          />
          <button className="btn" onClick={submitModel} disabled={loading}>
            {loading ? 'Submitting...' : 'Submit Model'}
          </button>
        </div>

        {status && (
          <div style={{ marginTop: '20px', padding: '15px', background: '#f8f9fa', borderRadius: '6px' }}>
            <h4>Model Status: {status.model_id}</h4>
            <div style={{ 
              display: 'inline-block',
              padding: '8px 16px',
              background: getStateColor(status.current_state),
              color: 'white',
              borderRadius: '20px',
              fontWeight: 'bold',
              marginTop: '10px'
            }}>
              {status.current_state.replace(/_/g, ' ').toUpperCase()}
            </div>

            <div style={{ marginTop: '15px' }}>
              <h5>Workflow History:</h5>
              {status.history.map((event, idx) => (
                <div key={idx} style={{ padding: '8px', borderLeft: '3px solid #667eea', marginLeft: '10px', marginTop: '5px' }}>
                  <strong>{event.state}</strong> - {event.actor} - {new Date(event.timestamp).toLocaleString()}
                </div>
              ))}
            </div>

            {status.current_state.includes('pending') && (
              <div style={{ marginTop: '15px' }}>
                <button 
                  className="btn" 
                  onClick={() => submitReview(status.model_id, 'approve')}
                  style={{ marginRight: '10px', background: '#51cf66' }}
                >
                  Approve
                </button>
                <button 
                  className="btn"
                  onClick={() => submitReview(status.model_id, 'reject')}
                  style={{ background: '#ff6b6b' }}
                >
                  Reject
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card">
        <h3>Pending Reviews ({pendingReviews.length})</h3>
        {pendingReviews.length === 0 ? (
          <p style={{ color: '#6c757d' }}>No pending reviews</p>
        ) : (
          <div>
            {pendingReviews.map((workflow, idx) => (
              <div key={idx} style={{ padding: '15px', background: '#f8f9fa', borderRadius: '6px', marginBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong>{workflow.model_id}</strong>
                    <div style={{ fontSize: '0.9em', color: '#6c757d', marginTop: '5px' }}>
                      Submitted by: {workflow.submitted_by} | Updated: {new Date(workflow.updated_at).toLocaleString()}
                    </div>
                  </div>
                  <div style={{
                    padding: '6px 12px',
                    background: getStateColor(workflow.state),
                    color: 'white',
                    borderRadius: '15px',
                    fontSize: '0.85em',
                    fontWeight: 'bold'
                  }}>
                    {workflow.state.replace(/_/g, ' ')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default GovernanceWorkflow;
