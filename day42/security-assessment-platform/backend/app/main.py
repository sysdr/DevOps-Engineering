from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
import logging

app = FastAPI(title="Security Assessment Platform", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for assessment results
assessment_results = {}
active_assessments = {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/assessment/status")
async def get_assessment_status():
    """Get current assessment status"""
    return {
        "active_assessments": len(active_assessments),
        "completed_assessments": len(assessment_results),
        "last_assessment": max(assessment_results.keys()) if assessment_results else None
    }

@app.post("/api/assessment/run")
async def run_assessment(background_tasks: BackgroundTasks):
    """Trigger a full security assessment"""
    assessment_id = f"assessment-{datetime.utcnow().timestamp()}"
    
    # Add assessment to active list
    active_assessments[assessment_id] = {
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "progress": 0
    }
    
    # Run assessment in background
    background_tasks.add_task(execute_assessment, assessment_id)
    
    return {
        "assessment_id": assessment_id,
        "status": "started",
        "message": "Security assessment initiated"
    }

async def execute_assessment(assessment_id: str):
    """Execute full security assessment"""
    try:
        results = {
            "assessment_id": assessment_id,
            "started_at": active_assessments[assessment_id]["started_at"],
            "components": {}
        }
        
        # Import validators
        from validators.container_security import validate_container_security
        from validators.secrets_validator import validate_secrets_management
        from validators.runtime_validator import validate_runtime_security
        from validators.vulnerability_scanner import validate_vulnerability_scanning
        from validators.incident_response import validate_incident_response
        from validators.supply_chain import validate_supply_chain
        
        # Run all validators
        logger.info(f"Running container security validation for {assessment_id}")
        active_assessments[assessment_id]["progress"] = 10
        results["components"]["container_security"] = await validate_container_security()
        
        logger.info(f"Running secrets validation for {assessment_id}")
        active_assessments[assessment_id]["progress"] = 25
        results["components"]["secrets_management"] = await validate_secrets_management()
        
        logger.info(f"Running runtime security validation for {assessment_id}")
        active_assessments[assessment_id]["progress"] = 40
        results["components"]["runtime_security"] = await validate_runtime_security()
        
        logger.info(f"Running vulnerability scanning validation for {assessment_id}")
        active_assessments[assessment_id]["progress"] = 55
        results["components"]["vulnerability_scanning"] = await validate_vulnerability_scanning()
        
        logger.info(f"Running incident response validation for {assessment_id}")
        active_assessments[assessment_id]["progress"] = 70
        results["components"]["incident_response"] = await validate_incident_response()
        
        logger.info(f"Running supply chain validation for {assessment_id}")
        active_assessments[assessment_id]["progress"] = 85
        results["components"]["supply_chain"] = await validate_supply_chain()
        
        # Calculate overall score
        from services.scoring_engine import calculate_security_score
        results["security_score"] = calculate_security_score(results["components"])
        
        # Generate compliance report
        from compliance.compliance_checker import generate_compliance_report
        results["compliance"] = generate_compliance_report(results["components"])
        
        # Store results
        results["completed_at"] = datetime.utcnow().isoformat()
        results["status"] = "completed"
        assessment_results[assessment_id] = results
        
        # Remove from active
        del active_assessments[assessment_id]
        
        logger.info(f"Assessment {assessment_id} completed with score: {results['security_score']}")
        
    except Exception as e:
        logger.error(f"Assessment {assessment_id} failed: {str(e)}")
        if assessment_id in active_assessments:
            active_assessments[assessment_id]["status"] = "failed"
            active_assessments[assessment_id]["error"] = str(e)

@app.get("/api/assessment/results/{assessment_id}")
async def get_assessment_results(assessment_id: str):
    """Get results for a specific assessment"""
    if assessment_id in assessment_results:
        return assessment_results[assessment_id]
    elif assessment_id in active_assessments:
        return {
            "assessment_id": assessment_id,
            "status": "running",
            "progress": active_assessments[assessment_id]["progress"]
        }
    else:
        raise HTTPException(status_code=404, detail="Assessment not found")

@app.get("/api/assessment/results/latest")
async def get_latest_results():
    """Get latest assessment results"""
    if not assessment_results:
        raise HTTPException(status_code=404, detail="No assessments found")
    
    latest_id = max(assessment_results.keys())
    return assessment_results[latest_id]

@app.post("/api/pentest/run")
async def run_penetration_tests(background_tasks: BackgroundTasks, test_suite: Optional[str] = "full"):
    """Run penetration tests"""
    test_id = f"pentest-{datetime.utcnow().timestamp()}"
    
    background_tasks.add_task(execute_pentests, test_id, test_suite)
    
    return {
        "test_id": test_id,
        "suite": test_suite,
        "status": "started"
    }

async def execute_pentests(test_id: str, test_suite: str):
    """Execute penetration tests"""
    try:
        from pentests.pentest_runner import run_test_suite
        results = await run_test_suite(test_suite)
        assessment_results[test_id] = results
        logger.info(f"Penetration tests {test_id} completed")
    except Exception as e:
        logger.error(f"Penetration tests {test_id} failed: {str(e)}")

@app.get("/api/compliance/report/{framework}")
async def get_compliance_report(framework: str):
    """Get compliance report for specific framework"""
    if framework not in ["soc2", "iso27001", "cis"]:
        raise HTTPException(status_code=400, detail="Invalid framework")
    
    # Get latest assessment
    if not assessment_results:
        raise HTTPException(status_code=404, detail="No assessment data available")
    
    latest_id = max(assessment_results.keys())
    assessment_data = assessment_results[latest_id]
    
    from compliance.compliance_checker import generate_framework_report
    report = generate_framework_report(framework, assessment_data)
    
    return report

@app.get("/api/playbooks")
async def get_incident_playbooks():
    """Get all generated incident response playbooks"""
    from playbooks.playbook_generator import get_all_playbooks
    return get_all_playbooks()

@app.get("/api/playbooks/{vulnerability_type}")
async def get_playbook(vulnerability_type: str):
    """Get specific incident response playbook"""
    from playbooks.playbook_generator import generate_playbook
    playbook = generate_playbook(vulnerability_type)
    return playbook

@app.get("/api/metrics/score-history")
async def get_score_history():
    """Get security score history"""
    history = []
    for assessment_id, result in sorted(assessment_results.items()):
        if "security_score" in result:
            history.append({
                "timestamp": result.get("completed_at"),
                "score": result["security_score"]["total_score"],
                "assessment_id": assessment_id
            })
    return history

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
