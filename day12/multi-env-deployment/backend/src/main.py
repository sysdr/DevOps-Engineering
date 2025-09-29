from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
import os
from deployment.pipeline import DeploymentPipeline
from deployment.blue_green import BlueGreenDeployer
from deployment.canary import CanaryDeployer
from features.flags import FeatureFlagService
from config.manager import ConfigManager
from monitoring.metrics import MetricsCollector

app = FastAPI(title="Multi-Environment Deployment Platform", version="1.0.0")

# Initialize services
pipeline = DeploymentPipeline()
blue_green = BlueGreenDeployer()
canary = CanaryDeployer()
feature_flags = FeatureFlagService()
config_manager = ConfigManager()
metrics = MetricsCollector()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    with open("frontend/public/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/environments")
async def get_environments():
    return {
        "environments": [
            {"name": "dev", "status": "active", "version": "1.2.3"},
            {"name": "staging", "status": "deploying", "version": "1.2.4"},
            {"name": "prod", "status": "stable", "version": "1.2.3"}
        ]
    }

@app.post("/api/deploy")
async def trigger_deployment(deployment_request: dict, background_tasks: BackgroundTasks):
    deployment_id = await pipeline.start_deployment(
        environment=deployment_request["environment"],
        version=deployment_request["version"],
        strategy=deployment_request.get("strategy", "blue-green")
    )
    
    if deployment_request.get("strategy") == "canary":
        background_tasks.add_task(canary.execute_canary_deployment, deployment_id)
    else:
        background_tasks.add_task(blue_green.execute_deployment, deployment_id)
    
    return {"deployment_id": deployment_id, "status": "started"}

@app.get("/api/deployments/{deployment_id}")
async def get_deployment_status(deployment_id: str):
    return await pipeline.get_deployment_status(deployment_id)

@app.post("/api/rollback/{deployment_id}")
async def rollback_deployment(deployment_id: str):
    return await pipeline.rollback_deployment(deployment_id)

@app.get("/api/feature-flags")
async def get_feature_flags():
    return await feature_flags.get_all_flags()

@app.put("/api/feature-flags/{flag_name}")
async def update_feature_flag(flag_name: str, flag_config: dict):
    return await feature_flags.update_flag(flag_name, flag_config)

@app.get("/api/metrics")
async def get_metrics():
    return await metrics.get_deployment_metrics()

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("frontend/public/favicon.ico")

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/src"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
