from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import logging
from datetime import datetime, timedelta
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cost Optimizer")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PricingData(BaseModel):
    timestamp: datetime
    on_demand_price: float
    spot_price: float
    savings_percentage: float

class CostAnalytics(BaseModel):
    total_cost_current: float
    potential_cost_optimized: float
    savings_amount: float
    savings_percentage: float
    recommendations: List[str]

class WorkloadMigration(BaseModel):
    job_id: str
    from_node_type: str
    to_node_type: str
    cost_savings_per_hour: float

# Simulated cost tracking
cost_history: List[Dict] = []
current_spend = {
    "on_demand_gpu_hours": 0.0,
    "spot_gpu_hours": 0.0,
    "mig_hours": 0.0
}

COST_ON_DEMAND = 3.50
COST_SPOT_BASE = 1.40
COST_MIG = 0.75

@app.on_event("startup")
async def startup():
    logger.info("Cost Optimizer started")
    # Initialize with some historical data
    for i in range(24):
        spot_variance = random.uniform(0.8, 1.2)
        cost_history.append({
            "timestamp": (datetime.now() - timedelta(hours=24-i)).isoformat(),
            "on_demand_price": COST_ON_DEMAND,
            "spot_price": COST_SPOT_BASE * spot_variance,
            "savings_percentage": ((COST_ON_DEMAND - COST_SPOT_BASE * spot_variance) / COST_ON_DEMAND) * 100
        })

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "cost-optimizer"}

@app.get("/pricing/current", response_model=PricingData)
async def get_current_pricing():
    """Get current GPU pricing"""
    spot_variance = random.uniform(0.85, 1.15)
    spot_price = COST_SPOT_BASE * spot_variance
    savings = ((COST_ON_DEMAND - spot_price) / COST_ON_DEMAND) * 100
    
    return PricingData(
        timestamp=datetime.now(),
        on_demand_price=COST_ON_DEMAND,
        spot_price=spot_price,
        savings_percentage=savings
    )

@app.get("/pricing/history")
async def get_pricing_history():
    """Get historical pricing data"""
    return {"history": cost_history[-24:]}

@app.get("/analytics", response_model=CostAnalytics)
async def get_cost_analytics():
    """Get cost analytics and optimization recommendations"""
    # Calculate current costs
    current_cost = (
        current_spend["on_demand_gpu_hours"] * COST_ON_DEMAND +
        current_spend["spot_gpu_hours"] * COST_SPOT_BASE +
        current_spend["mig_hours"] * COST_MIG
    )
    
    # Calculate optimized costs (assuming 60% can move to spot/MIG)
    optimizable_hours = current_spend["on_demand_gpu_hours"] * 0.6
    optimized_cost = (
        current_spend["on_demand_gpu_hours"] * 0.4 * COST_ON_DEMAND +
        optimizable_hours * COST_SPOT_BASE +
        current_spend["spot_gpu_hours"] * COST_SPOT_BASE +
        current_spend["mig_hours"] * COST_MIG
    )
    
    savings = current_cost - optimized_cost
    savings_pct = (savings / max(current_cost, 0.01)) * 100
    
    recommendations = []
    if current_spend["on_demand_gpu_hours"] > 10:
        recommendations.append("Move checkpoint-enabled jobs to spot instances (60% cost reduction)")
    if current_spend["on_demand_gpu_hours"] > 5:
        recommendations.append("Enable MIG for small inference workloads (78% cost reduction)")
    if savings_pct > 30:
        recommendations.append("Implement auto-scaling to shut down idle GPUs")
    
    return CostAnalytics(
        total_cost_current=current_cost,
        potential_cost_optimized=optimized_cost,
        savings_amount=savings,
        savings_percentage=savings_pct,
        recommendations=recommendations
    )

@app.post("/track/usage")
async def track_usage(node_type: str, hours: float):
    """Track GPU usage"""
    if node_type == "on-demand":
        current_spend["on_demand_gpu_hours"] += hours
    elif node_type == "spot":
        current_spend["spot_gpu_hours"] += hours
    elif node_type == "mig":
        current_spend["mig_hours"] += hours
    
    return {"message": "Usage tracked", "type": node_type, "hours": hours}

@app.get("/recommendations/migrations")
async def get_migration_recommendations():
    """Get workload migration recommendations"""
    recommendations = []
    
    # Simulate finding migration opportunities
    if current_spend["on_demand_gpu_hours"] > 5:
        recommendations.append(WorkloadMigration(
            job_id="training-job-123",
            from_node_type="on-demand-full-gpu",
            to_node_type="spot-gpu",
            cost_savings_per_hour=COST_ON_DEMAND - COST_SPOT_BASE
        ))
    
    if current_spend["on_demand_gpu_hours"] > 10:
        recommendations.append(WorkloadMigration(
            job_id="inference-job-456",
            from_node_type="on-demand-full-gpu",
            to_node_type="mig-instance",
            cost_savings_per_hour=COST_ON_DEMAND - COST_MIG
        ))
    
    return {"recommendations": recommendations}

@app.get("/metrics")
async def get_metrics():
    """Get cost metrics for monitoring"""
    total_spend = (
        current_spend["on_demand_gpu_hours"] * COST_ON_DEMAND +
        current_spend["spot_gpu_hours"] * COST_SPOT_BASE +
        current_spend["mig_hours"] * COST_MIG
    )
    
    return {
        "total_spend": total_spend,
        "on_demand_hours": current_spend["on_demand_gpu_hours"],
        "spot_hours": current_spend["spot_gpu_hours"],
        "mig_hours": current_spend["mig_hours"],
        "potential_savings": total_spend * 0.4  # 40% potential savings
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
