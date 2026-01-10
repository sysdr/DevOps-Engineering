from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime, timedelta
from ..services.cost_collector import CostCollector
from ..models.cost_models import CostSummary, NamespaceCost
import asyncio

router = APIRouter()
collector = CostCollector()

# Flag to track if initial collection has been done
_collection_initialized = False

async def ensure_collection_done():
    """Ensure cost collection has been performed at least once"""
    global _collection_initialized
    if not _collection_initialized:
        try:
            await collector.collect_metrics()
            _collection_initialized = True
        except Exception as e:
            print(f"Error in initial cost collection: {e}")

@router.post("/collect")
async def trigger_collection():
    """Trigger immediate cost collection"""
    try:
        await collector.collect_metrics()
        return {"status": "success", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/total")
async def get_total_cost():
    """Get total cluster cost"""
    await ensure_collection_done()
    return {
        "total": collector.get_total_cost(),
        "currency": "USD",
        "period": "current_month"
    }

@router.get("/namespaces")
async def get_namespace_costs():
    """Get cost breakdown by namespace"""
    await ensure_collection_done()
    costs = collector.get_namespace_costs()
    return {"namespaces": costs, "total": sum(costs.values())}

@router.get("/trend")
async def get_cost_trend(days: int = 30):
    """Get cost trend over time"""
    await ensure_collection_done()
    trend = collector.get_cost_trend(days)
    return {"trend": trend, "period_days": days}

@router.get("/breakdown")
async def get_cost_breakdown():
    """Get detailed cost breakdown"""
    await ensure_collection_done()
    return {
        "compute": collector.get_compute_cost(),
        "storage": collector.get_storage_cost(),
        "network": collector.get_network_cost(),
        "total": collector.get_total_cost()
    }
