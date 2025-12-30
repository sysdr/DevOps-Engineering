from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import httpx
import logging
from datetime import datetime
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GPU Scheduler")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobRequest(BaseModel):
    job_id: str
    memory_required: int  # MB
    can_use_spot: bool = False
    priority: str = "normal"  # low, normal, high
    checkpoint_enabled: bool = False

class SchedulingDecision(BaseModel):
    job_id: str
    gpu_id: Optional[int]
    mig_instance_id: Optional[str]
    node_type: str  # "mig", "full-gpu", "spot"
    estimated_cost_per_hour: float

class ClusterState(BaseModel):
    total_gpus: int
    available_gpus: int
    mig_instances_total: int
    mig_instances_available: int
    spot_nodes_available: int

MIG_CONTROLLER_URL = "http://localhost:8001"
COST_OPTIMIZER_URL = "http://localhost:8003"

# Cost constants (per hour)
COST_MIG_1G = 0.50
COST_MIG_2G = 1.00
COST_MIG_3G = 1.50
COST_FULL_GPU = 3.50
COST_SPOT_GPU = 1.40

scheduled_jobs: Dict[str, SchedulingDecision] = {}

@app.on_event("startup")
async def startup():
    logger.info("GPU Scheduler started")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "gpu-scheduler"}

@app.get("/cluster/state", response_model=ClusterState)
async def get_cluster_state():
    """Get current cluster state"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MIG_CONTROLLER_URL}/gpus", timeout=5.0)
            gpus = response.json()
            
            total_gpus = len(gpus)
            mig_instances_total = sum(len(gpu["mig_instances"]) for gpu in gpus)
            mig_instances_available = sum(
                len([inst for inst in gpu["mig_instances"] if not inst["allocated"]])
                for gpu in gpus
            )
            
            return ClusterState(
                total_gpus=total_gpus,
                available_gpus=sum(1 for gpu in gpus if not gpu["mig_enabled"]),
                mig_instances_total=mig_instances_total,
                mig_instances_available=mig_instances_available,
                spot_nodes_available=2  # Simulated
            )
    except Exception as e:
        logger.error(f"Failed to get cluster state: {e}")
        return ClusterState(
            total_gpus=4,
            available_gpus=2,
            mig_instances_total=0,
            mig_instances_available=0,
            spot_nodes_available=2
        )

@app.post("/schedule", response_model=SchedulingDecision)
async def schedule_job(job: JobRequest):
    """Schedule a job on the most appropriate GPU resource"""
    logger.info(f"Scheduling job {job.job_id} with {job.memory_required}MB memory")
    
    try:
        # Get available GPUs and MIG instances
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MIG_CONTROLLER_URL}/gpus", timeout=5.0)
            gpus = response.json()
        
        # Strategy 1: Try MIG instances for small jobs (< 10GB)
        if job.memory_required < 10240:
            for gpu in gpus:
                if gpu["mig_enabled"]:
                    for instance in gpu["mig_instances"]:
                        if not instance["allocated"] and instance["memory"] >= job.memory_required:
                            # Allocate this instance
                            async with httpx.AsyncClient() as client:
                                await client.post(
                                    f"{MIG_CONTROLLER_URL}/gpu/{gpu['gpu_id']}/mig/instance/{instance['id']}/allocate",
                                    timeout=5.0
                                )
                            
                            decision = SchedulingDecision(
                                job_id=job.job_id,
                                gpu_id=gpu["gpu_id"],
                                mig_instance_id=instance["id"],
                                node_type="mig",
                                estimated_cost_per_hour=COST_MIG_1G if instance["memory"] <= 5120 else COST_MIG_2G
                            )
                            scheduled_jobs[job.job_id] = decision
                            logger.info(f"Scheduled {job.job_id} on MIG instance {instance['id']}")
                            return decision
        
        # Strategy 2: Use spot instances for interruptible jobs
        if job.can_use_spot and job.checkpoint_enabled:
            decision = SchedulingDecision(
                job_id=job.job_id,
                gpu_id=None,
                mig_instance_id=None,
                node_type="spot",
                estimated_cost_per_hour=COST_SPOT_GPU
            )
            scheduled_jobs[job.job_id] = decision
            logger.info(f"Scheduled {job.job_id} on spot instance")
            return decision
        
        # Strategy 3: Full GPU on-demand
        for gpu in gpus:
            if not gpu["mig_enabled"] and gpu["utilization"] < 20.0:
                decision = SchedulingDecision(
                    job_id=job.job_id,
                    gpu_id=gpu["gpu_id"],
                    mig_instance_id=None,
                    node_type="full-gpu",
                    estimated_cost_per_hour=COST_FULL_GPU
                )
                scheduled_jobs[job.job_id] = decision
                logger.info(f"Scheduled {job.job_id} on full GPU {gpu['gpu_id']}")
                return decision
        
        raise HTTPException(status_code=503, detail="No GPU resources available")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scheduling failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scheduling failed: {str(e)}")

@app.get("/jobs")
async def list_scheduled_jobs():
    """List all scheduled jobs"""
    return {"jobs": list(scheduled_jobs.values())}

@app.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """Remove a scheduled job"""
    if job_id in scheduled_jobs:
        del scheduled_jobs[job_id]
        return {"message": "Job removed", "job_id": job_id}
    raise HTTPException(status_code=404, detail="Job not found")

@app.get("/metrics")
async def get_metrics():
    """Get scheduler metrics"""
    total_jobs = len(scheduled_jobs)
    mig_jobs = sum(1 for j in scheduled_jobs.values() if j.node_type == "mig")
    spot_jobs = sum(1 for j in scheduled_jobs.values() if j.node_type == "spot")
    full_gpu_jobs = sum(1 for j in scheduled_jobs.values() if j.node_type == "full-gpu")
    
    return {
        "total_jobs_scheduled": total_jobs,
        "mig_jobs": mig_jobs,
        "spot_jobs": spot_jobs,
        "full_gpu_jobs": full_gpu_jobs,
        "avg_cost_per_hour": sum(j.estimated_cost_per_hour for j in scheduled_jobs.values()) / max(total_jobs, 1)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
