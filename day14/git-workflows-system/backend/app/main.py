from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import asyncio
from typing import List, Dict, Any
import git
import os
import yaml
from datetime import datetime
import subprocess
import logging

app = FastAPI(title="Git Workflows Manager", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

# Git workflow models
class BranchProtectionRule:
    def __init__(self, branch: str, require_reviews: int = 2, 
                 require_status_checks: bool = True, 
                 dismiss_stale_reviews: bool = True):
        self.branch = branch
        self.require_reviews = require_reviews
        self.require_status_checks = require_status_checks
        self.dismiss_stale_reviews = dismiss_stale_reviews

class WorkflowState:
    def __init__(self):
        self.branches = {}
        self.merge_queue = []
        self.protection_rules = []
        self.dependencies = {}
        self.lfs_files = []

workflow_state = WorkflowState()

@app.get("/")
async def root():
    return {"message": "Git Workflows Manager API", "status": "active"}

@app.get("/api/workflow/status")
async def get_workflow_status():
    return {
        "branches": len(workflow_state.branches),
        "merge_queue_size": len(workflow_state.merge_queue),
        "protection_rules": len(workflow_state.protection_rules),
        "dependencies": len(workflow_state.dependencies),
        "lfs_files": len(workflow_state.lfs_files),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/workflow/branch-protection")
async def create_branch_protection(rule_data: dict):
    rule = BranchProtectionRule(
        branch=rule_data["branch"],
        require_reviews=rule_data.get("require_reviews", 2),
        require_status_checks=rule_data.get("require_status_checks", True)
    )
    workflow_state.protection_rules.append(rule)
    
    await manager.broadcast({
        "type": "branch_protection_created",
        "data": rule_data,
        "timestamp": datetime.now().isoformat()
    })
    
    return {"status": "success", "rule": rule_data}

@app.post("/api/workflow/merge-queue")
async def add_to_merge_queue(merge_data: dict):
    merge_request = {
        "id": len(workflow_state.merge_queue) + 1,
        "branch": merge_data["branch"],
        "target": merge_data.get("target", "main"),
        "author": merge_data["author"],
        "status": "queued",
        "created_at": datetime.now().isoformat()
    }
    
    workflow_state.merge_queue.append(merge_request)
    
    await manager.broadcast({
        "type": "merge_queue_updated",
        "data": merge_request,
        "queue_size": len(workflow_state.merge_queue)
    })
    
    return {"status": "success", "merge_request": merge_request}

@app.post("/api/workflow/process-merge-queue")
async def process_merge_queue():
    if not workflow_state.merge_queue:
        return {"status": "queue_empty"}
    
    current_merge = workflow_state.merge_queue[0]
    current_merge["status"] = "processing"
    
    # Simulate merge processing
    await asyncio.sleep(2)
    
    # Simulate successful merge
    current_merge["status"] = "merged"
    current_merge["merged_at"] = datetime.now().isoformat()
    
    workflow_state.merge_queue.pop(0)
    
    await manager.broadcast({
        "type": "merge_completed",
        "data": current_merge,
        "queue_size": len(workflow_state.merge_queue)
    })
    
    return {"status": "success", "merged": current_merge}

@app.post("/api/workflow/dependency-update")
async def simulate_dependency_update():
    dependency_update = {
        "package": "fastapi",
        "from_version": "0.104.0",
        "to_version": "0.104.1",
        "security_patch": True,
        "auto_merge": True,
        "timestamp": datetime.now().isoformat()
    }
    
    workflow_state.dependencies[dependency_update["package"]] = dependency_update
    
    await manager.broadcast({
        "type": "dependency_updated",
        "data": dependency_update
    })
    
    return {"status": "success", "update": dependency_update}

@app.post("/api/workflow/lfs-track")
async def track_lfs_file(file_data: dict):
    lfs_file = {
        "path": file_data["path"],
        "size": file_data["size"],
        "type": file_data.get("type", "binary"),
        "tracked_at": datetime.now().isoformat()
    }
    
    workflow_state.lfs_files.append(lfs_file)
    
    await manager.broadcast({
        "type": "lfs_file_tracked",
        "data": lfs_file,
        "total_lfs_files": len(workflow_state.lfs_files)
    })
    
    return {"status": "success", "lfs_file": lfs_file}

@app.get("/api/workflow/analytics")
async def get_workflow_analytics():
    return {
        "merge_queue": {
            "current_size": len(workflow_state.merge_queue),
            "processing_time_avg": 5.2,
            "success_rate": 95.7
        },
        "branch_protection": {
            "rules_count": len(workflow_state.protection_rules),
            "violations_today": 0,
            "enforcement_rate": 100.0
        },
        "dependencies": {
            "total_tracked": len(workflow_state.dependencies),
            "security_updates_today": 3,
            "outdated_packages": 1
        },
        "lfs": {
            "files_tracked": len(workflow_state.lfs_files),
            "storage_used": "2.3 GB",
            "bandwidth_saved": "847 MB"
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for keep-alive
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
