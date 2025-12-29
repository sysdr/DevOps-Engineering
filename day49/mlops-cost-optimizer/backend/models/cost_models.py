from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

class ResourceType(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    STORAGE = "storage"

class JobPriority(str, Enum):
    CRITICAL = "P0"
    NORMAL = "P1"
    LOW = "P2"

class CostRecord(BaseModel):
    timestamp: datetime
    team: str
    project: str
    resource_type: ResourceType
    quantity: float
    cost_per_hour: float
    total_cost: float
    instance_type: str
    region: str
    tags: Dict[str, str] = {}

class SpotInstance(BaseModel):
    instance_id: str
    instance_type: str
    availability_zone: str
    state: str
    assigned_job: Optional[str] = None
    interruption_time: Optional[datetime] = None
    hourly_cost: float

class MLJob(BaseModel):
    job_id: str
    name: str
    team: str
    project: str
    priority: JobPriority
    cpu_request: int
    memory_request: int  # GB
    gpu_request: int = 0
    estimated_duration: int  # hours
    checkpoint_interval: int = 600  # seconds
    max_retries: int = 3

class InferenceConfig(BaseModel):
    model_id: str
    instance_type: str
    replicas: int
    batch_size: int = 1
    p99_latency_ms: float
    qps: float
    monthly_cost: float

class BudgetQuota(BaseModel):
    team: str
    monthly_budget: float
    current_spend: float
    forecast_spend: float
    alert_threshold: float = 0.8

class CostMetrics(BaseModel):
    total_cost: float
    training_cost: float
    inference_cost: float
    storage_cost: float
    by_team: Dict[str, float]
    by_project: Dict[str, float]
    daily_trend: List[Dict[str, float]]
