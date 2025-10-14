class GPUDashboard {
    constructor() {
        this.chart = null;
        this.refreshInterval = 3000; // 3 seconds to match monitoring interval
        this.activeWorkloads = new Map();
        this.chartPaused = false;
        this.chartDataBuffer = [];
        this.init();
    }

    async init() {
        await this.initChart();
        await this.loadInitialData();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    async initChart() {
        // Add chart controls
        this.addChartControls();
        
        const ctx = document.getElementById('utilization-chart').getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Average GPU Utilization',
                    data: [],
                    borderColor: 'rgb(139, 92, 246)',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                resizeDelay: 0,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        display: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart'
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                elements: {
                    point: {
                        radius: 4,
                        hoverRadius: 6
                    }
                }
            }
        });
    }

    addChartControls() {
        const chartPanel = document.querySelector('.chart-panel');
        const controlsHTML = `
            <div class="chart-controls">
                <button id="pause-chart" class="chart-control-btn">
                    <span class="control-icon">⏸️</span>
                    <span class="control-text">Pause</span>
                </button>
                <button id="play-chart" class="chart-control-btn" style="display: none;">
                    <span class="control-icon">▶️</span>
                    <span class="control-text">Play</span>
                </button>
                <button id="reset-chart" class="chart-control-btn">
                    <span class="control-icon">🔄</span>
                    <span class="control-text">Reset</span>
                </button>
                <div class="chart-info">
                    <span id="chart-status">Live</span>
                </div>
            </div>
        `;
        
        chartPanel.insertAdjacentHTML('afterbegin', controlsHTML);
        
        // Add event listeners for controls
        document.getElementById('pause-chart').addEventListener('click', () => this.pauseChart());
        document.getElementById('play-chart').addEventListener('click', () => this.playChart());
        document.getElementById('reset-chart').addEventListener('click', () => this.resetChart());
    }

    pauseChart() {
        this.chartPaused = true;
        document.getElementById('pause-chart').style.display = 'none';
        document.getElementById('play-chart').style.display = 'inline-flex';
        document.getElementById('chart-status').textContent = 'Paused';
        document.getElementById('chart-status').style.color = '#f59e0b';
    }

    playChart() {
        this.chartPaused = false;
        document.getElementById('pause-chart').style.display = 'inline-flex';
        document.getElementById('play-chart').style.display = 'none';
        document.getElementById('chart-status').textContent = 'Live';
        document.getElementById('chart-status').style.color = '#10b981';
        
        // Process any buffered data
        if (this.chartDataBuffer.length > 0) {
            this.processBufferedData();
        }
    }

    resetChart() {
        this.chartDataBuffer = [];
        this.chart.data.labels = [];
        this.chart.data.datasets[0].data = [];
        this.chart.update('active');
        this.playChart();
    }

    processBufferedData() {
        if (this.chartDataBuffer.length === 0) return;
        
        // Process all buffered data points
        this.chartDataBuffer.forEach(data => {
            this.updateChart(data);
        });
        this.chartDataBuffer = [];
    }

    async loadInitialData() {
        await Promise.all([
            this.refreshGPUResources(),
            this.refreshMetrics(),
            this.refreshCostAnalysis(),
            this.refreshActiveWorkloads()
        ]);
    }

    setupEventListeners() {
        // Workload form submission
        const form = document.getElementById('workload-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.submitWorkload(e.target);
        });

        // Auto-refresh controls
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else {
                this.startAutoRefresh();
            }
        });
    }

    startAutoRefresh() {
        this.refreshTimer = setInterval(() => {
            this.refreshData();
        }, this.refreshInterval);
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
    }

    async refreshData() {
        try {
            await Promise.all([
                this.refreshGPUResources(),
                this.refreshMetrics(),
                this.refreshCostAnalysis(),
                this.refreshActiveWorkloads()
            ]);
        } catch (error) {
            console.error('Error refreshing dashboard data:', error);
        }
    }

    async refreshGPUResources() {
        try {
            const response = await fetch('/api/gpu/resources');
            const data = await response.json();
            this.renderGPUResources(data.resources);
        } catch (error) {
            console.error('Error fetching GPU resources:', error);
        }
    }

    renderGPUResources(resources) {
        const container = document.getElementById('gpu-resources-container');
        
        if (!resources || resources.length === 0) {
            container.innerHTML = '<p class="text-center">No GPU resources available</p>';
            return;
        }

        container.innerHTML = resources.map(gpu => `
            <div class="gpu-card ${gpu.state}">
                <div class="gpu-header">
                    <div class="gpu-name">${gpu.name} (${gpu.id})</div>
                    <div class="gpu-status ${gpu.state}">${gpu.state}</div>
                </div>
                <div class="gpu-metrics">
                    <div class="metric">
                        <span class="metric-label">Memory:</span>
                        <span class="metric-value">${gpu.memory_used_gb}/${gpu.memory_total_gb} GB</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Utilization:</span>
                        <span class="metric-value">${gpu.utilization_percent.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Temperature:</span>
                        <span class="metric-value">${gpu.temperature_c}°C</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Power:</span>
                        <span class="metric-value">${gpu.power_usage_w}W</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async refreshMetrics() {
        try {
            const response = await fetch('/api/monitoring/metrics');
            const data = await response.json();
            this.updateHeaderStats(data.cluster_stats);
            this.updateChart(data.historical_data);
            this.renderMetrics(data);
        } catch (error) {
            console.error('Error fetching metrics:', error);
        }
    }

    updateHeaderStats(stats) {
        document.getElementById('total-gpus').textContent = stats.total_gpus;
        document.getElementById('avg-utilization').textContent = `${stats.average_utilization}%`;
        
        // Update hourly cost (will be updated from cost analysis)
    }

    updateChart(historicalData) {
        if (!historicalData || historicalData.length === 0) return;

        // If chart is paused, buffer the data instead of updating
        if (this.chartPaused) {
            this.chartDataBuffer.push(historicalData);
            return;
        }

        // Get last 15 data points for better visibility
        const recentData = historicalData.slice(-15);
        
        const labels = recentData.map(item => {
            const time = new Date(item.timestamp);
            return time.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        });
        
        const utilizationData = recentData.map(item => {
            const totalUtil = item.gpus.reduce((sum, gpu) => sum + gpu.utilization, 0);
            return item.gpus.length > 0 ? (totalUtil / item.gpus.length).toFixed(1) : 0;
        });

        // Smooth update - only animate if there's a significant change
        const currentData = this.chart.data.datasets[0].data;
        const lastValue = currentData.length > 0 ? parseFloat(currentData[currentData.length - 1]) : 0;
        const newValue = parseFloat(utilizationData[utilizationData.length - 1]);
        const hasSignificantChange = Math.abs(newValue - lastValue) > 5;

        this.chart.data.labels = labels;
        this.chart.data.datasets[0].data = utilizationData;
        
        // Use smooth animation only for significant changes, otherwise no animation
        this.chart.update(hasSignificantChange ? 'active' : 'none');
    }

    renderMetrics(data) {
        const container = document.getElementById('metrics-container');
        
        if (!data || !data.individual_gpus || data.individual_gpus.length === 0) {
            container.innerHTML = '<p class="text-center">No metrics data available</p>';
            return;
        }

        const clusterStats = data.cluster_stats;
        const gpus = data.individual_gpus;
        
        container.innerHTML = `
            <div class="metrics-summary">
                <div class="metric-card">
                    <div class="metric-icon">🔥</div>
                    <div class="metric-content">
                        <div class="metric-value">${clusterStats.average_temperature}°C</div>
                        <div class="metric-label">Avg Temperature</div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">⚡</div>
                    <div class="metric-content">
                        <div class="metric-value">${clusterStats.total_power_usage}W</div>
                        <div class="metric-label">Total Power</div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">💾</div>
                    <div class="metric-content">
                        <div class="metric-value">${clusterStats.total_memory_used_gb}GB</div>
                        <div class="metric-label">Memory Used</div>
                    </div>
                </div>
            </div>
            
            <div class="gpu-metrics-detailed">
                <h3>Individual GPU Metrics</h3>
                ${gpus.map(gpu => `
                    <div class="gpu-metric-card">
                        <div class="gpu-metric-header">
                            <span class="gpu-name">${gpu.name} (${gpu.id})</span>
                            <span class="gpu-utilization ${this.getUtilizationClass(gpu.utilization)}">
                                ${gpu.utilization.toFixed(1)}%
                            </span>
                        </div>
                        <div class="gpu-metric-details">
                            <div class="metric-row">
                                <span class="metric-name">Memory:</span>
                                <span class="metric-value">${gpu.memory_used_gb}GB</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-name">Temperature:</span>
                                <span class="metric-value">${gpu.temperature}°C</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-name">Power:</span>
                                <span class="metric-value">${gpu.power_usage}W</span>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
            
            <div class="metrics-timestamp">
                <small>Last updated: ${new Date(data.timestamp).toLocaleTimeString()}</small>
            </div>
        `;
    }

    getUtilizationClass(utilization) {
        if (utilization >= 80) return 'high';
        if (utilization >= 50) return 'medium';
        return 'low';
    }

    async refreshCostAnalysis() {
        try {
            const response = await fetch('/api/costs/analysis');
            const data = await response.json();
            this.renderCostAnalysis(data);
            
            // Update header hourly cost
            document.getElementById('hourly-cost').textContent = `$${data.current_hourly_cost}`;
        } catch (error) {
            console.error('Error fetching cost analysis:', error);
        }
    }

    renderCostAnalysis(analysis) {
        const container = document.getElementById('cost-analysis-container');
        
        container.innerHTML = `
            <div class="cost-summary">
                <div class="cost-grid">
                    <div class="cost-item">
                        <span class="cost-value">$${analysis.current_hourly_cost}</span>
                        <span class="cost-label">Hourly</span>
                    </div>
                    <div class="cost-item">
                        <span class="cost-value">$${analysis.projected_daily_cost}</span>
                        <span class="cost-label">Daily</span>
                    </div>
                    <div class="cost-item">
                        <span class="cost-value">$${analysis.projected_monthly_cost}</span>
                        <span class="cost-label">Monthly</span>
                    </div>
                </div>
            </div>
            
            ${analysis.underutilized_gpus.length > 0 ? `
                <div class="alert alert-warning">
                    <strong>Underutilized GPUs:</strong> ${analysis.underutilized_gpus.join(', ')}
                </div>
            ` : ''}
            
            <div class="recommendations">
                <h3>Optimization Recommendations</h3>
                ${analysis.optimization_recommendations.map(rec => `
                    <div class="recommendation">
                        <div class="recommendation-message">${rec.message}</div>
                        ${rec.potential_monthly_savings ? `
                            <div class="recommendation-savings">
                                Potential savings: $${rec.potential_monthly_savings.toFixed(2)}/month
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    async refreshActiveWorkloads() {
        // For demo, we'll show some sample workloads
        // In production, this would fetch from /api/workloads
        this.renderActiveWorkloads([]);
    }

    renderActiveWorkloads(workloads) {
        const container = document.getElementById('active-workloads-container');
        
        if (workloads.length === 0) {
            container.innerHTML = `
                <p class="text-center">No active workloads. Submit a workload to get started!</p>
                <div class="workload-card">
                    <div class="workload-header">
                        <div class="workload-name">Sample: BERT Training</div>
                        <div class="workload-status pending">Demo</div>
                    </div>
                    <div class="workload-details">
                        <div>Type: Training</div>
                        <div>GPUs: 2x A100</div>
                        <div>Duration: 4h</div>
                        <div>Cost: $25.60</div>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = workloads.map(workload => `
            <div class="workload-card">
                <div class="workload-header">
                    <div class="workload-name">${workload.name}</div>
                    <div class="workload-status ${workload.status}">${workload.status}</div>
                </div>
                <div class="workload-details">
                    <div>Type: ${workload.workload_type}</div>
                    <div>GPUs: ${workload.gpu_count}</div>
                    <div>Memory: ${Math.round(workload.gpu_memory_required / (1024**3))}GB</div>
                    <div>Cost: $${workload.cost_estimate.toFixed(2)}</div>
                </div>
            </div>
        `).join('');
    }

    async submitWorkload(form) {
        const submitButton = form.querySelector('.submit-button');
        const originalText = submitButton.textContent;
        
        submitButton.textContent = 'Submitting...';
        submitButton.disabled = true;

        try {
            const formData = new FormData(form);
            const workload = {
                name: formData.get('name'),
                workload_type: formData.get('workload_type'),
                gpu_memory_required: parseInt(formData.get('gpu_memory_gb')) * (1024**3), // Convert GB to bytes
                gpu_count: parseInt(formData.get('gpu_count')),
                max_duration_hours: parseInt(formData.get('max_duration_hours')),
                priority: parseInt(formData.get('priority')),
                framework: formData.get('framework')
            };

            const response = await fetch('/api/workloads/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(workload)
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('Workload submitted successfully!', 'success');
                form.reset();
                await this.refreshActiveWorkloads();
            } else {
                throw new Error(result.detail || 'Submission failed');
            }
        } catch (error) {
            this.showNotification(`Error: ${error.message}`, 'error');
        } finally {
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 2rem;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#06b6d4'};
            color: white;
            border-radius: 0.5rem;
            z-index: 1000;
            box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new GPUDashboard();
});
