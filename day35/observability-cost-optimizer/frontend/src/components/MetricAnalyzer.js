import React, { useState } from 'react';

function MetricAnalyzer() {
  const [analysis, setAnalysis] = useState(null);
  const [formData, setFormData] = useState({
    service: 'api-gateway',
    metric_name: 'http_requests_total',
    cardinality: 500,
    samples_per_second: 50,
    data_size_mb: 10
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('http://localhost:8000/api/metrics/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      setAnalysis(data);
    } catch (error) {
      console.error('Error analyzing metric:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: isNaN(value) ? value : Number(value)
    }));
  };

  return (
    <div className="analyzer">
      <h2>Metric Cost Analyzer</h2>
      <p className="description">
        Analyze the cost impact of your metrics. High cardinality = more time series = higher costs.
      </p>

      <form onSubmit={handleSubmit} className="analyzer-form">
        <div className="form-group">
          <label>Service Name</label>
          <input
            type="text"
            name="service"
            value={formData.service}
            onChange={handleChange}
            placeholder="e.g., api-gateway"
          />
        </div>

        <div className="form-group">
          <label>Metric Name</label>
          <input
            type="text"
            name="metric_name"
            value={formData.metric_name}
            onChange={handleChange}
            placeholder="e.g., http_requests_total"
          />
        </div>

        <div className="form-group">
          <label>Cardinality (unique time series)</label>
          <input
            type="number"
            name="cardinality"
            value={formData.cardinality}
            onChange={handleChange}
            placeholder="e.g., 500"
          />
          <small>Product of all label values (service × endpoint × region × ...)</small>
        </div>

        <div className="form-group">
          <label>Samples per Second</label>
          <input
            type="number"
            name="samples_per_second"
            value={formData.samples_per_second}
            onChange={handleChange}
            step="0.1"
            placeholder="e.g., 50"
          />
        </div>

        <div className="form-group">
          <label>Estimated Data Size (MB/month)</label>
          <input
            type="number"
            name="data_size_mb"
            value={formData.data_size_mb}
            onChange={handleChange}
            step="0.1"
            placeholder="e.g., 10"
          />
        </div>

        <button type="submit" className="analyze-button">
          Analyze Cost Impact
        </button>
      </form>

      {analysis && (
        <div className="analysis-result">
          <h3>Cost Analysis Results</h3>
          
          <div className="result-grid">
            <div className="result-card">
              <div className="result-label">Time Series Count</div>
              <div className="result-value">{analysis.time_series_count.toLocaleString()}</div>
              <div className={`result-badge ${analysis.cardinality_impact.toLowerCase()}`}>
                {analysis.cardinality_impact}
              </div>
            </div>

            <div className="result-card">
              <div className="result-label">Hot Storage Cost</div>
              <div className="result-value">${analysis.hot_storage_cost}</div>
              <div className="result-sublabel">7 days, instant queries</div>
            </div>

            <div className="result-card">
              <div className="result-label">Warm Storage Cost</div>
              <div className="result-value">${analysis.warm_storage_cost}</div>
              <div className="result-sublabel">30 days, slower queries</div>
            </div>

            <div className="result-card">
              <div className="result-label">Ingestion Cost</div>
              <div className="result-value">${analysis.ingestion_cost}</div>
              <div className="result-sublabel">Processing pipeline</div>
            </div>

            <div className="result-card highlight">
              <div className="result-label">Total Monthly Cost</div>
              <div className="result-value large">${analysis.total_monthly_cost}</div>
            </div>
          </div>

          {analysis.cardinality_impact === 'HIGH' && (
            <div className="warning-box">
              <strong>⚠️ High Cardinality Warning</strong>
              <p>This metric creates {analysis.time_series_count} time series. Consider:</p>
              <ul>
                <li>Removing unnecessary labels</li>
                <li>Using recording rules for aggregations</li>
                <li>Implementing label value limits</li>
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default MetricAnalyzer;
