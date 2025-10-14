from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime

class WorkloadType(str, Enum):
    TRAINING = "training"
    INFERENCE = "inference"
    BATCH = "batch"
    INTERACTIVE = "interactive"

class WorkloadPriority(int, Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class WorkloadRequest(BaseModel):
    name: str = Field(..., description="Human-readable workload name")
    workload_type: WorkloadType = Field(..., description="Type of GPU workload")
    gpu_memory_required: int = Field(..., description="Required GPU memory in bytes", gt=0)
    gpu_count: int = Field(default=1, description="Number of GPUs required", ge=1)
    max_duration_hours: int = Field(default=24, description="Maximum runtime in hours", ge=1)
    priority: WorkloadPriority = Field(default=WorkloadPriority.NORMAL, description="Workload priority")
    framework: str = Field(default="pytorch", description="ML framework (pytorch, tensorflow, etc.)")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "BERT Model Training",
                "workload_type": "training",
                "gpu_memory_required": 16106127360,  # 15GB
                "gpu_count": 2,
                "max_duration_hours": 8,
                "priority": 2,
                "framework": "pytorch"
            }
        }

class WorkloadStatus(BaseModel):
    id: str
    name: str
    status: str
    allocated_gpus: List[str]
    start_time: Optional[datetime]
    estimated_completion: Optional[datetime]
    cost_estimate: float
    workload_type: str
    gpu_memory_required: int
    gpu_count: int

class GPUResource(BaseModel):
    id: str
    name: str
    memory_total_gb: int
    memory_used_gb: int
    memory_free_gb: int
    utilization_percent: float
    temperature_c: int
    power_usage_w: int
    state: str
    mig_enabled: bool = False

class MetricsResponse(BaseModel):
    timestamp: str
    cluster_stats: dict
    individual_gpus: List[dict]
    historical_data: List[dict]

class CostAnalysisResponse(BaseModel):
    current_hourly_cost: float
    projected_daily_cost: float
    projected_monthly_cost: float
    utilization_analysis: dict
    underutilized_gpus: List[str]
    optimization_recommendations: List[dict]
    cost_breakdown_by_gpu_type: dict
