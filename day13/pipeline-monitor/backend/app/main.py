from fastapi import FastAPI, WebSocket, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import json
import time
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import redis
import uuid

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    asyncio.create_task(generate_demo_builds())
    yield
    # Shutdown
    pass

app = FastAPI(title="Pipeline Performance Monitor", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Global storage for demo purposes
metrics_store = {}
active_builds = {}
performance_history = []

class MetricsCollector:
    def __init__(self):
        self.start_time = None
        self.metrics = {}
        
    def start_build(self, build_id: str, pipeline_name: str):
        self.start_time = time.time()
        self.metrics = {
            'build_id': build_id,
            'pipeline_name': pipeline_name,
            'start_time': self.start_time,
            'cpu_samples': [],
            'memory_samples': [],
            'disk_io': [],
            'network_io': [],
            'cache_stats': {'hits': 0, 'misses': 0},
            'stages': {},
            'status': 'running'
        }
        active_builds[build_id] = self.metrics
        return self.metrics
    
    def collect_sample(self, build_id: str):
        if build_id not in active_builds:
            return None
            
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        net_io = psutil.net_io_counters()
        
        sample = {
            'timestamp': time.time(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': memory.used / (1024**3),
            'disk_read_mb': disk_io.read_bytes / (1024**2) if disk_io else 0,
            'disk_write_mb': disk_io.write_bytes / (1024**2) if disk_io else 0,
            'network_sent_mb': net_io.bytes_sent / (1024**2) if net_io else 0,
            'network_recv_mb': net_io.bytes_recv / (1024**2) if net_io else 0
        }
        
        active_builds[build_id]['cpu_samples'].append(sample['cpu_percent'])
        active_builds[build_id]['memory_samples'].append(sample['memory_percent'])
        
        return sample
    
    def finish_build(self, build_id: str, success: bool = True):
        if build_id not in active_builds:
            return None
            
        build_metrics = active_builds[build_id]
        build_metrics['end_time'] = time.time()
        build_metrics['duration'] = build_metrics['end_time'] - build_metrics['start_time']
        build_metrics['status'] = 'success' if success else 'failed'
        build_metrics['avg_cpu'] = sum(build_metrics['cpu_samples']) / len(build_metrics['cpu_samples']) if build_metrics['cpu_samples'] else 0
        build_metrics['max_cpu'] = max(build_metrics['cpu_samples']) if build_metrics['cpu_samples'] else 0
        build_metrics['avg_memory'] = sum(build_metrics['memory_samples']) / len(build_metrics['memory_samples']) if build_metrics['memory_samples'] else 0
        build_metrics['max_memory'] = max(build_metrics['memory_samples']) if build_metrics['memory_samples'] else 0
        
        # Calculate cost (simplified model: $0.01 per minute + resource usage)
        base_cost = (build_metrics['duration'] / 60) * 0.01
        resource_cost = (build_metrics['avg_cpu'] / 100) * 0.005
        build_metrics['estimated_cost'] = round(base_cost + resource_cost, 4)
        
        # Store in history
        performance_history.append(build_metrics.copy())
        metrics_store[build_id] = build_metrics
        
        # Remove from active builds
        del active_builds[build_id]
        
        return build_metrics

collector = MetricsCollector()

@app.get("/")
async def root():
    return {"message": "Pipeline Performance Monitor API", "status": "running"}

@app.post("/api/builds/start")
async def start_build(build_request: dict):
    build_id = build_request.get('build_id', str(uuid.uuid4()))
    pipeline_name = build_request.get('pipeline_name', 'default-pipeline')
    
    metrics = collector.start_build(build_id, pipeline_name)
    return {"build_id": build_id, "status": "started", "metrics": metrics}

@app.post("/api/builds/{build_id}/finish")
async def finish_build(build_id: str, result: dict):
    success = result.get('success', True)
    metrics = collector.finish_build(build_id, success)
    return {"build_id": build_id, "status": "finished", "metrics": metrics}

@app.get("/api/builds/{build_id}/metrics")
async def get_build_metrics(build_id: str):
    if build_id in active_builds:
        return active_builds[build_id]
    elif build_id in metrics_store:
        return metrics_store[build_id]
    else:
        return {"error": "Build not found"}

@app.get("/api/builds/active")
async def get_active_builds():
    return {"active_builds": list(active_builds.keys()), "count": len(active_builds)}

@app.get("/api/metrics/summary")
async def get_metrics_summary():
    if not performance_history:
        return {"message": "No builds completed yet"}
    
    total_builds = len(performance_history)
    successful_builds = len([b for b in performance_history if b['status'] == 'success'])
    failed_builds = total_builds - successful_builds
    
    durations = [b['duration'] for b in performance_history]
    costs = [b['estimated_cost'] for b in performance_history]
    
    summary = {
        "total_builds": total_builds,
        "success_rate": round((successful_builds / total_builds) * 100, 2),
        "failed_builds": failed_builds,
        "avg_duration": round(sum(durations) / len(durations), 2),
        "min_duration": round(min(durations), 2),
        "max_duration": round(max(durations), 2),
        "total_cost": round(sum(costs), 4),
        "avg_cost_per_build": round(sum(costs) / len(costs), 4),
        "builds_last_24h": len([b for b in performance_history if b['start_time'] > time.time() - 86400])
    }
    
    return summary

@app.get("/api/metrics/trends")
async def get_performance_trends():
    if len(performance_history) < 2:
        return {"message": "Insufficient data for trends"}
    
    recent_builds = performance_history[-10:]  # Last 10 builds
    
    trends = {
        "build_times": [{"build_id": b['build_id'], "duration": b['duration'], "timestamp": b['start_time']} for b in recent_builds],
        "resource_usage": [{"build_id": b['build_id'], "avg_cpu": b['avg_cpu'], "max_memory": b['max_memory']} for b in recent_builds],
        "costs": [{"build_id": b['build_id'], "cost": b['estimated_cost'], "timestamp": b['start_time']} for b in recent_builds]
    }
    
    return trends

@app.websocket("/ws/metrics")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Send real-time metrics for active builds
            active_metrics = {}
            for build_id in active_builds:
                sample = collector.collect_sample(build_id)
                if sample:
                    active_metrics[build_id] = sample
            
            if active_metrics:
                await websocket.send_text(json.dumps({
                    "type": "metrics_update",
                    "data": active_metrics,
                    "timestamp": time.time()
                }))
            
            await asyncio.sleep(2)  # Update every 2 seconds
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Background task to generate demo builds
async def generate_demo_builds():
    while True:
        if len(active_builds) < 2:  # Keep 1-2 demo builds running
            build_id = f"demo-{int(time.time())}"
            collector.start_build(build_id, f"demo-pipeline-{len(performance_history) % 3 + 1}")
            
            # Simulate build duration (10-60 seconds)
            build_duration = 10 + (len(performance_history) % 50)
            await asyncio.sleep(build_duration)
            
            # Finish with random success/failure
            success = (len(performance_history) % 10) != 0  # 90% success rate
            collector.finish_build(build_id, success)
        
        await asyncio.sleep(5)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
