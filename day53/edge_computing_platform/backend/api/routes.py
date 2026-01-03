from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

app = FastAPI(title="Edge Control Plane")

# Serve static files from frontend/public
frontend_path = Path(__file__).parent.parent.parent / "frontend" / "public"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.get("/")
async def serve_dashboard():
    """Serve the dashboard index.html"""
    index_path = Path(__file__).parent.parent.parent / "frontend" / "public" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Dashboard not found"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from services.edge_controller import EdgeController

controller = EdgeController()
websocket_clients = []

class DeviceRegistration(BaseModel):
    location: Dict
    capabilities: List[str]

class HeartbeatData(BaseModel):
    device_id: str
    metrics: Dict

class ModelDeployment(BaseModel):
    model_id: str
    version: str
    optimization: str
    selector: Dict

@app.post("/api/devices/register")
async def register_device(registration: DeviceRegistration):
    device_id = controller.register_device(
        registration.location,
        registration.capabilities
    )
    await broadcast_update({"type": "device_registered", "device_id": device_id})
    return {"device_id": device_id, "status": "registered"}

@app.post("/api/devices/heartbeat")
async def process_heartbeat(heartbeat: HeartbeatData):
    result = controller.process_heartbeat(
        heartbeat.device_id,
        heartbeat.metrics
    )
    await broadcast_update({
        "type": "device_update",
        "device_id": heartbeat.device_id,
        "status": result.get("device_status")
    })
    return result

@app.get("/api/devices")
async def list_devices():
    devices = [d.to_dict() for d in controller.devices.values()]
    return {"devices": devices, "count": len(devices)}

@app.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    if device_id not in controller.devices:
        raise HTTPException(status_code=404, detail="Device not found")
    return controller.devices[device_id].to_dict()

@app.post("/api/models/deploy")
async def deploy_model(deployment: ModelDeployment):
    result = controller.deploy_model(
        deployment.model_id,
        deployment.version,
        deployment.optimization,
        deployment.selector
    )
    await broadcast_update({"type": "model_deployed", "deployment": result})
    return result

@app.get("/api/models")
async def list_models():
    models = [m.to_dict() for m in controller.models.values()]
    return {"models": models, "count": len(models)}

@app.get("/api/fleet/status")
async def fleet_status():
    return controller.get_fleet_status()

@app.get("/api/fleet/sync-metrics")
async def sync_metrics():
    return controller.get_sync_metrics()

@app.get("/api/deployments")
async def list_deployments():
    return {
        "deployments": controller.deployment_history,
        "count": len(controller.deployment_history)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)

async def broadcast_update(message: Dict):
    """Broadcast updates to all connected clients"""
    if websocket_clients:
        message["timestamp"] = datetime.now().isoformat()
        for client in websocket_clients:
            try:
                await client.send_json(message)
            except:
                pass

@app.post("/api/demo/seed")
async def seed_demo_data():
    """Seed demo data: deploy sample models to show in dashboard"""
    demo_deployments = []
    
    # Deploy models to different device types
    deployments = [
        {
            "model_id": "object-detection-v2",
            "version": "2.1.0",
            "optimization": "full",
            "selector": {"gpu": True}  # Deploy to GPU-capable devices
        },
        {
            "model_id": "quality-control",
            "version": "1.5.0",
            "optimization": "quantized",
            "selector": {}  # Deploy to all devices
        },
        {
            "model_id": "anomaly-detection",
            "version": "3.0.0",
            "optimization": "ultra-light",
            "selector": {"gpu": False}  # Deploy to CPU-only devices
        }
    ]
    
    for deployment in deployments:
        result = controller.deploy_model(
            deployment["model_id"],
            deployment["version"],
            deployment["optimization"],
            deployment["selector"]
        )
        demo_deployments.append(result)
        await broadcast_update({"type": "model_deployed", "deployment": result})
        await asyncio.sleep(0.5)  # Small delay between deployments
    
    return {
        "status": "success",
        "message": f"Deployed {len(demo_deployments)} demo models",
        "deployments": demo_deployments
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
