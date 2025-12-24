import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobStatus(Enum):
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    INITIALIZING = "initializing"
    TRAINING = "training"
    CHECKPOINTING = "checkpointing"
    SUCCESS = "success"
    FAILED = "failed"
    PREEMPTED = "preempted"

@dataclass
class TrainingJob:
    job_id: str
    model_type: str
    epochs: int
    batch_size: int
    learning_rate: float
    num_gpus: int
    status: JobStatus
    priority: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    current_epoch: int = 0
    best_loss: float = float('inf')
    checkpoint_path: Optional[str] = None
    metrics: List[Dict] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = []

class TrainingOrchestrator:
    def __init__(self):
        self.jobs: Dict[str, TrainingJob] = {}
        self.queue: List[str] = []
        self.running_jobs: Dict[str, asyncio.Task] = {}
        self.available_gpus = 4
        self.allocated_gpus: Dict[str, int] = {}
        
    def submit_job(self, config: Dict) -> TrainingJob:
        """Submit new training job"""
        job = TrainingJob(
            job_id=str(uuid.uuid4())[:8],
            model_type=config.get('model_type', 'resnet18'),
            epochs=config.get('epochs', 10),
            batch_size=config.get('batch_size', 64),
            learning_rate=config.get('learning_rate', 0.001),
            num_gpus=config.get('num_gpus', 1),
            status=JobStatus.QUEUED,
            priority=config.get('priority', 5),
            created_at=datetime.now().isoformat()
        )
        
        self.jobs[job.job_id] = job
        self.queue.append(job.job_id)
        logger.info(f"Job {job.job_id} submitted and queued")
        
        return job
    
    def can_allocate(self, num_gpus: int) -> bool:
        """Check if enough GPUs available"""
        used = sum(self.allocated_gpus.values())
        return (self.available_gpus - used) >= num_gpus
    
    def allocate_gpus(self, job_id: str, num_gpus: int) -> bool:
        """Allocate GPUs to job"""
        if self.can_allocate(num_gpus):
            self.allocated_gpus[job_id] = num_gpus
            logger.info(f"Allocated {num_gpus} GPUs to job {job_id}")
            return True
        return False
    
    def release_gpus(self, job_id: str):
        """Release GPUs from job"""
        if job_id in self.allocated_gpus:
            released = self.allocated_gpus.pop(job_id)
            logger.info(f"Released {released} GPUs from job {job_id}")
    
    async def schedule_jobs(self):
        """Schedule queued jobs when resources available"""
        while True:
            if self.queue:
                # Sort by priority
                self.queue.sort(key=lambda jid: self.jobs[jid].priority, reverse=True)
                
                for job_id in self.queue[:]:
                    job = self.jobs[job_id]
                    
                    if self.allocate_gpus(job_id, job.num_gpus):
                        self.queue.remove(job_id)
                        job.status = JobStatus.SCHEDULED
                        job.started_at = datetime.now().isoformat()
                        
                        # Start training task
                        task = asyncio.create_task(self._run_training(job))
                        self.running_jobs[job_id] = task
                        
                        logger.info(f"Scheduled job {job_id}")
            
            await asyncio.sleep(1)
    
    async def _run_training(self, job: TrainingJob):
        """Execute training job"""
        try:
            job.status = JobStatus.INITIALIZING
            logger.info(f"Initializing job {job.job_id}")
            
            # Simulate initialization
            await asyncio.sleep(2)
            
            job.status = JobStatus.TRAINING
            logger.info(f"Training started for job {job.job_id}")
            
            # Training loop
            for epoch in range(job.current_epoch, job.epochs):
                job.current_epoch = epoch
                
                # Simulate training epoch
                await asyncio.sleep(1)
                
                # Generate mock metrics
                loss = max(0.1, 2.0 - (epoch * 0.15) + (epoch * 0.01 * hash(job.job_id) % 10 / 10))
                accuracy = min(0.95, 0.3 + (epoch * 0.06))
                
                metric = {
                    'epoch': epoch,
                    'loss': loss,
                    'accuracy': accuracy,
                    'timestamp': datetime.now().isoformat()
                }
                job.metrics.append(metric)
                
                if loss < job.best_loss:
                    job.best_loss = loss
                
                # Checkpoint every 5 epochs
                if (epoch + 1) % 5 == 0:
                    job.status = JobStatus.CHECKPOINTING
                    await self._save_checkpoint(job, epoch)
                    job.status = JobStatus.TRAINING
                
                logger.info(f"Job {job.job_id} - Epoch {epoch}/{job.epochs} - Loss: {loss:.4f}")
            
            # Training completed
            job.status = JobStatus.SUCCESS
            job.completed_at = datetime.now().isoformat()
            logger.info(f"Job {job.job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {e}")
            job.status = JobStatus.FAILED
        
        finally:
            self.release_gpus(job.job_id)
            if job.job_id in self.running_jobs:
                del self.running_jobs[job.job_id]
    
    async def _save_checkpoint(self, job: TrainingJob, epoch: int):
        """Save training checkpoint"""
        checkpoint_path = f"checkpoints/{job.job_id}_epoch_{epoch}.json"
        
        checkpoint = {
            'job_id': job.job_id,
            'epoch': epoch,
            'best_loss': job.best_loss,
            'model_state': f'model_weights_epoch_{epoch}',
            'optimizer_state': f'optimizer_state_epoch_{epoch}',
            'timestamp': datetime.now().isoformat()
        }
        
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        job.checkpoint_path = checkpoint_path
        logger.info(f"Checkpoint saved for job {job.job_id} at epoch {epoch}")
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status and metrics"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            return {
                **asdict(job),
                'status': job.status.value,
                'allocated_gpus': self.allocated_gpus.get(job_id, 0)
            }
        return None
    
    def get_all_jobs(self) -> List[Dict]:
        """Get all jobs with status"""
        return [
            {
                **asdict(job),
                'status': job.status.value,
                'allocated_gpus': self.allocated_gpus.get(job.job_id, 0)
            }
            for job in self.jobs.values()
        ]
    
    def get_resource_usage(self) -> Dict:
        """Get current resource utilization"""
        used = sum(self.allocated_gpus.values())
        return {
            'total_gpus': self.available_gpus,
            'used_gpus': used,
            'available_gpus': self.available_gpus - used,
            'utilization': (used / self.available_gpus) * 100,
            'active_jobs': len(self.running_jobs),
            'queued_jobs': len(self.queue)
        }

# Global orchestrator instance
orchestrator = TrainingOrchestrator()
