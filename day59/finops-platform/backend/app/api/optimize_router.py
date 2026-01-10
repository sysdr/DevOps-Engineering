from fastapi import APIRouter, HTTPException
from typing import List
from ..services.optimizer import CostOptimizer
from ..models.optimization_models import Recommendation, CommitmentPlan

router = APIRouter()
optimizer = CostOptimizer()

@router.get("/recommendations")
async def get_recommendations():
    """Get cost optimization recommendations"""
    return await optimizer.generate_recommendations()

@router.post("/commitments")
async def analyze_commitments():
    """Analyze commitment opportunities"""
    try:
        await optimizer.analyze_commitments()
        return {"status": "analysis_complete"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/commitments/recommendations")
async def get_commitment_recommendations():
    """Get reserved instance recommendations"""
    return await optimizer.get_commitment_recommendations()

@router.get("/rightsizing")
async def get_rightsizing_recommendations():
    """Get pod rightsizing recommendations"""
    return await optimizer.get_rightsizing_recommendations()

@router.get("/waste")
async def get_waste_analysis():
    """Get waste analysis"""
    return {
        "idle_resources": await optimizer.find_idle_resources(),
        "oversized_pods": await optimizer.find_oversized_pods(),
        "unused_volumes": await optimizer.find_unused_volumes(),
        "total_waste": await optimizer.calculate_total_waste()
    }
