"""GitOps Observability Platform - Main Application"""
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json

from collectors.metrics_collector import MetricsCollector
from calculators.sli_calculator import SLICalculator
from evaluators.slo_evaluator import SLOEvaluator
from automators.incident_automator import IncidentAutomator
from api.routes import router
from models.database import Database
from utils.websocket_manager import WebSocketManager

db = Database()
ws_manager = WebSocketManager()
metrics_collector = MetricsCollector(db)
sli_calculator = SLICalculator(db)
slo_evaluator = SLOEvaluator(db)
incident_automator = IncidentAutomator(db)

async def background_tasks():
    """Run background collection and evaluation tasks"""
    while True:
        try:
            await metrics_collector.collect()
            slis = await sli_calculator.calculate()
            evaluations = await slo_evaluator.evaluate(slis)
            await incident_automator.process(evaluations)
            
            dashboard_data = {
                "metrics": await db.get_latest_metrics(),
                "slis": slis,
                "evaluations": evaluations,
                "incidents": await db.get_active_incidents(),
                "deployments": await db.get_recent_deployments()
            }
            await ws_manager.broadcast(json.dumps(dashboard_data))
        except Exception as e:
            print(f"Background task error: {e}")
        
        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(background_tasks())
    yield
    task.cancel()

app = FastAPI(
    title="GitOps Observability Platform",
    description="SLI/SLO tracking and incident automation for GitOps",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "components": {
            "collector": metrics_collector.status,
            "calculator": sli_calculator.status,
            "evaluator": slo_evaluator.status,
            "automator": incident_automator.status
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
