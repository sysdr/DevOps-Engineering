from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
from datetime import datetime, timedelta
import asyncio
import logging
from typing import Dict, List, Optional
import json

from validators.reliability import ReliabilityValidator
from validators.security import SecurityValidator
from validators.observability import ObservabilityValidator
from validators.cost import CostValidator
from validators.scalability import ScalabilityValidator
from validators.operability import OperabilityValidator
from generators.runbook_generator import RunbookGenerator
from generators.knowledge_generator import KnowledgeGenerator
from services.integration_tester import IntegrationTester
from services.validation_engine import ValidationEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Production Readiness Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics
validation_counter = Counter('validation_runs_total', 'Total validation runs')
validation_duration = Histogram('validation_duration_seconds', 'Validation duration')
readiness_score = Histogram('readiness_score', 'Current readiness score')

# Global state
validation_results = {
    "last_run": None,
    "scores": {},
    "status": "initializing",
    "history": []
}

integration_test_results = {
    "last_run": None,
    "tests": [],
    "pass_rate": 0.0
}

# Initialize components
validators = {
    "reliability": ReliabilityValidator(),
    "security": SecurityValidator(),
    "observability": ObservabilityValidator(),
    "cost": CostValidator(),
    "scalability": ScalabilityValidator(),
    "operability": OperabilityValidator()
}

runbook_gen = RunbookGenerator()
knowledge_gen = KnowledgeGenerator()
integration_tester = IntegrationTester()
validation_engine = ValidationEngine(validators)

@app.get("/")
async def root():
    return {
        "service": "Production Readiness Platform",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "validators": len(validators),
        "last_validation": validation_results.get("last_run"),
        "last_test": integration_test_results.get("last_run")
    }

@app.post("/api/v1/validate")
async def run_validation():
    """Run comprehensive production readiness validation"""
    validation_counter.inc()
    
    start_time = datetime.utcnow()
    
    try:
        results = await validation_engine.run_validation()
        
        validation_results.update({
            "last_run": datetime.utcnow().isoformat(),
            "scores": results["scores"],
            "status": results["status"],
            "details": results["details"]
        })
        
        # Store in history
        validation_results["history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "scores": results["scores"],
            "overall_score": results["overall_score"]
        })
        
        # Keep only last 100 results
        if len(validation_results["history"]) > 100:
            validation_results["history"] = validation_results["history"][-100:]
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        validation_duration.observe(duration)
        readiness_score.observe(results["overall_score"])
        
        return results
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/validation/status")
async def get_validation_status():
    """Get current validation status"""
    return validation_results

@app.get("/api/v1/validation/history")
async def get_validation_history(hours: int = 24):
    """Get validation history"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    filtered_history = [
        h for h in validation_results.get("history", [])
        if datetime.fromisoformat(h["timestamp"]) > cutoff
    ]
    
    return {
        "history": filtered_history,
        "period_hours": hours,
        "count": len(filtered_history)
    }

@app.post("/api/v1/integration-tests")
async def run_integration_tests():
    """Run end-to-end integration tests"""
    try:
        results = await integration_tester.run_tests()
        
        integration_test_results.update({
            "last_run": datetime.utcnow().isoformat(),
            "tests": results["tests"],
            "pass_rate": results["pass_rate"],
            "total": results["total"],
            "passed": results["passed"],
            "failed": results["failed"]
        })
        
        return results
        
    except Exception as e:
        logger.error(f"Integration tests failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/integration-tests/status")
async def get_test_status():
    """Get integration test status"""
    return integration_test_results

@app.post("/api/v1/runbooks/generate")
async def generate_runbook(scenario: str):
    """Generate operational runbook for a scenario"""
    try:
        runbook = await runbook_gen.generate(scenario)
        return runbook
    except Exception as e:
        logger.error(f"Runbook generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/runbooks")
async def list_runbooks():
    """List available runbooks"""
    return await runbook_gen.list_runbooks()

@app.get("/api/v1/runbooks/{runbook_id}")
async def get_runbook(runbook_id: str):
    """Get specific runbook"""
    runbook = await runbook_gen.get_runbook(runbook_id)
    if not runbook:
        raise HTTPException(status_code=404, detail="Runbook not found")
    return runbook

@app.post("/api/v1/knowledge/generate")
async def generate_knowledge():
    """Generate knowledge transfer materials"""
    try:
        materials = await knowledge_gen.generate()
        return materials
    except Exception as e:
        logger.error(f"Knowledge generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/knowledge")
async def get_knowledge():
    """Get knowledge transfer materials"""
    return await knowledge_gen.get_materials()

@app.get("/api/v1/dashboard/summary")
async def get_dashboard_summary():
    """Get dashboard summary data"""
    return {
        "validation": {
            "last_run": validation_results.get("last_run"),
            "scores": validation_results.get("scores", {}),
            "status": validation_results.get("status")
        },
        "testing": {
            "last_run": integration_test_results.get("last_run"),
            "pass_rate": integration_test_results.get("pass_rate", 0),
            "total_tests": integration_test_results.get("total", 0)
        },
        "runbooks": {
            "count": await runbook_gen.count()
        },
        "knowledge": {
            "materials": await knowledge_gen.count()
        }
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

# Background task for continuous validation
async def continuous_validation():
    """Run validation continuously"""
    while True:
        try:
            logger.info("Running continuous validation...")
            await validation_engine.run_validation()
            await asyncio.sleep(300)  # Every 5 minutes
        except Exception as e:
            logger.error(f"Continuous validation error: {str(e)}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(continuous_validation())
    logger.info("Production Readiness Platform started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
