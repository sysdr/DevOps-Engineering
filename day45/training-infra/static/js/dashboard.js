let ws;
let trainingChart;

function initWebSocket() {
    ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateDashboard(data);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting...');
        setTimeout(initWebSocket, 3000);
    };
}

function updateDashboard(data) {
    updateResources(data.resources);
    updateMetrics(data.metrics);
    updateJobs(data.jobs);
    updateTrainingChart(data.jobs);
}

function updateResources(resources) {
    const html = `
        <div class="metric">
            <span class="metric-label">Total GPUs</span>
            <span class="metric-value">${resources.total_gpus}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Available GPUs</span>
            <span class="metric-value">${resources.available_gpus}</span>
        </div>
        <div class="metric">
            <span class="metric-label">GPU Utilization</span>
            <span class="metric-value">${resources.utilization.toFixed(1)}%</span>
        </div>
        <div class="metric">
            <span class="metric-label">Active Jobs</span>
            <span class="metric-value">${resources.active_jobs}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Queued Jobs</span>
            <span class="metric-value">${resources.queued_jobs}</span>
        </div>
    `;
    document.getElementById('resources').innerHTML = html;
}

function updateMetrics(metrics) {
    const html = `
        <div class="metric">
            <span class="metric-label">CPU Usage</span>
            <span class="metric-value">${metrics.cpu.toFixed(1)}%</span>
        </div>
        <div class="metric">
            <span class="metric-label">Memory Used</span>
            <span class="metric-value">${metrics.memory.used.toFixed(2)} GB</span>
        </div>
        <div class="metric">
            <span class="metric-label">Memory Available</span>
            <span class="metric-value">${metrics.memory.available.toFixed(2)} GB</span>
        </div>
        <div class="metric">
            <span class="metric-label">Disk Used</span>
            <span class="metric-value">${metrics.disk.percent.toFixed(1)}%</span>
        </div>
    `;
    document.getElementById('metrics').innerHTML = html;
}

function updateJobs(jobs) {
    if (!jobs || jobs.length === 0) {
        document.getElementById('jobs').innerHTML = '<p>No training jobs</p>';
        return;
    }
    
    const html = jobs.map(job => `
        <div class="job-item">
            <div class="job-header">
                <span class="job-id">Job ${job.job_id}</span>
                <span class="job-status status-${job.status}">${job.status.toUpperCase()}</span>
            </div>
            <div class="job-metrics">
                <div class="job-metric">
                    <strong>Model:</strong> ${job.model_type}
                </div>
                <div class="job-metric">
                    <strong>Epochs:</strong> ${job.current_epoch}/${job.epochs}
                </div>
                <div class="job-metric">
                    <strong>GPUs:</strong> ${job.allocated_gpus}
                </div>
            </div>
            ${job.current_epoch > 0 ? `
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(job.current_epoch / job.epochs * 100)}%"></div>
                </div>
            ` : ''}
            ${job.metrics && job.metrics.length > 0 ? `
                <div class="job-metric" style="margin-top: 10px;">
                    <strong>Latest Loss:</strong> ${job.metrics[job.metrics.length - 1].loss.toFixed(4)}
                    <strong>Accuracy:</strong> ${(job.metrics[job.metrics.length - 1].accuracy * 100).toFixed(2)}%
                </div>
            ` : ''}
        </div>
    `).join('');
    
    document.getElementById('jobs').innerHTML = html;
}

async function submitJob() {
    const config = {
        model_type: 'resnet18',
        epochs: 20,
        batch_size: 64,
        learning_rate: 0.001,
        num_gpus: 2,
        priority: 5
    };
    
    // Show submitting message
    alert('Submitting Job...');
    
    try {
        const response = await fetch('/api/jobs', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(config)
        });
        
        if (!response.ok) {
            // Handle HTTP error responses
            let errorMessage = 'Failed to submit training job';
            try {
                const errorData = await response.json();
                if (errorData.detail) {
                    errorMessage = `Error: ${errorData.detail}`;
                } else if (errorData.message) {
                    errorMessage = `Error: ${errorData.message}`;
                } else {
                    errorMessage = `Error: ${response.status} ${response.statusText}`;
                }
            } catch (parseError) {
                // If response is not JSON, use status text
                errorMessage = `Error: ${response.status} ${response.statusText || 'Unknown error'}`;
            }
            alert(errorMessage);
            console.error('Job submission failed:', errorMessage);
            return;
        }
        
        const result = await response.json();
        console.log('Job submitted:', result);
        
        if (result.job_id) {
            alert(`✅ Training job ${result.job_id} submitted successfully!`);
        } else if (result.status === 'success' && result.job_id) {
            alert(`✅ Training job ${result.job_id} submitted successfully!`);
        } else {
            alert('⚠️ Job submitted but response format unexpected');
        }
    } catch (error) {
        // Handle network errors or other exceptions
        let errorMessage = 'Failed to submit training job';
        
        if (error instanceof TypeError && error.message.includes('fetch')) {
            errorMessage = '❌ Network error: Unable to connect to the server. Please check if the server is running.';
        } else if (error.message) {
            errorMessage = `❌ Error: ${error.message}`;
        } else {
            errorMessage = '❌ An unexpected error occurred while submitting the job.';
        }
        
        alert(errorMessage);
        console.error('Error submitting job:', error);
    }
}

