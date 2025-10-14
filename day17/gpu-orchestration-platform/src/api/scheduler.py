import asyncio
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import logging
import heapq

logger = logging.getLogger(__name__)

class WorkloadPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class WorkloadType(Enum):
    TRAINING = "training"
    INFERENCE = "inference"
    BATCH = "batch"
    INTERACTIVE = "interactive"

@dataclass
class WorkloadRequest:
    name: str
    workload_type: WorkloadType
    gpu_memory_required: int
    gpu_count: int = 1
    max_duration_hours: int = 24
    priority: WorkloadPriority = WorkloadPriority.NORMAL
    framework: str = "pytorch"
    
@dataclass
class WorkloadStatus:
    id: str
    request: WorkloadRequest
    status: str
    allocated_gpus: List[str]
    start_time: Optional[datetime]
    estimated_completion: Optional[datetime]
    cost_estimate: float

class GPUScheduler:
    def __init__(self, gpu_manager):
        self.gpu_manager = gpu_manager
        self.workloads: Dict[str, WorkloadStatus] = {}
        self.queue = []  # Priority queue for pending workloads
        self.running = False

    async def start_scheduler(self):
        """Start the background scheduler loop"""
        self.running = True
        asyncio.create_task(self._scheduler_loop())

    async def submit_workload(self, request: WorkloadRequest) -> str:
        """Submit new workload for scheduling"""
        workload_id = str(uuid.uuid4())
        
        status = WorkloadStatus(
            id=workload_id,
            request=request,
            status="pending",
            allocated_gpus=[],
            start_time=None,
            estimated_completion=None,
            cost_estimate=self._estimate_cost(request)
        )
        
        self.workloads[workload_id] = status
        
        # Add to priority queue
        heapq.heappush(self.queue, (
            -request.priority.value,  # Negative for max-heap behavior
            datetime.utcnow(),
            workload_id
        ))
        
        logger.info(f"Workload {workload_id} submitted: {request.name}")
        return workload_id

    async def get_workload_status(self, workload_id: str) -> Optional[Dict]:
        """Get current status of workload"""
        if workload_id not in self.workloads:
            return None
            
        status = self.workloads[workload_id]
        return {
            "id": status.id,
            "name": status.request.name,
            "status": status.status,
            "allocated_gpus": status.allocated_gpus,
            "start_time": status.start_time.isoformat() if status.start_time else None,
            "estimated_completion": status.estimated_completion.isoformat() if status.estimated_completion else None,
            "cost_estimate": status.cost_estimate,
            "workload_type": status.request.workload_type.value,
            "gpu_memory_required": status.request.gpu_memory_required,
            "gpu_count": status.request.gpu_count
        }

    async def _scheduler_loop(self):
        """Main scheduler loop - runs continuously"""
        while self.running:
            try:
                await self._process_pending_workloads()
                await self._check_running_workloads()
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")

    async def _process_pending_workloads(self):
        """Process workloads in priority queue"""
        while self.queue:
            _, _, workload_id = heapq.heappop(self.queue)
            
            if workload_id not in self.workloads:
                continue
                
            status = self.workloads[workload_id]
            if status.status != "pending":
                continue

            # Try to allocate resources
            allocated_gpus = await self._find_suitable_gpus(status.request)
            
            if allocated_gpus:
                # Allocate GPUs
                for gpu_id in allocated_gpus:
                    await self.gpu_manager.allocate_gpu(gpu_id, workload_id)
                
                status.allocated_gpus = allocated_gpus
                status.status = "running"
                status.start_time = datetime.utcnow()
                status.estimated_completion = status.start_time + timedelta(
                    hours=status.request.max_duration_hours
                )
                
                logger.info(f"Workload {workload_id} started on GPUs: {allocated_gpus}")
                break
            else:
                # Put back in queue for later
                heapq.heappush(self.queue, (
                    -status.request.priority.value,
                    datetime.utcnow(),
                    workload_id
                ))
                break

    async def _find_suitable_gpus(self, request: WorkloadRequest) -> List[str]:
        """Find GPUs that meet workload requirements"""
        available_resources = await self.gpu_manager.get_available_resources()
        suitable_gpus = []
        
        for resource in available_resources:
            if (resource["state"] == "available" and
                resource["memory_free_gb"] * (1024**3) >= request.gpu_memory_required):
                suitable_gpus.append(resource["id"])
                
                if len(suitable_gpus) >= request.gpu_count:
                    break
        
        return suitable_gpus[:request.gpu_count] if len(suitable_gpus) >= request.gpu_count else []

    async def _check_running_workloads(self):
        """Check for completed workloads and release resources"""
        for workload_id, status in list(self.workloads.items()):
            if status.status == "running":
                # Simulate workload completion after some time
                if status.start_time and datetime.utcnow() - status.start_time > timedelta(minutes=2):
                    await self._complete_workload(workload_id)

    async def _complete_workload(self, workload_id: str):
        """Complete workload and release GPU resources"""
        status = self.workloads[workload_id]
        
        # Release allocated GPUs
        for gpu_id in status.allocated_gpus:
            await self.gpu_manager.release_gpu(gpu_id)
        
        status.status = "completed"
        logger.info(f"Workload {workload_id} completed, GPUs released")

    def _estimate_cost(self, request: WorkloadRequest) -> float:
        """Estimate workload cost based on GPU type and duration"""
        # Simplified cost model - in production, use real pricing
        base_cost_per_hour = 3.20  # A100 hourly rate
        
        if "V100" in request.framework:
            base_cost_per_hour = 2.48
        elif "T4" in request.framework:
            base_cost_per_hour = 0.95
            
        return base_cost_per_hour * request.gpu_count * request.max_duration_hours

    async def process_workload(self, workload_id: str):
        """Background task to simulate workload processing"""
        await asyncio.sleep(1)  # Simulate processing delay
        logger.info(f"Processing workload {workload_id}")
