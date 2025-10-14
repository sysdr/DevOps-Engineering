from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from typing import Dict, List, Optional
import asyncio
import json
from datetime import datetime
import os

from .gpu_manager import GPUManager
from .scheduler import GPUScheduler
from .monitoring import GPUMonitor
from .models import WorkloadRequest, WorkloadStatus, GPUResource

app = FastAPI(
    title="GPU Orchestration Platform",
    description="Production-ready GPU resource orchestration with NVIDIA operators",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Initialize components
gpu_manager = GPUManager()
scheduler = GPUScheduler(gpu_manager)
monitor = GPUMonitor()

@app.on_event("startup")
async def startup_event():
    """Initialize GPU discovery and monitoring"""
    await gpu_manager.initialize()
    await monitor.start_monitoring()
    await scheduler.start_scheduler()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main GPU orchestration dashboard"""
    with open("web/src/dashboard.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/api/gpu/resources")
async def get_gpu_resources():
    """Get available GPU resources and their current status"""
    try:
        resources = await gpu_manager.get_available_resources()
        return {"resources": resources, "timestamp": datetime.utcnow()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch GPU resources: {str(e)}")

@app.post("/api/workloads/submit")
async def submit_workload(request: WorkloadRequest, background_tasks: BackgroundTasks):
    """Submit AI/ML workload for GPU scheduling"""
    try:
        workload_id = await scheduler.submit_workload(request)
        background_tasks.add_task(scheduler.process_workload, workload_id)
        return {"workload_id": workload_id, "status": "submitted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Workload submission failed: {str(e)}")

@app.get("/api/workloads/{workload_id}/status")
async def get_workload_status(workload_id: str):
    """Get current status of submitted workload"""
    status = await scheduler.get_workload_status(workload_id)
    if not status:
        raise HTTPException(status_code=404, detail="Workload not found")
    return status

@app.get("/api/monitoring/metrics")
async def get_metrics():
    """Get real-time GPU utilization and performance metrics"""
    metrics = await monitor.collect_metrics()
    return metrics

@app.get("/api/costs/analysis")
async def get_cost_analysis():
    """Get GPU cost analysis and optimization recommendations"""
    analysis = await monitor.analyze_costs()
    return analysis

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
