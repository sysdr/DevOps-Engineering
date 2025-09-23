from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
import time
import random
from datetime import datetime
import subprocess
import os

app = FastAPI(title="Testing Automation System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class TestResult(BaseModel):
    test_id: str
    test_type: str
    status: str
    duration: float
    coverage: Optional[float] = None
    timestamp: datetime

class QualityGate(BaseModel):
    name: str
    status: str
    threshold: float
    current_value: float
    passed: bool

class TestSuite(BaseModel):
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    coverage: float
    duration: float

# In-memory storage (production would use database)
test_results: List[TestResult] = []
quality_gates: List[QualityGate] = []
test_metrics = {
    "total_tests_run": 0,
    "success_rate": 0.0,
    "avg_duration": 0.0,
    "coverage_trend": [],
    "performance_trend": []
}

@app.get("/")
async def root():
    return {"message": "Testing Automation System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post("/tests/run/{test_type}")
async def run_tests(test_type: str, background_tasks: BackgroundTasks):
    """Run specific test type"""
    if test_type not in ["unit", "integration", "e2e", "performance", "chaos"]:
        raise HTTPException(status_code=400, detail="Invalid test type")
    
    test_id = f"{test_type}_{int(time.time())}"
    
    # Start background test execution
    background_tasks.add_task(execute_tests, test_type, test_id)
    
    return {"test_id": test_id, "status": "started", "test_type": test_type}

@app.get("/tests/results")
async def get_test_results():
    return {"results": test_results, "total": len(test_results)}

@app.get("/tests/results/{test_id}")
async def get_test_result(test_id: str):
    result = next((r for r in test_results if r.test_id == test_id), None)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    return result

@app.get("/quality/gates")
async def get_quality_gates():
    # Update quality gates based on recent test results
    update_quality_gates()
    return {"gates": quality_gates}

@app.get("/metrics/dashboard")
async def get_dashboard_metrics():
    update_metrics()
    return {
        "metrics": test_metrics,
        "recent_results": test_results[-10:],
        "quality_gates": quality_gates
    }

@app.post("/chaos/inject/{fault_type}")
async def inject_chaos(fault_type: str, duration: int = 30):
    """Inject chaos for testing resilience"""
    if fault_type not in ["latency", "error", "shutdown"]:
        raise HTTPException(status_code=400, detail="Invalid fault type")
    
    chaos_id = f"chaos_{fault_type}_{int(time.time())}"
    
    # Simulate chaos injection
    await asyncio.sleep(1)  # Simulate injection time
    
    # Record chaos test result
    result = TestResult(
        test_id=chaos_id,
        test_type="chaos",
        status="completed",
        duration=duration,
        timestamp=datetime.now()
    )
    test_results.append(result)
    
    return {"chaos_id": chaos_id, "fault_type": fault_type, "duration": duration}

async def execute_tests(test_type: str, test_id: str):
    """Background task to execute tests"""
    start_time = time.time()
    
    # Simulate test execution
    await asyncio.sleep(random.uniform(5, 15))  # Realistic test duration
    
    # Simulate test results
    status = "passed" if random.random() > 0.1 else "failed"
    coverage = random.uniform(0.7, 0.95) if test_type in ["unit", "integration"] else None
    
    duration = time.time() - start_time
    
    result = TestResult(
        test_id=test_id,
        test_type=test_type,
        status=status,
        duration=duration,
        coverage=coverage,
        timestamp=datetime.now()
    )
    
    test_results.append(result)
    test_metrics["total_tests_run"] += 1

def update_quality_gates():
    """Update quality gates based on test results"""
    global quality_gates
    
    recent_results = test_results[-20:] if len(test_results) >= 20 else test_results
    
    if not recent_results:
        return
    
    # Code coverage gate
    coverage_values = [r.coverage for r in recent_results if r.coverage is not None]
    avg_coverage = sum(coverage_values) / len(coverage_values) if coverage_values else 0
    
    # Success rate gate
    passed_tests = len([r for r in recent_results if r.status == "passed"])
    success_rate = passed_tests / len(recent_results) if recent_results else 0
    
    # Performance gate
    avg_duration = sum([r.duration for r in recent_results]) / len(recent_results)
    
    quality_gates = [
        QualityGate(
            name="Code Coverage",
            status="passed" if avg_coverage >= 0.8 else "failed",
            threshold=0.8,
            current_value=avg_coverage,
            passed=avg_coverage >= 0.8
        ),
        QualityGate(
            name="Success Rate",
            status="passed" if success_rate >= 0.95 else "failed",
            threshold=0.95,
            current_value=success_rate,
            passed=success_rate >= 0.95
        ),
        QualityGate(
            name="Performance",
            status="passed" if avg_duration <= 30.0 else "failed",
            threshold=30.0,
            current_value=avg_duration,
            passed=avg_duration <= 30.0
        )
    ]

def update_metrics():
    """Update system metrics"""
    if not test_results:
        return
    
    recent_results = test_results[-50:]
    
    # Success rate
    passed = len([r for r in recent_results if r.status == "passed"])
    test_metrics["success_rate"] = passed / len(recent_results)
    
    # Average duration
    test_metrics["avg_duration"] = sum([r.duration for r in recent_results]) / len(recent_results)
    
    # Coverage trend
    coverage_values = [r.coverage for r in recent_results[-10:] if r.coverage is not None]
    test_metrics["coverage_trend"] = coverage_values
    
    # Performance trend
    perf_values = [r.duration for r in recent_results[-10:]]
    test_metrics["performance_trend"] = perf_values

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
