#!/bin/bash

# Linux Performance Tuning Script for High-Scale Applications
# This script optimizes kernel parameters for high-concurrency workloads

echo "🔧 Starting Linux performance tuning..."

# Backup original sysctl configuration
sudo cp /etc/sysctl.conf /etc/sysctl.conf.backup.20250906_200404

# Network optimizations
echo "📡 Applying network optimizations..."

# Increase maximum number of connections
echo "net.core.somaxconn = 65535" | sudo tee -a /etc/sysctl.conf

# Increase network buffer sizes
echo "net.core.rmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
echo "net.core.netdev_max_backlog = 30000" | sudo tee -a /etc/sysctl.conf

# TCP optimizations
echo "net.ipv4.tcp_max_syn_backlog = 65535" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_rmem = 4096 87380 16777216" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_wmem = 4096 65536 16777216" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_fin_timeout = 30" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_keepalive_time = 600" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_keepalive_intvl = 60" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_keepalive_probes = 3" | sudo tee -a /etc/sysctl.conf

# Memory management optimizations
echo "💾 Applying memory optimizations..."

# Reduce swappiness (prefer RAM over swap)
echo "vm.swappiness = 10" | sudo tee -a /etc/sysctl.conf

# Increase file descriptor limits
echo "fs.file-max = 2097152" | sudo tee -a /etc/sysctl.conf

# Virtual memory optimizations
echo "vm.dirty_ratio = 15" | sudo tee -a /etc/sysctl.conf
echo "vm.dirty_background_ratio = 5" | sudo tee -a /etc/sysctl.conf

# Security optimizations
echo "🔒 Applying security optimizations..."

# Disable IP forwarding (if not needed)
echo "net.ipv4.ip_forward = 0" | sudo tee -a /etc/sysctl.conf

# Enable SYN flood protection
echo "net.ipv4.tcp_syncookies = 1" | sudo tee -a /etc/sysctl.conf

# Ignore ICMP ping requests
echo "net.ipv4.icmp_echo_ignore_all = 1" | sudo tee -a /etc/sysctl.conf

# Apply all changes
sudo sysctl -p

# Update limits.conf for user processes
echo "👤 Updating user limits..."

sudo tee -a /etc/security/limits.conf << EOL

# DevOps Foundation - High Performance Limits
* soft nofile 1048576
* hard nofile 1048576
* soft nproc 1048576
* hard nproc 1048576
* soft memlock unlimited
* hard memlock unlimited
EOL

# Create monitoring script
cat > /tmp/system-monitor.py << 'PYTHON_EOF'
#!/usr/bin/env python3
import psutil
import time
import json
from datetime import datetime

def get_system_metrics():
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0],
        "network_connections": len(psutil.net_connections()),
        "processes": len(psutil.pids())
    }

if __name__ == "__main__":
    while True:
        metrics = get_system_metrics()
        print(json.dumps(metrics, indent=2))
        time.sleep(5)
PYTHON_EOF

chmod +x /tmp/system-monitor.py

echo "✅ Linux performance tuning completed!"
echo "📊 Run 'python3 /tmp/system-monitor.py' to monitor system performance"
echo "🔄 Reboot recommended to ensure all changes take effect"
