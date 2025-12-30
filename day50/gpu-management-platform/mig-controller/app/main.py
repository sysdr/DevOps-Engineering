from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import json
from typing import List, Dict, Optional
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MIG Controller")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MIGProfile(BaseModel):
    profile: str  # e.g., "1g.5gb", "2g.10gb", "3g.20gb", "7g.80gb"
    instances: int

class MIGConfiguration(BaseModel):
    gpu_id: int
    profiles: List[MIGProfile]

class GPUStatus(BaseModel):
    gpu_id: int
    name: str
    total_memory: int
    mig_enabled: bool
    mig_instances: List[Dict]
    utilization: float
    temperature: int

# Simulated MIG configuration store
mig_configs: Dict[int, List[Dict]] = {}
gpu_inventory = {}

def initialize_gpu_inventory():
    """Initialize GPU inventory simulation"""
    global gpu_inventory
    # Simulate 4 NVIDIA A100 GPUs
    for i in range(4):
        gpu_inventory[i] = {
            "id": i,
            "name": "NVIDIA A100-SXM4-80GB",
            "total_memory": 81920,  # 80GB in MB
            "mig_enabled": False,
            "mig_instances": [],
            "utilization": 0.0,
            "temperature": 35 + (i * 2),
            "power_usage": 150 + (i * 10)
        }

initialize_gpu_inventory()

@app.on_event("startup")
async def startup():
    logger.info("MIG Controller started")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mig-controller"}

@app.get("/gpus", response_model=List[GPUStatus])
async def list_gpus():
    """List all GPUs and their current MIG configuration"""
    return [
        GPUStatus(
            gpu_id=gpu["id"],
            name=gpu["name"],
            total_memory=gpu["total_memory"],
            mig_enabled=gpu["mig_enabled"],
            mig_instances=gpu["mig_instances"],
            utilization=gpu["utilization"],
            temperature=gpu["temperature"]
        )
        for gpu in gpu_inventory.values()
    ]

@app.post("/gpu/{gpu_id}/mig/enable")
async def enable_mig(gpu_id: int):
    """Enable MIG mode on GPU"""
    if gpu_id not in gpu_inventory:
        raise HTTPException(status_code=404, detail="GPU not found")
    
    gpu = gpu_inventory[gpu_id]
    if gpu["mig_enabled"]:
        return {"message": "MIG already enabled", "gpu_id": gpu_id}
    
    gpu["mig_enabled"] = True
    logger.info(f"MIG enabled on GPU {gpu_id}")
    
    return {"message": "MIG enabled successfully", "gpu_id": gpu_id}

@app.post("/gpu/{gpu_id}/mig/disable")
async def disable_mig(gpu_id: int):
    """Disable MIG mode on GPU"""
    if gpu_id not in gpu_inventory:
        raise HTTPException(status_code=404, detail="GPU not found")
    
    gpu = gpu_inventory[gpu_id]
    gpu["mig_enabled"] = False
    gpu["mig_instances"] = []
    mig_configs[gpu_id] = []
    
    logger.info(f"MIG disabled on GPU {gpu_id}")
    return {"message": "MIG disabled successfully", "gpu_id": gpu_id}

@app.post("/gpu/{gpu_id}/mig/configure")
async def configure_mig(gpu_id: int, config: MIGConfiguration):
    """Configure MIG instances on GPU"""
    if gpu_id not in gpu_inventory:
        raise HTTPException(status_code=404, detail="GPU not found")
    
    gpu = gpu_inventory[gpu_id]
    
    if not gpu["mig_enabled"]:
        raise HTTPException(status_code=400, detail="MIG not enabled on this GPU")
    
    # Clear existing instances
    gpu["mig_instances"] = []
    
    # Create new instances
    instance_id = 0
    for profile in config.profiles:
        memory_map = {
            "1g.5gb": 5120,
            "2g.10gb": 10240,
            "3g.20gb": 20480,
            "4g.40gb": 40960,
            "7g.80gb": 81920
        }
        
        memory = memory_map.get(profile.profile, 5120)
        
        for _ in range(profile.instances):
            gpu["mig_instances"].append({
                "id": f"mig-{gpu_id}-{instance_id}",
                "profile": profile.profile,
                "memory": memory,
                "utilization": 0.0,
                "allocated": False
            })
            instance_id += 1
    
    mig_configs[gpu_id] = gpu["mig_instances"]
    logger.info(f"Configured {len(gpu['mig_instances'])} MIG instances on GPU {gpu_id}")
    
    return {
        "message": "MIG configured successfully",
        "gpu_id": gpu_id,
        "instances": gpu["mig_instances"]
    }

@app.get("/gpu/{gpu_id}/mig/instances")
async def get_mig_instances(gpu_id: int):
    """Get MIG instances for a GPU"""
    if gpu_id not in gpu_inventory:
        raise HTTPException(status_code=404, detail="GPU not found")
    
    gpu = gpu_inventory[gpu_id]
    return {"gpu_id": gpu_id, "instances": gpu["mig_instances"]}

@app.post("/gpu/{gpu_id}/mig/instance/{instance_id}/allocate")
async def allocate_instance(gpu_id: int, instance_id: str):
    """Allocate a MIG instance to a workload"""
    if gpu_id not in gpu_inventory:
        raise HTTPException(status_code=404, detail="GPU not found")
    
    gpu = gpu_inventory[gpu_id]
    for instance in gpu["mig_instances"]:
        if instance["id"] == instance_id:
            if instance["allocated"]:
                raise HTTPException(status_code=400, detail="Instance already allocated")
            instance["allocated"] = True
            instance["utilization"] = 45.0 + (hash(instance_id) % 40)
            return {"message": "Instance allocated", "instance": instance}
    
    raise HTTPException(status_code=404, detail="MIG instance not found")

@app.get("/metrics")
async def get_metrics():
    """Get Prometheus-compatible metrics"""
    metrics = []
    
    for gpu_id, gpu in gpu_inventory.items():
        metrics.append(f'gpu_utilization{{gpu_id="{gpu_id}"}} {gpu["utilization"]}')
        metrics.append(f'gpu_temperature{{gpu_id="{gpu_id}"}} {gpu["temperature"]}')
        metrics.append(f'gpu_power_usage{{gpu_id="{gpu_id}"}} {gpu["power_usage"]}')
        metrics.append(f'gpu_memory_total{{gpu_id="{gpu_id}"}} {gpu["total_memory"]}')
        
        for instance in gpu["mig_instances"]:
            allocated = 1 if instance["allocated"] else 0
            metrics.append(f'mig_instance_allocated{{gpu_id="{gpu_id}",instance_id="{instance["id"]}"}} {allocated}')
            metrics.append(f'mig_instance_utilization{{gpu_id="{gpu_id}",instance_id="{instance["id"]}"}} {instance["utilization"]}')
    
    return "\n".join(metrics)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
