from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import psutil
import boto3
import json
import asyncio
from datetime import datetime
import os
from pathlib import Path

app = FastAPI(title="DevOps Foundation API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# System monitoring endpoints
@app.get("/api/system/metrics")
async def get_system_metrics():
    """Get real-time system performance metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "usage_percent": cpu_percent,
                "count": psutil.cpu_count(),
                "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/aws/costs")
async def get_aws_costs():
    """Simulate AWS cost allocation data"""
    return {
        "timestamp": datetime.now().isoformat(),
        "total_cost": 1247.83,
        "services": {
            "EC2": {"cost": 542.10, "instances": 12, "hours": 8760},
            "RDS": {"cost": 234.50, "instances": 3, "hours": 8760},
            "S3": {"cost": 67.23, "storage_gb": 2340, "requests": 1250000},
            "CloudWatch": {"cost": 89.45, "metrics": 450, "logs_gb": 150},
            "Load Balancer": {"cost": 156.78, "lb_count": 4, "hours": 8760},
            "NAT Gateway": {"cost": 125.67, "gateways": 2, "data_gb": 890},
            "CloudTrail": {"cost": 32.10, "events": 560000, "data_gb": 45}
        },
        "cost_by_team": {
            "Platform": 423.15,
            "Backend": 398.22,
            "Frontend": 156.78,
            "Data": 234.50,
            "DevOps": 35.18
        }
    }

@app.get("/api/infrastructure/status")
async def get_infrastructure_status():
    """Get infrastructure component status"""
    return {
        "timestamp": datetime.now().isoformat(),
        "vpc": {
            "id": "vpc-12345678",
            "status": "available",
            "subnets": 6,
            "route_tables": 4,
            "security_groups": 8
        },
        "ec2_instances": [
            {"id": "i-1234567890abcdef0", "type": "t3.medium", "state": "running", "az": "us-west-2a"},
            {"id": "i-1234567890abcdef1", "type": "t3.medium", "state": "running", "az": "us-west-2b"},
            {"id": "i-1234567890abcdef2", "type": "t3.large", "state": "running", "az": "us-west-2c"}
        ],
        "load_balancers": [
            {"name": "web-alb", "type": "application", "state": "active", "targets": 3}
        ],
        "security_compliance": {
            "score": 94,
            "passed_checks": 47,
            "failed_checks": 3,
            "last_scan": datetime.now().isoformat()
        }
    }

@app.get("/api/performance/tuning")
async def get_performance_status():
    """Get Linux performance tuning status"""
    return {
        "timestamp": datetime.now().isoformat(),
        "kernel_parameters": {
            "net.core.somaxconn": {"current": 65535, "recommended": 65535, "tuned": True},
            "net.ipv4.tcp_max_syn_backlog": {"current": 65535, "recommended": 65535, "tuned": True},
            "vm.swappiness": {"current": 10, "recommended": 10, "tuned": True},
            "fs.file-max": {"current": 2097152, "recommended": 2097152, "tuned": True}
        },
        "processes": {
            "total": len(psutil.pids()),
            "running": len([p for p in psutil.process_iter() if p.status() == 'running']),
            "sleeping": len([p for p in psutil.process_iter() if p.status() == 'sleeping'])
        },
        "optimization_score": 92
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
