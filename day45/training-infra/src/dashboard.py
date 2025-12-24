from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, List
import asyncio
import json
import logging
import os
from pathlib import Path
from src.orchestrator import orchestrator
from src.monitor import SystemMonitor
from src.scheduler import ResourceScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the project root directory (parent of src directory)
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Training Infrastructure Dashboard")

# Mount static files with absolute path
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# WebSocket connections
active_connections: List[WebSocket] = []

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve dashboard HTML"""
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.post("/api/jobs")
async def submit_job(config: Dict):
    """Submit new training job"""
    try:
        # Validate required fields
        if not isinstance(config, dict):
            raise HTTPException(status_code=400, detail="Invalid request: config must be a JSON object")
        
        # Validate num_gpus
        num_gpus = config.get('num_gpus', 1)
        if not isinstance(num_gpus, int) or num_gpus < 1:
            raise HTTPException(status_code=400, detail="Invalid num_gpus: must be a positive integer")
        if num_gpus > orchestrator.available_gpus:
            raise HTTPException(status_code=400, detail=f"Insufficient GPUs: requested {num_gpus}, but only {orchestrator.available_gpus} available")
        
        # Validate epochs
        epochs = config.get('epochs', 10)
        if not isinstance(epochs, int) or epochs < 1:
            raise HTTPException(status_code=400, detail="Invalid epochs: must be a positive integer")
        
        # Validate batch_size
        batch_size = config.get('batch_size', 64)
        if not isinstance(batch_size, int) or batch_size < 1:
            raise HTTPException(status_code=400, detail="Invalid batch_size: must be a positive integer")
        
        # Validate learning_rate
        learning_rate = config.get('learning_rate', 0.001)
        if not isinstance(learning_rate, (int, float)) or learning_rate <= 0:
            raise HTTPException(status_code=400, detail="Invalid learning_rate: must be a positive number")
        
        job = orchestrator.submit_job(config)
        return {"status": "success", "job_id": job.job_id, "job": job.__dict__}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job status"""
    job_status = orchestrator.get_job_status(job_id)
    if job_status:
        return job_status
    raise HTTPException(status_code=404, detail="Job not found")

@app.get("/api/jobs")
async def list_jobs():
    """List all jobs"""
    return {"jobs": orchestrator.get_all_jobs()}

@app.get("/api/resources")
async def get_resources():
    """Get resource usage"""
    return orchestrator.get_resource_usage()

@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics"""
    return SystemMonitor.get_system_metrics()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Send updates every second
            await asyncio.sleep(1)
            
            data = {
                'jobs': orchestrator.get_all_jobs(),
                'resources': orchestrator.get_resource_usage(),
                'metrics': SystemMonitor.get_system_metrics()
            }
            
            await websocket.send_json(data)
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("WebSocket disconnected")

@app.on_event("startup")
async def startup_event():
    """Start orchestrator scheduler"""
    asyncio.create_task(orchestrator.schedule_jobs())
    logger.info("Training orchestrator started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
