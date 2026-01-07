from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskStatus(str, Enum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Task(BaseModel):
    id: str
    name: str
    dependencies: List[str] = []
    command: str
    timeout: int = 300
    retry_count: int = 3
    status: TaskStatus = TaskStatus.WAITING

class Workflow(BaseModel):
    id: str
    name: str
    tasks: List[Task]
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class HealthStatus(BaseModel):
    resource_id: str
    resource_type: str
    healthy: bool
    last_check: datetime
    metrics: Dict[str, float]

class ChaosExperiment(BaseModel):
    id: str
    name: str
    type: str
    blast_radius: float
    steady_state_metrics: Dict[str, float]
    status: str = "scheduled"
    results: Optional[Dict[str, Any]] = None

class Incident(BaseModel):
    id: str
    severity: IncidentSeverity
    description: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    auto_resolved: bool = False
    remediation_actions: List[str] = []
