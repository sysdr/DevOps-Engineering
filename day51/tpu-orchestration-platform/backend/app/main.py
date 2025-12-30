from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import uvicorn
from datetime import datetime
import json
import logging

from models.job import Job, JobStatus, TPUType
from services.orchestrator import TPUOrchestrator
from services.cost_optimizer import CostOptimizer
from services.monitor import TPUMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
orchestrator = None
cost_optimizer = None
monitor = None

async def initialize_demo_data(orchestrator_instance):
    """Initialize demo data for the dashboard"""
    logger.info("Initializing demo data...")
    
    # Create some completed jobs for demo
    completed_jobs_data = [
        {
            "model_name": "resnet-50",
            "tpu_type": "v4-8",
            "priority": 50,
            "total_steps": 5000,
            "status": JobStatus.COMPLETED,
            "cost_accumulated": 125.50,
            "progress": 100.0,
            "current_step": 5000
        },
        {
            "model_name": "vit-base",
            "tpu_type": "v4-8",
            "priority": 60,
            "total_steps": 3000,
            "status": JobStatus.COMPLETED,
            "cost_accumulated": 89.20,
            "progress": 100.0,
            "current_step": 3000
        },
        {
            "model_name": "efficientnet-b7",
            "tpu_type": "v4-32",
            "priority": 70,
            "total_steps": 2000,
            "status": JobStatus.COMPLETED,
            "cost_accumulated": 245.80,
            "progress": 100.0,
            "current_step": 2000
        }
    ]
    
    for job_data in completed_jobs_data:
        try:
            job = Job(**job_data)
            job.completed_at = datetime.now()
            orchestrator_instance.completed_jobs[job.job_id] = job
            logger.info(f"Demo completed job created: {job.model_name}")
        except Exception as e:
            logger.error(f"Failed to create completed demo job: {e}")
    
    # Create active/queued jobs
    demo_jobs = [
        {
            "model_name": "gpt-large-critical",
            "tpu_type": "v4-8",
            "priority": 90,
            "optimize_cost": True,
            "total_steps": 1000
        },
        {
            "model_name": "bert-base-batch",
            "tpu_type": "v4-32",
            "priority": 30,
            "optimize_cost": True,
            "use_preemptible": True,
            "total_steps": 5000
        },
        {
            "model_name": "roberta-large",
            "tpu_type": "v4-8",
            "priority": 60,
            "optimize_cost": True,
            "total_steps": 2000
        },
        {
            "model_name": "t5-xxl",
            "tpu_type": "v4-8",
            "priority": 40,
            "optimize_cost": True,
            "use_preemptible": True,
            "total_steps": 3000
        },
        {
            "model_name": "whisper-large",
            "tpu_type": "v4-32",
            "priority": 50,
            "optimize_cost": True,
            "total_steps": 1500
        }
    ]
    
    # Submit demo jobs
    for job_data in demo_jobs:
        try:
            job = Job(**job_data)
            await orchestrator_instance.schedule_job(job)
            logger.info(f"Demo job created: {job.model_name}")
        except Exception as e:
            logger.error(f"Failed to create demo job: {e}")
    
    logger.info(f"Created {len(demo_jobs)} active/queued jobs and {len(completed_jobs_data)} completed jobs")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator, cost_optimizer, monitor
    
    # Startup
    logger.info("Initializing TPU Orchestration Platform...")
    orchestrator = TPUOrchestrator()
    cost_optimizer = CostOptimizer(orchestrator)
    monitor = TPUMonitor(orchestrator)
    
    # Set cross-references
    cost_optimizer.set_orchestrator(orchestrator)
    monitor.set_orchestrator(orchestrator)
    
    # Start background tasks
    asyncio.create_task(orchestrator.scheduling_loop())
    asyncio.create_task(monitor.collection_loop())
    
    # Initialize demo data after a short delay to let services start
    await asyncio.sleep(2)
    await initialize_demo_data(orchestrator)
    
    logger.info("✓ Platform initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down platform...")
    await orchestrator.shutdown()

app = FastAPI(title="TPU Orchestration Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "TPU Orchestration Platform",
        "version": "1.0.0",
        "status": "operational",
        "active_jobs": len(orchestrator.active_jobs) if orchestrator else 0
    }

@app.post("/api/jobs")
async def create_job(job_data: dict):
    """Submit new TPU training job"""
    try:
        job = Job(**job_data)
        
        # Cost estimation
        estimated_cost = cost_optimizer.estimate_cost(job)
        
        # Add to orchestrator
        job_id = await orchestrator.schedule_job(job)
        
        return {
            "job_id": job_id,
            "status": "queued",
            "estimated_cost_per_hour": estimated_cost,
            "message": "Job queued for scheduling"
        }
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job status and metrics"""
    job = orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    metrics = monitor.get_job_metrics(job_id)
    
    return {
        "job_id": job_id,
        "status": job.status.value,
        "model": job.model_name,
        "tpu_type": job.tpu_type.value,
        "progress": job.progress,
        "metrics": metrics,
        "cost_so_far": job.cost_accumulated
    }

@app.get("/api/jobs")
async def list_jobs():
    """List all jobs"""
    return {
        "queued": orchestrator.get_queued_jobs(),
        "active": orchestrator.get_active_jobs(),
        "completed": orchestrator.get_completed_jobs()
    }

@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel running job"""
    success = await orchestrator.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or already completed")
    
    return {"message": "Job cancelled successfully"}

@app.get("/api/metrics/cluster")
async def cluster_metrics():
    """Get cluster-wide TPU metrics"""
    return {
        "total_tpus": orchestrator.tpu_resources.total_capacity(),
        "available_tpus": orchestrator.tpu_resources.available_capacity(),
        "utilization": monitor.get_cluster_utilization(),
        "cost_per_hour": cost_optimizer.get_current_cost_rate(),
        "preemption_rate": cost_optimizer.get_preemption_rate()
    }

@app.websocket("/ws/metrics")
async def metrics_websocket(websocket: WebSocket):
    """Real-time metrics stream"""
    await websocket.accept()
    logger.info("Client connected to metrics stream")
    
    try:
        while True:
            try:
                # Ensure services are available
                if not orchestrator or not monitor or not cost_optimizer:
                    logger.warning("Services not initialized yet")
                    try:
                        await websocket.send_json({
                            "timestamp": datetime.now().isoformat(),
                            "jobs": [],
                            "cluster": {"total_utilization": 0.0, "average_mxu": 0.0, "total_flops": 0.0},
                            "cost": {"cost_per_hour": 0.0, "estimated_daily_cost": 0.0, "preemptible_savings": 0.70, "preemption_overhead": 0.05}
                        })
                    except Exception:
                        # Client disconnected
                        break
                    await asyncio.sleep(1)
                    continue
                
                # Gather current metrics
                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "jobs": orchestrator.get_active_jobs(),
                    "cluster": await monitor.get_cluster_metrics(),
                    "cost": cost_optimizer.get_current_metrics()
                }
                
                # Send metrics, catch disconnect errors
                try:
                    await websocket.send_json(metrics)
                except Exception as send_error:
                    # Client disconnected or connection error
                    logger.info(f"Client disconnected during send: {type(send_error).__name__}")
                    break
                    
            except Exception as metrics_error:
                logger.error(f"Error gathering metrics: {metrics_error}", exc_info=True)
                # Try to send error, but if client disconnected, just break
                try:
                    await websocket.send_json({
                        "error": str(metrics_error),
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception:
                    # Client disconnected, exit loop
                    break
            
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("WebSocket connection cancelled")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.info("Client disconnected from metrics stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
