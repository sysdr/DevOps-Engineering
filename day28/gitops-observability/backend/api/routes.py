"""API routes for GitOps Observability Platform"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter()

from models.database import Database
from calculators.sli_calculator import SLICalculator
from evaluators.slo_evaluator import SLOEvaluator

db = Database()
sli_calculator = SLICalculator(db)
slo_evaluator = SLOEvaluator(db)

@router.get("/api/metrics")
async def get_metrics():
    return await db.get_latest_metrics()

@router.get("/api/metrics/history")
async def get_metrics_history(window_minutes: int = 60):
    return await db.get_metrics_in_window(window_minutes)

@router.get("/api/deployments")
async def get_deployments(limit: int = 50):
    return await db.get_recent_deployments(limit)

@router.get("/api/slis")
async def get_slis():
    return await sli_calculator.calculate()

@router.get("/api/slos")
async def get_slo_configs():
    return db.get_slo_configs()

@router.get("/api/slos/evaluation")
async def get_slo_evaluations():
    slis = await sli_calculator.calculate()
    return await slo_evaluator.evaluate(slis)

@router.get("/api/error-budgets")
async def get_error_budgets():
    return await db.get_error_budgets()

@router.get("/api/incidents")
async def get_incidents():
    return await db.get_active_incidents()

@router.post("/api/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str):
    await db.resolve_incident(incident_id)
    return {"status": "resolved", "incident_id": incident_id}

@router.get("/api/dashboard/summary")
async def get_dashboard_summary():
    slis = await sli_calculator.calculate()
    evaluations = await slo_evaluator.evaluate(slis)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "slis": slis,
        "slo_evaluations": evaluations,
        "active_incidents": len(await db.get_active_incidents()),
        "recent_deployments": len(await db.get_deployments_in_window(60)),
        "system_health": _calculate_system_health(evaluations)
    }

def _calculate_system_health(evaluations):
    if not evaluations:
        return "unknown"
    
    statuses = [e["status"] for e in evaluations]
    if "critical" in statuses:
        return "critical"
    elif "warning" in statuses:
        return "degraded"
    return "healthy"
