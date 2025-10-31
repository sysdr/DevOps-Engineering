from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import yaml
import git
import json
from datetime import datetime
import httpx
import asyncio

app = FastAPI(title="GitOps Demo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Application(BaseModel):
    name: str
    environment: str
    status: str
    sync_status: str
    health_status: str
    last_sync: str
    git_revision: str

class GitOpsConfig(BaseModel):
    repo_url: str
    branch: str
    path: str
    auto_sync: bool

# Global state
applications_state = {}
gitops_configs = {}

@app.get("/")
async def root():
    return {"message": "GitOps Demo API", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/applications")
async def get_applications() -> List[Application]:
    """Get all applications with their GitOps status"""
    apps = []
    for env in ["dev", "staging", "prod"]:
        for app_name in ["web-app", "api-service"]:
            app_id = f"{app_name}-{env}"
            state = applications_state.get(app_id, {})
            apps.append(Application(
                name=app_name,
                environment=env,
                status=state.get("status", "Unknown"),
                sync_status=state.get("sync_status", "OutOfSync"),
                health_status=state.get("health_status", "Unknown"),
                last_sync=state.get("last_sync", "Never"),
                git_revision=state.get("git_revision", "unknown")
            ))
    return apps

@app.get("/applications/{app_name}/{environment}")
async def get_application_details(app_name: str, environment: str):
    """Get detailed information about a specific application"""
    app_id = f"{app_name}-{environment}"
    if app_id not in applications_state:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {
        "application": applications_state[app_id],
        "config": gitops_configs.get(app_id, {}),
        "resources": await get_application_resources(app_name, environment)
    }

async def get_application_resources(app_name: str, environment: str):
    """Simulate getting Kubernetes resources for an application"""
    return [
        {
            "kind": "Deployment",
            "name": f"{app_name}-deployment",
            "namespace": environment,
            "status": "Running",
            "replicas": "3/3"
        },
        {
            "kind": "Service", 
            "name": f"{app_name}-service",
            "namespace": environment,
            "status": "Active",
            "type": "ClusterIP"
        },
        {
            "kind": "Ingress",
            "name": f"{app_name}-ingress", 
            "namespace": environment,
            "status": "Ready",
            "hosts": [f"{app_name}-{environment}.demo.local"]
        }
    ]

@app.post("/sync/{app_name}/{environment}")
async def sync_application(app_name: str, environment: str):
    """Trigger manual sync for an application"""
    app_id = f"{app_name}-{environment}"
    
    # Simulate sync process
    applications_state[app_id] = {
        "status": "Syncing",
        "sync_status": "Progressing", 
        "health_status": "Progressing",
        "last_sync": datetime.now().isoformat(),
        "git_revision": f"abc123{hash(app_id) % 10000}"
    }
    
    # Simulate async sync completion
    async def complete_sync():
        await asyncio.sleep(2)
        applications_state[app_id].update({
            "status": "Running",
            "sync_status": "Synced",
            "health_status": "Healthy"
        })
    
    asyncio.create_task(complete_sync())
    
    return {"message": f"Sync initiated for {app_name} in {environment}"}

@app.get("/metrics")
async def get_metrics():
    """GitOps metrics endpoint"""
    synced_apps = len([app for app in applications_state.values() if app.get("sync_status") == "Synced"])
    total_apps = len(applications_state)
    
    return {
        "applications_total": total_apps,
        "applications_synced": synced_apps,
        "applications_out_of_sync": total_apps - synced_apps,
        "sync_success_rate": (synced_apps / max(total_apps, 1)) * 100
    }

# Initialize sample data
def initialize_data():
    """Initialize sample application states"""
    for env in ["dev", "staging", "prod"]:
        for app_name in ["web-app", "api-service"]:
            app_id = f"{app_name}-{env}"
            applications_state[app_id] = {
                "status": "Running" if env != "prod" else "Pending",
                "sync_status": "Synced" if env == "dev" else "OutOfSync",
                "health_status": "Healthy" if env == "dev" else "Unknown",
                "last_sync": datetime.now().isoformat() if env == "dev" else "Never",
                "git_revision": f"abc123{hash(app_id) % 10000}"
            }
            
            gitops_configs[app_id] = {
                "repo_url": "https://github.com/demo/gitops-config",
                "branch": "main",
                "path": f"apps/{env}/{app_name}",
                "auto_sync": env == "dev"
            }

initialize_data()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
