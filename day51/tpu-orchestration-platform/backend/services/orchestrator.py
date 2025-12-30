import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque

from models.job import Job, JobStatus, TPUType

logger = logging.getLogger(__name__)

class TPUResource:
    def __init__(self, pod_id: str, tpu_type: TPUType, is_preemptible: bool):
        self.pod_id = pod_id
        self.tpu_type = tpu_type
        self.is_preemptible = is_preemptible
        self.available = True
        self.current_job_id: Optional[str] = None
        
class TPUResourceManager:
    def __init__(self):
        self.resources: Dict[str, TPUResource] = {}
        self._initialize_resources()
    
    def _initialize_resources(self):
        """Initialize simulated TPU pods"""
        tpu_configs = [
            ("v4-8-pod-1", TPUType.V4_8, False),
            ("v4-8-pod-2", TPUType.V4_8, True),
            ("v4-32-pod-1", TPUType.V4_32, False),
            ("v4-32-pod-2", TPUType.V4_32, True),
        ]
        
        for pod_id, tpu_type, preemptible in tpu_configs:
            self.resources[pod_id] = TPUResource(pod_id, tpu_type, preemptible)
        
        logger.info(f"Initialized {len(self.resources)} TPU pods")
    
    def find_available(self, tpu_type: TPUType, prefer_preemptible: bool) -> Optional[TPUResource]:
        """Find available TPU matching criteria"""
        candidates = [
            r for r in self.resources.values()
            if r.available and r.tpu_type == tpu_type
        ]
        
        if not candidates:
            return None
        
        # Prefer preemptible for cost savings if requested
        if prefer_preemptible:
            preemptible = [r for r in candidates if r.is_preemptible]
            if preemptible:
                return preemptible[0]
        
        return candidates[0]
    
    def allocate(self, resource: TPUResource, job_id: str):
        resource.available = False
        resource.current_job_id = job_id
    
    def release(self, pod_id: str):
        if pod_id in self.resources:
            self.resources[pod_id].available = True
            self.resources[pod_id].current_job_id = None
    
    def total_capacity(self) -> int:
        return len(self.resources)
    
    def available_capacity(self) -> int:
        return sum(1 for r in self.resources.values() if r.available)