async function refreshData() {
    try {
        const response = await fetch('/api/jobs');
        const data = await response.json();
        updateJobs(data.jobs);
        updateTrainingChart(data.jobs);
        
        const resourcesResp = await fetch('/api/resources');
        const resources = await resourcesResp.json();
        updateResources(resources);
        
        const metricsResp = await fetch('/api/metrics');
        const metrics = await metricsResp.json();
        updateMetrics(metrics);
    } catch (error) {
        console.error('Error refreshing data:', error);
    }
}

function initTrainingChart() {
    const ctx = document.getElementById('trainingChart').getContext('2d');
    trainingChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Loss / Accuracy'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Epoch'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

function updateTrainingChart(jobs) {
    if (!trainingChart) {
        initTrainingChart();
    }
    
    // Filter active training jobs
    const activeJobs = jobs.filter(job => 
        job.status === 'training' || job.status === 'checkpointing' || job.status === 'initializing'
    );
    
    if (activeJobs.length === 0) {
        trainingChart.data.labels = [];
        trainingChart.data.datasets = [];
        trainingChart.update();
        return;
    }
    
    // Get all unique epochs across all jobs
    const allEpochs = new Set();
    activeJobs.forEach(job => {
        if (job.metrics && job.metrics.length > 0) {
            job.metrics.forEach(metric => allEpochs.add(metric.epoch));
        }
    });
    const sortedEpochs = Array.from(allEpochs).sort((a, b) => a - b);
    
    // Create datasets for each job
    const datasets = [];
    const colors = [
        { loss: 'rgba(255, 99, 132, 1)', accuracy: 'rgba(54, 162, 235, 1)' },
        { loss: 'rgba(255, 159, 64, 1)', accuracy: 'rgba(75, 192, 192, 1)' },
        { loss: 'rgba(153, 102, 255, 1)', accuracy: 'rgba(201, 203, 207, 1)' },
        { loss: 'rgba(255, 205, 86, 1)', accuracy: 'rgba(255, 99, 255, 1)' }
    ];
    
    activeJobs.forEach((job, index) => {
        const colorSet = colors[index % colors.length];
        
        // Loss dataset
        const lossData = sortedEpochs.map(epoch => {
            const metric = job.metrics.find(m => m.epoch === epoch);
            return metric ? metric.loss : null;
        });
        
        datasets.push({
            label: `Job ${job.job_id} - Loss`,
            data: lossData,
            borderColor: colorSet.loss,
            backgroundColor: colorSet.loss.replace('1)', '0.2)'),
            yAxisID: 'y',
            tension: 0.4,
            pointRadius: 3,
            pointHoverRadius: 5
        });
        
        // Accuracy dataset
        const accuracyData = sortedEpochs.map(epoch => {
            const metric = job.metrics.find(m => m.epoch === epoch);
            return metric ? metric.accuracy * 100 : null; // Convert to percentage
        });
        
        datasets.push({
            label: `Job ${job.job_id} - Accuracy (%)`,
            data: accuracyData,
            borderColor: colorSet.accuracy,
            backgroundColor: colorSet.accuracy.replace('1)', '0.2)'),
            yAxisID: 'y',
            tension: 0.4,
            pointRadius: 3,
            pointHoverRadius: 5
        });
    });
    
    trainingChart.data.labels = sortedEpochs;
    trainingChart.data.datasets = datasets;
    trainingChart.update('none'); // 'none' mode for smooth updates
}

// Initialize on page load
window.addEventListener('load', () => {
    initTrainingChart();
    initWebSocket();
    refreshData();
});
