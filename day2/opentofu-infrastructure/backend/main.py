from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import boto3
import subprocess
import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpenTofu Infrastructure Manager", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InfrastructureState(BaseModel):
    environment: str
    status: str
    resources: List[Dict]
    last_updated: datetime
    drift_detected: bool

class DeploymentRequest(BaseModel):
    environment: str
    action: str  # plan, apply, destroy
    auto_approve: bool = False

class DriftDetectionResult(BaseModel):
    environment: str
    drift_detected: bool
    changes: List[Dict]
    timestamp: datetime

# Global state storage
infrastructure_states = {}
drift_results = {}

# AWS clients
try:
    s3_client = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
except Exception as e:
    logger.warning(f"AWS clients not available: {e}")
    s3_client = None
    dynamodb = None

@app.get("/")
async def root():
    return {"message": "OpenTofu Infrastructure Manager API", "version": "1.0.0"}

@app.get("/api/infrastructure/status")
async def get_infrastructure_status():
    """Get current infrastructure status for all environments"""
    return {
        "environments": infrastructure_states,
        "total_environments": len(infrastructure_states),
        "healthy_environments": len([env for env in infrastructure_states.values() if env.get("status") == "healthy"])
    }

@app.get("/api/infrastructure/{environment}/state")
async def get_environment_state(environment: str):
    """Get detailed state for specific environment"""
    if environment not in infrastructure_states:
        # Simulate fetching from OpenTofu state
        infrastructure_states[environment] = {
            "environment": environment,
            "status": "healthy" if environment == "dev" else "unknown",
            "resources": [
                {"type": "aws_vpc", "name": f"{environment}-vpc", "status": "created"},
                {"type": "aws_subnet", "name": f"{environment}-public-subnet", "status": "created"},
                {"type": "aws_lb", "name": f"{environment}-alb", "status": "created"}
            ],
            "last_updated": datetime.now().isoformat(),
            "drift_detected": False
        }
    
    return infrastructure_states[environment]

@app.post("/api/infrastructure/deploy")
async def deploy_infrastructure(request: DeploymentRequest, background_tasks: BackgroundTasks):
    """Deploy infrastructure using OpenTofu"""
    logger.info(f"Deploying {request.environment} with action {request.action}")
    
    # Add background task for actual deployment
    background_tasks.add_task(execute_deployment, request)
    
    return {
        "message": f"Deployment {request.action} started for {request.environment}",
        "request_id": f"deploy-{request.environment}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    }

async def execute_deployment(request: DeploymentRequest):
    """Execute OpenTofu deployment in background"""
    try:
        env_path = f"../infrastructure/environments/{request.environment}"
        
        # Simulate OpenTofu commands
        if request.action == "plan":
            cmd = ["echo", "OpenTofu plan completed successfully"]
        elif request.action == "apply":
            cmd = ["echo", "OpenTofu apply completed successfully"]
        elif request.action == "destroy":
            cmd = ["echo", "OpenTofu destroy completed successfully"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Update infrastructure state
        infrastructure_states[request.environment] = {
            "environment": request.environment,
            "status": "healthy" if request.action != "destroy" else "destroyed",
            "resources": [] if request.action == "destroy" else [
                {"type": "aws_vpc", "name": f"{request.environment}-vpc", "status": "created"},
                {"type": "aws_subnet", "name": f"{request.environment}-public-subnet", "status": "created"},
                {"type": "aws_lb", "name": f"{request.environment}-alb", "status": "created"}
            ],
            "last_updated": datetime.now().isoformat(),
            "drift_detected": False
        }
        
        logger.info(f"Deployment {request.action} completed for {request.environment}")
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")

@app.get("/api/drift-detection/results")
async def get_all_drift_results():
    """Get drift detection results for all environments"""
    return {"results": drift_results}

@app.get("/api/drift-detection/{environment}")
async def check_drift(environment: str):
    """Check for infrastructure drift"""
    logger.info(f"Checking drift for {environment}")
    
    # Simulate drift detection
    drift_detected = False
    changes = []
    
    # For demo purposes, simulate occasional drift
    import random
    if random.random() < 0.3:  # 30% chance of drift
        drift_detected = True
        changes = [
            {"resource": f"{environment}-vpc", "change": "manual_tag_added", "severity": "low"},
            {"resource": f"{environment}-security-group", "change": "rule_modified", "severity": "medium"}
        ]
    
    result = DriftDetectionResult(
        environment=environment,
        drift_detected=drift_detected,
        changes=changes,
        timestamp=datetime.now()
    )
    
    drift_results[environment] = result.dict()
    return result

@app.post("/api/drift-detection/remediate/{environment}")
async def remediate_drift(environment: str, background_tasks: BackgroundTasks):
    """Remediate detected infrastructure drift"""
    if environment not in drift_results:
        raise HTTPException(status_code=404, detail="No drift detection results found")
    
    background_tasks.add_task(execute_drift_remediation, environment)
    
    return {"message": f"Drift remediation started for {environment}"}

async def execute_drift_remediation(environment: str):
    """Execute drift remediation in background"""
    try:
        logger.info(f"Remediating drift for {environment}")
        
        # Simulate remediation process
        await asyncio.sleep(2)
        
        # Clear drift status
        if environment in drift_results:
            drift_results[environment]["drift_detected"] = False
            drift_results[environment]["changes"] = []
            drift_results[environment]["timestamp"] = datetime.now().isoformat()
        
        logger.info(f"Drift remediation completed for {environment}")
        
    except Exception as e:
        logger.error(f"Drift remediation failed: {e}")

@app.get("/api/modules")
async def get_available_modules():
    """Get list of available infrastructure modules"""
    return {
        "modules": [
            {"name": "vpc", "version": "1.0.0", "description": "Virtual Private Cloud setup"},
            {"name": "compute", "version": "1.0.0", "description": "Auto-scaling compute resources"},
            {"name": "database", "version": "1.0.0", "description": "RDS database setup"},
            {"name": "monitoring", "version": "1.0.0", "description": "CloudWatch monitoring"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
