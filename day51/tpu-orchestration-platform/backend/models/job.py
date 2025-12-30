from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, Dict
from datetime import datetime
import uuid

class JobStatus(Enum):
    QUEUED = "queued"
    PROVISIONING = "provisioning"
    INITIALIZING = "initializing"
    TRAINING = "training"
    CHECKPOINTING = "checkpointing"
    PREEMPTED = "preempted"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TPUType(Enum):
    V3_8 = "v3-8"
    V3_32 = "v3-32"
    V4_8 = "v4-8"
    V4_32 = "v4-32"
    V4_128 = "v4-128"

class Job(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str
    tpu_type: TPUType = TPUType.V4_8
    priority: int = Field(default=50, ge=0, le=100)
    optimize_cost: bool = True
    use_preemptible: bool = True
    checkpoint_frequency_minutes: int = 10
    max_retries: int = 3
    
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    tpu_pod_assigned: Optional[str] = None
    current_step: int = 0
    total_steps: int = 10000
    progress: float = 0.0
    
    cost_accumulated: float = 0.0
    preemption_count: int = 0
    retry_count: int = 0
    
    metrics: Dict = Field(default_factory=dict)
    
    def update_progress(self, current_step: int):
        self.current_step = current_step
        self.progress = (current_step / self.total_steps) * 100
    
    def can_use_preemptible(self) -> bool:
        return self.optimize_cost and self.use_preemptible and self.priority < 80