class TPUOrchestrator:
    def __init__(self):
        self.job_queue = deque()
        self.active_jobs: Dict[str, Job] = {}
        self.completed_jobs: Dict[str, Job] = {}
        
        self.tpu_resources = TPUResourceManager()
        self.scheduling_interval = 5  # seconds
        
        logger.info("TPU Orchestrator initialized")
    
    async def schedule_job(self, job: Job) -> str:
        """Add job to scheduling queue"""
        self.job_queue.append(job)
        logger.info(f"Job {job.job_id} queued (priority: {job.priority})")
        return job.job_id
    
    async def scheduling_loop(self):
        """Continuous scheduling cycle"""
        logger.info("Starting scheduling loop...")
        
        while True:
            try:
                await self._schedule_cycle()
                await asyncio.sleep(self.scheduling_interval)
            except Exception as e:
                logger.error(f"Scheduling error: {e}")
    
    async def _schedule_cycle(self):
        """Single scheduling cycle"""
        if not self.job_queue:
            return
        
        # Sort queue by priority
        sorted_queue = sorted(self.job_queue, key=lambda j: j.priority, reverse=True)
        
        for job in sorted_queue:
            # Find suitable TPU
            resource = self.tpu_resources.find_available(
                job.tpu_type,
                job.can_use_preemptible()
            )
            
            if resource:
                # Allocate and start job
                self.tpu_resources.allocate(resource, job.job_id)
                job.tpu_pod_assigned = resource.pod_id
                job.status = JobStatus.PROVISIONING
                job.started_at = datetime.now()
                
                self.job_queue.remove(job)
                self.active_jobs[job.job_id] = job
                
                # Start training simulation
                asyncio.create_task(self._simulate_training(job))
                
                logger.info(
                    f"Scheduled job {job.job_id} on {resource.pod_id} "
                    f"({'preemptible' if resource.is_preemptible else 'on-demand'})"
                )
    
    async def _simulate_training(self, job: Job):
        """Simulate TPU training execution"""
        try:
            # Provisioning
            await asyncio.sleep(2)
            job.status = JobStatus.INITIALIZING
            
            # Initialization
            await asyncio.sleep(1)
            job.status = JobStatus.TRAINING
            
            # Training loop
            while job.current_step < job.total_steps:
                # Simulate training steps
                await asyncio.sleep(0.1)
                job.current_step += 10
                job.update_progress(job.current_step)
                
                # Accumulate cost
                job.cost_accumulated += 0.008  # $0.008 per step
                
                # Update metrics
                job.metrics = {
                    "mxu_utilization": 85.5 + (job.current_step % 10),
                    "memory_bandwidth_gbps": 950 + (job.current_step % 50),
                    "step_time_ms": 45 + (job.current_step % 5),
                    "flops": 2.5e11
                }
                
                # Checkpoint periodically
                if job.current_step % 1000 == 0:
                    prev_status = job.status
                    job.status = JobStatus.CHECKPOINTING
                    await asyncio.sleep(0.5)
                    job.status = prev_status
                    logger.info(f"Job {job.job_id} checkpointed at step {job.current_step}")
                
                # Simulate preemption (5% chance on preemptible)
                if job.tpu_pod_assigned and "pod-2" in job.tpu_pod_assigned:
                    import random
                    if random.random() < 0.001:  # 0.1% chance per step
                        logger.warning(f"Job {job.job_id} preempted!")
                        job.status = JobStatus.PREEMPTED
                        job.preemption_count += 1
                        
                        # Release resources
                        self.tpu_resources.release(job.tpu_pod_assigned)
                        job.tpu_pod_assigned = None
                        
                        # Re-queue if retries available
                        if job.retry_count < job.max_retries:
                            job.retry_count += 1
                            job.status = JobStatus.QUEUED
                            self.job_queue.append(job)
                            del self.active_jobs[job.job_id]
                            logger.info(f"Job {job.job_id} re-queued (retry {job.retry_count})")
                        else:
                            job.status = JobStatus.FAILED
                            job.completed_at = datetime.now()
                            self.completed_jobs[job.job_id] = job
                            del self.active_jobs[job.job_id]
                            logger.error(f"Job {job.job_id} failed after max retries")
                        return
            
            # Training completed successfully
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.update_progress(job.total_steps)
            
            # Release resources
            if job.tpu_pod_assigned:
                self.tpu_resources.release(job.tpu_pod_assigned)
            
            self.completed_jobs[job.job_id] = job
            del self.active_jobs[job.job_id]
            
            logger.info(
                f"Job {job.job_id} completed! "
                f"Cost: ${job.cost_accumulated:.2f}, "
                f"Preemptions: {job.preemption_count}"
            )
            
        except Exception as e:
            logger.error(f"Training error for job {job.job_id}: {e}")
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            
            if job.tpu_pod_assigned:
                self.tpu_resources.release(job.tpu_pod_assigned)
            
            self.completed_jobs[job.job_id] = job
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel active job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            
            if job.tpu_pod_assigned:
                self.tpu_resources.release(job.tpu_pod_assigned)
            
            self.completed_jobs[job_id] = job
            del self.active_jobs[job_id]
            
            logger.info(f"Job {job_id} cancelled")
            return True
        return False
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        if job_id in self.completed_jobs:
            return self.completed_jobs[job_id]
        for job in self.job_queue:
            if job.job_id == job_id:
                return job
        return None
    
    def get_queued_jobs(self) -> List[dict]:
        return [
            {"job_id": j.job_id, "model": j.model_name, "priority": j.priority}
            for j in self.job_queue
        ]
    
    def get_active_jobs(self) -> List[dict]:
        return [
            {
                "job_id": j.job_id,
                "model": j.model_name,
                "status": j.status.value,
                "progress": j.progress,
                "tpu_pod": j.tpu_pod_assigned,
                "cost": j.cost_accumulated
            }
            for j in self.active_jobs.values()
        ]
    
    def get_completed_jobs(self) -> List[dict]:
        return [
            {
                "job_id": j.job_id,
                "model": j.model_name,
                "status": j.status.value,
                "cost": j.cost_accumulated,
                "preemptions": j.preemption_count
            }
            for j in list(self.completed_jobs.values())[-10:]  # Last 10
        ]
    
    async def shutdown(self):
        logger.info("Orchestrator shutting down...")
