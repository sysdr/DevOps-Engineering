// Policy as Code Dashboard JavaScript

const API_BASE = 'http://localhost:5000';

let currentViolations = [];
let currentSeverityFilter = '';
let currentStatusFilter = '';

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Policy as Code Dashboard...');
    loadAll();
    
    // Auto-refresh every 10 seconds
    setInterval(loadAll, 10000);
});

// Load all dashboard data
async function loadAll() {
    try {
        await Promise.all([
            loadMetrics(),
            loadViolations(),
            loadPolicies(),
            loadTrends()
        ]);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Load compliance metrics
async function loadMetrics() {
    try {
        const response = await fetch(`${API_BASE}/api/compliance/metrics`);
        const data = await response.json();
        
        document.getElementById('compliance-rate').textContent = `${data.compliance_rate}%`;
        document.getElementById('total-resources').textContent = data.total_resources;
        document.getElementById('compliant-resources').textContent = `${data.compliant_resources} compliant`;
        document.getElementById('total-violations').textContent = data.total_violations;
        document.getElementById('critical-violations').textContent = `${data.critical_violations} critical`;
        
    } catch (error) {
        console.error('Error loading metrics:', error);
    }
}

// Load violations
async function loadViolations() {
    try {
        let url = `${API_BASE}/api/violations`;
        const params = new URLSearchParams();
        
        if (currentSeverityFilter) params.append('severity', currentSeverityFilter);
        if (currentStatusFilter) params.append('status', currentStatusFilter);
        
        if (params.toString()) url += `?${params.toString()}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        currentViolations = data.violations;
        renderViolations(data.violations);
        
    } catch (error) {
        console.error('Error loading violations:', error);
    }
}

// Render violations list
function renderViolations(violations) {
    const container = document.getElementById('violations-list');
    
    if (violations.length === 0) {
        container.innerHTML = '<div class="loading">No violations found 🎉</div>';
        return;
    }
    
    container.innerHTML = violations.map(v => `
        <div class="violation-item ${v.severity}">
            <div class="violation-header">
                <div>
                    <div class="violation-title">${v.resource_name}</div>
                    <div class="violation-meta">${v.resource_type} • ${v.namespace}</div>
                </div>
                <div class="violation-badges">
                    <span class="badge ${v.severity}">${v.severity}</span>
                    <span class="badge ${v.status}">${v.status}</span>
                </div>
            </div>
            <div class="violation-message">
                <strong>${v.policy_name}:</strong> ${v.message}
            </div>
            <div class="violation-footer">
                <span class="violation-time">Detected ${formatTime(v.detected_at)}</span>
                ${v.remediation_available && v.status === 'open' ? 
                    `<button class="btn btn-remediate" onclick="remediate('${v.id}')">
                        ⚡ Auto Remediate
                    </button>` : ''}
            </div>
        </div>
    `).join('');
}

// Load active policies
async function loadPolicies() {
    try {
        const response = await fetch(`${API_BASE}/api/policies`);
        const data = await response.json();
        
        document.getElementById('active-policies').textContent = data.policies.filter(p => p.status === 'active').length;
        renderPolicies(data.policies);
        
    } catch (error) {
        console.error('Error loading policies:', error);
    }
}

// Render policies list
function renderPolicies(policies) {
    const container = document.getElementById('policies-list');
    
    container.innerHTML = policies.map(p => `
        <div class="policy-item">
            <div class="policy-header">
                <div class="policy-name">${p.name}</div>
                <span class="policy-status ${p.status}">${p.status}</span>
            </div>
            <div class="policy-description">${p.description}</div>
            <div class="policy-stats">
                <span>Severity: <strong>${p.severity}</strong></span>
                <span>Violations: <strong>${p.violations_count}</strong></span>
                <span>Enforcement: <strong>${p.enforcement}</strong></span>
            </div>
        </div>
    `).join('');
}

// Load compliance trends
async function loadTrends() {
    try {
        const response = await fetch(`${API_BASE}/api/compliance/trends?days=7`);
        const data = await response.json();
        
        renderTrendsChart(data.trends);
        
    } catch (error) {
        console.error('Error loading trends:', error);
    }
}

// Render trends chart (simple ASCII-style chart)
function renderTrendsChart(trends) {
    const canvas = document.getElementById('trends-chart');
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = 300;
    
    const width = canvas.width;
    const height = canvas.height;
    const padding = 40;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Draw grid
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    
    for (let i = 0; i <= 5; i++) {
        const y = padding + (height - 2 * padding) * i / 5;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
    }
    
    // Draw axes
    ctx.strokeStyle = '#2d3748';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.stroke();
    
    // Draw compliance line
    const pointSpacing = (width - 2 * padding) / (trends.length - 1);
    
    ctx.strokeStyle = '#48bb78';
    ctx.lineWidth = 3;
    ctx.beginPath();
    
    trends.forEach((trend, i) => {
        const x = padding + i * pointSpacing;
        const y = height - padding - ((trend.compliance_rate / 100) * (height - 2 * padding));
        
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    
    ctx.stroke();
    
    // Draw points
    ctx.fillStyle = '#48bb78';
    trends.forEach((trend, i) => {
        const x = padding + i * pointSpacing;
        const y = height - padding - ((trend.compliance_rate / 100) * (height - 2 * padding));
        
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, 2 * Math.PI);
        ctx.fill();
    });
    
    // Draw labels
    ctx.fillStyle = '#718096';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    
    trends.forEach((trend, i) => {
        const x = padding + i * pointSpacing;
        const label = trend.date.split('-').slice(1).join('/');
        ctx.fillText(label, x, height - padding + 20);
    });
    
    // Draw percentage labels
    ctx.textAlign = 'right';
    for (let i = 0; i <= 5; i++) {
        const y = padding + (height - 2 * padding) * i / 5;
        const value = 100 - (i * 20);
        ctx.fillText(`${value}%`, padding - 10, y + 5);
    }
}

// Filter violations
function filterViolations() {
    currentSeverityFilter = document.getElementById('severity-filter').value;
    currentStatusFilter = document.getElementById('status-filter').value;
    loadViolations();
}

// Trigger remediation
async function remediate(violationId) {
    try {
        const response = await fetch(`${API_BASE}/api/violations/${violationId}/remediate`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Remediation started! The violation will be fixed automatically.');
            await loadViolations();
            await loadMetrics();
        } else {
            alert(`Error: ${data.error}`);
        }
        
    } catch (error) {
        console.error('Error triggering remediation:', error);
        alert('Failed to start remediation. Please try again.');
    }
}

// Run full audit
async function runAudit() {
    try {
        const response = await fetch(`${API_BASE}/api/audit/run`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`Audit scan started!\nScan ID: ${data.scan_id}\nEstimated duration: ${data.estimated_duration}`);
        }
        
    } catch (error) {
        console.error('Error running audit:', error);
        alert('Failed to start audit. Please try again.');
    }
}

// Format timestamp
function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hours ago`;
    return `${Math.floor(diffMins / 1440)} days ago`;
}
