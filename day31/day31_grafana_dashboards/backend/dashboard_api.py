from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List
import json
from pathlib import Path
from grafana_api import GrafanaAPI

app = FastAPI(title="Dashboard Management API")

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

grafana = GrafanaAPI()

class DashboardRequest(BaseModel):
    title: str
    tags: List[str] = []
    refresh: str = "5s"

class TemplateDeployRequest(BaseModel):
    filename: str
    title: str | None = None

@app.get("/")
async def root():
    return {
        "service": "Dashboard Management API",
        "version": "1.0.0",
        "endpoints": {
            "dashboards": "/api/dashboards",
            "templates": "/api/templates",
            "grafana_status": "/api/grafana/status"
        }
    }

@app.options("/api/dashboards")
async def dashboards_options():
    """Handle CORS preflight for dashboards endpoint"""
    return Response(status_code=204, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    })

@app.get("/api/dashboards")
async def list_dashboards():
    """List all Grafana dashboards"""
    dashboards = grafana.get_dashboards()
    return {"dashboards": dashboards, "count": len(dashboards)}

@app.get("/api/dashboards/{uid}")
async def get_dashboard(uid: str):
    """Get specific dashboard"""
    dashboard = grafana.get_dashboard(uid)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "grafana" / "dashboards"


@app.get("/api/templates")
async def list_templates():
    """List available dashboard templates"""
    if not TEMPLATES_DIR.exists():
        return {"templates": [], "count": 0}
    
    templates = []
    for file in TEMPLATES_DIR.glob("*.json"):
        try:
            with open(file) as f:
                data = json.load(f)
                # Handle both wrapped and unwrapped dashboard JSON
                dashboard_data = data.get("dashboard", data)
                templates.append({
                    "filename": file.name,
                    "title": dashboard_data.get("title", "Unknown"),
                    "tags": dashboard_data.get("tags", []),
                    "uid": dashboard_data.get("uid", "")
                })
        except Exception as e:
            print(f"Error reading {file}: {e}")
    
    return {"templates": templates, "count": len(templates)}

@app.get("/api/grafana/status")
async def grafana_status():
    """Check Grafana availability"""
    health = grafana.get_health()
    return health

@app.post("/api/dashboards/deploy")
async def deploy_dashboard(request: DashboardRequest):
    """Deploy a new dashboard from template"""
    # Simple dashboard creation
    dashboard = {
        "title": request.title,
        "tags": request.tags,
        "timezone": "browser",
        "schemaVersion": 16,
        "version": 0,
        "refresh": request.refresh
    }
    
    result = grafana.create_dashboard(dashboard)
    return result


@app.post("/api/templates/deploy")
async def deploy_template(request: TemplateDeployRequest):
    """Deploy a dashboard from a saved template"""
    template_path = TEMPLATES_DIR / request.filename
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        with open(template_path) as f:
            template_data = json.load(f)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid template JSON: {exc}") from exc

    dashboard_payload = template_data.get("dashboard", template_data)
    # Ensure Grafana creates a new dashboard
    dashboard_payload = dict(dashboard_payload)
    dashboard_payload["id"] = None
    dashboard_payload["uid"] = dashboard_payload.get("uid") or None

    if request.title:
        dashboard_payload["title"] = request.title

    result = grafana.create_dashboard(dashboard_payload)
    if "status" in result and result["status"] == "success":
        message = f"Template '{request.filename}' deployed successfully"
    else:
        message = result.get("message", "Template deployment response received")

    return {
        "status": "success" if result.get("status") == "success" else "pending",
        "message": message,
        "grafana_response": result
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
