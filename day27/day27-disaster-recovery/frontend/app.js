const API_BASE = 'http://localhost:8000';

async function fetchBackups() {
    try {
        const response = await fetch(`${API_BASE}/api/backups`);
        const data = await response.json();
        displayBackups(data.backups);
    } catch (error) {
        console.error('Error fetching backups:', error);
    }
}

function displayBackups(backups) {
    const container = document.getElementById('backup-list');
    
    if (backups.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: #a0aec0;">No backups yet. Create your first backup!</div>';
        return;
    }
    
    container.innerHTML = backups.map(backup => `
        <div class="backup-item">
            <div class="backup-header">
                <span class="backup-name">${backup.name}</span>
                <span class="backup-status status-${backup.status}">${backup.status}</span>
            </div>
            <div class="backup-details">
                <span>📦 ${backup.resources_count} resources</span>
                <span>💾 ${formatBytes(backup.size_bytes)}</span>
                <span>🕐 ${formatDate(backup.created_at)}</span>
            </div>
        </div>
    `).join('');
}

async function fetchReplicationStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/replication/status`);
        const data = await response.json();
        updateReplicationStatus(data);
    } catch (error) {
        console.error('Error fetching replication status:', error);
    }
}

function updateReplicationStatus(status) {
    document.getElementById('primary-region').textContent = status.primary_region;
    document.getElementById('dr-region').textContent = status.dr_region;
    document.getElementById('replication-lag').textContent = `${status.lag_seconds}s`;
    document.getElementById('last-sync').textContent = formatDate(status.last_sync);
}

async function fetchMetrics() {
    try {
        const response = await fetch(`${API_BASE}/api/metrics`);
        const data = await response.json();
        document.getElementById('backup-success').textContent = `${(data.backup_success_rate * 100).toFixed(1)}%`;
        document.getElementById('restore-success').textContent = `${(data.restore_success_rate * 100).toFixed(1)}%`;
    } catch (error) {
        console.error('Error fetching metrics:', error);
    }
}

async function createBackup() {
    const name = prompt('Enter backup name:', `backup-${Date.now()}`);
    if (!name) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/backups`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                namespaces: ['default', 'production'],
                type: 'full'
            })
        });
        
        if (response.ok) {
            alert('✅ Backup created successfully!');
            fetchBackups();
        }
    } catch (error) {
        alert('❌ Error creating backup: ' + error.message);
    }
}

async function triggerFailover() {
    if (!confirm('⚠️ Are you sure you want to trigger failover? This will switch traffic to the DR region.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/failover`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_region: 'us-west-2' })
        });
        
        const data = await response.json();
        if (response.ok) {
            alert(`✅ Failover completed in ${data.total_duration_ms}ms`);
            fetchReplicationStatus();
        }
    } catch (error) {
        alert('❌ Error triggering failover: ' + error.message);
    }
}

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Initialize
fetchBackups();
fetchReplicationStatus();
fetchMetrics();

// Refresh data every 5 seconds
setInterval(() => {
    fetchBackups();
    fetchReplicationStatus();
    fetchMetrics();
}, 5000);
