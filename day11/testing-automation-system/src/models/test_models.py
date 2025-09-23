from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class TestType(str, Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    CHAOS = "chaos"

class TestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

class TestCase(BaseModel):
    name: str
    description: Optional[str] = None
    test_type: TestType
    expected_duration: Optional[float] = None
    requirements: Optional[List[str]] = None

class TestExecution(BaseModel):
    test_case: TestCase
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    artifacts: Optional[Dict[str, Any]] = None

class QualityMetrics(BaseModel):
    code_coverage: float
    complexity_score: float
    maintainability_index: float
    technical_debt_ratio: float
    security_rating: str
    reliability_rating: str

class PerformanceMetrics(BaseModel):
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    throughput: float
    error_rate: float
    cpu_usage: float
    memory_usage: float
