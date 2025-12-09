from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import json
import time
import random
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

app = FastAPI(title="Observability Cost Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cost Models (per GB/month)
COST_MODELS = {
    "hot_storage": 1.0,      # SSD, instant queries
    "warm_storage": 0.3,     # Compressed SSD
    "cold_storage": 0.05,    # Object storage
    "archive_storage": 0.01, # Glacier-class
    "trace_processing": 0.02,  # Per GB processed
    "metric_ingestion": 0.10,  # Per million metrics
    "log_ingestion": 0.50,     # Per GB
    "alert_sms": 0.01,         # Per message
    "alert_pagerduty": 0.25,   # Per incident
    "alert_webhook": 0.001,    # Per call
}

# Retention policies (days)
RETENTION_TIERS = {
    "hot": 7,
    "warm": 30,
    "cold": 90,
    "archive": 365
}

class MetricData(BaseModel):
    service: str
    metric_name: str
    cardinality: int
    samples_per_second: float
    data_size_mb: float

class TraceData(BaseModel):
    service: str
    traces_per_second: float
    avg_spans_per_trace: int
    error_rate: float

class CostOptimizer:
    def __init__(self):
        self.service_costs = defaultdict(lambda: {
            "metrics": 0.0,
            "traces": 0.0,
            "logs": 0.0,
            "storage": 0.0,
            "alerts": 0.0,
            "total": 0.0
        })
        self.sampling_rates = {}
        self.retention_policies = {}
        self.cost_history = []
        self.roi_metrics = {
            "mttr_reduction_hours": 0,
            "incidents_prevented": 0,
            "optimization_savings": 0
        }
        
    def calculate_metric_cost(self, metric: MetricData) -> Dict:
        """Calculate monthly cost for a metric"""
        # Time series count = cardinality
        time_series = metric.cardinality
        
        # Data points per month
        data_points_per_month = metric.samples_per_second * 60 * 60 * 24 * 30
        
        # Storage cost (distributed across tiers)
        hot_gb = metric.data_size_mb * 0.001 * 0.23  # 7 days of 30
        warm_gb = metric.data_size_mb * 0.001 * 0.77  # Rest in warm/cold
        
        hot_cost = hot_gb * COST_MODELS["hot_storage"]
        warm_cost = warm_gb * COST_MODELS["warm_storage"]
        
        # Ingestion cost
        ingestion_cost = (data_points_per_month / 1_000_000) * COST_MODELS["metric_ingestion"]
        
        total_cost = hot_cost + warm_cost + ingestion_cost
        
        return {
            "service": metric.service,
            "metric": metric.metric_name,
            "time_series_count": time_series,
            "hot_storage_cost": round(hot_cost, 2),
            "warm_storage_cost": round(warm_cost, 2),
            "ingestion_cost": round(ingestion_cost, 2),
            "total_monthly_cost": round(total_cost, 2),
            "cardinality_impact": (
                "HIGH" if time_series >= 1000 else "MEDIUM" if time_series >= 100 else "LOW"
            )
        }
    
    def calculate_trace_cost(self, trace: TraceData) -> Dict:
        """Calculate monthly cost for traces"""
        # Traces per month
        traces_per_month = trace.traces_per_second * 60 * 60 * 24 * 30
        
        # Assume 1KB per span
        gb_per_month = (traces_per_month * trace.avg_spans_per_trace * 1) / (1024 * 1024 * 1024)
        
        # Processing cost
        processing_cost = gb_per_month * COST_MODELS["trace_processing"]
        
        # Storage cost (7 days hot, rest warm)
        hot_gb = gb_per_month * 0.23
        warm_gb = gb_per_month * 0.77
        
        storage_cost = (hot_gb * COST_MODELS["hot_storage"]) + (warm_gb * COST_MODELS["warm_storage"])
        
        total_cost = processing_cost + storage_cost
        
        # Calculate optimal sampling rate
        optimal_sample_rate = self.calculate_optimal_sampling(trace.error_rate, total_cost)
        potential_savings = total_cost * (1 - optimal_sample_rate)
        
        return {
            "service": trace.service,
            "traces_per_month": int(traces_per_month),
            "processing_cost": round(processing_cost, 2),
            "storage_cost": round(storage_cost, 2),
            "total_monthly_cost": round(total_cost, 2),
            "current_sample_rate": 1.0,
            "optimal_sample_rate": optimal_sample_rate,
            "potential_monthly_savings": round(potential_savings, 2)
        }
    
    def calculate_optimal_sampling(self, error_rate: float, current_cost: float) -> float:
        """Calculate optimal sampling rate based on error rate and cost"""
        # Always sample 100% of errors
        error_sampling = error_rate * 1.0
        
        # For successful requests, sample based on cost/value ratio
        success_rate = 1.0 - error_rate
        
        if error_rate < 0.01:
            success_sampling = success_rate * 0.1  # Low error rates, aggressive downsampling
        elif current_cost < 100:  # Low cost, sample more
            success_sampling = success_rate * 0.5
        elif current_cost < 1000:  # Medium cost
            success_sampling = success_rate * 0.1
        else:  # High cost, aggressive sampling
            success_sampling = success_rate * 0.01
        
        optimal_rate = error_sampling + success_sampling
        return min(round(optimal_rate, 3), 1.0)
    
    def calculate_retention_savings(self, service: str, current_gb: float) -> Dict:
        """Calculate savings from optimized retention policies"""
        # Current: Everything in hot storage for 30 days
        current_cost = current_gb * COST_MODELS["hot_storage"]
        
        # Optimized: Multi-tier retention
        hot_gb = current_gb * 0.23   # 7 days
        warm_gb = current_gb * 0.33  # 10 days
        cold_gb = current_gb * 0.30  # 9 days
        archive_gb = current_gb * 0.14  # 4 days
        
        optimized_cost = (
            hot_gb * COST_MODELS["hot_storage"] +
            warm_gb * COST_MODELS["warm_storage"] +
            cold_gb * COST_MODELS["cold_storage"] +
            archive_gb * COST_MODELS["archive_storage"]
        )
        
        savings = current_cost - optimized_cost
        savings_pct = (savings / current_cost) * 100
        
        return {
            "service": service,
            "current_monthly_cost": round(current_cost, 2),
            "optimized_monthly_cost": round(optimized_cost, 2),
            "monthly_savings": round(savings, 2),
            "savings_percentage": round(savings_pct, 1),
            "retention_policy": {
                "hot": f"{RETENTION_TIERS['hot']} days",
                "warm": f"{RETENTION_TIERS['warm']-RETENTION_TIERS['hot']} days",
                "cold": f"{RETENTION_TIERS['cold']-RETENTION_TIERS['warm']} days",
                "archive": f"{RETENTION_TIERS['archive']-RETENTION_TIERS['cold']} days"
            }
        }
    
    def calculate_alert_cost(self, service: str, alerts_per_day: int, 
                            alert_types: Dict[str, int]) -> Dict:
        """Calculate monthly alerting costs"""
        days_per_month = 30
        
        costs = {}
        total_cost = 0.0
        
        for alert_type, count in alert_types.items():
            monthly_count = count * days_per_month
            cost_per_alert = COST_MODELS.get(f"alert_{alert_type}", 0)
            type_cost = monthly_count * cost_per_alert
            costs[alert_type] = {
                "count": monthly_count,
                "cost": round(type_cost, 2)
            }
            total_cost += type_cost
        
        # Calculate optimized cost with deduplication and throttling
        optimized_cost = total_cost * 0.4  # 60% reduction through smart alerting
        
        return {
            "service": service,
            "alerts_per_month": alerts_per_day * days_per_month,
            "cost_by_type": costs,
            "total_monthly_cost": round(total_cost, 2),
            "optimized_cost": round(optimized_cost, 2),
            "potential_savings": round(total_cost - optimized_cost, 2)
        }
    
    def calculate_roi(self, monthly_cost: float) -> Dict:
        """Calculate observability ROI"""
        # Value calculations
        mttr_value = self.roi_metrics["mttr_reduction_hours"] * 150  # $150/hour engineer time
        incident_value = self.roi_metrics["incidents_prevented"] * 100000  # $100K per incident
        optimization_value = self.roi_metrics["optimization_savings"]
        
        total_value = mttr_value + incident_value + optimization_value
        roi = ((total_value - monthly_cost) / monthly_cost) * 100 if monthly_cost > 0 else 0
        
        return {
            "monthly_observability_cost": round(monthly_cost, 2),
            "value_metrics": {
                "mttr_reduction_value": round(mttr_value, 2),
                "incident_prevention_value": round(incident_value, 2),
                "optimization_value": round(optimization_value, 2),
                "total_value": round(total_value, 2)
            },
            "roi_percentage": round(roi, 1),
            "roi_status": "POSITIVE" if roi > 0 else "NEGATIVE",
            "break_even_cost": round(total_value, 2)
        }

    def update_service_cost(self, service: str, category: str, cost: float):
        """Update service cost tracking"""
        self.service_costs[service][category] += cost
        self.service_costs[service]["total"] = sum(
            v for k, v in self.service_costs[service].items() if k != "total"
        )

# Global optimizer instance
optimizer = CostOptimizer()

# WebSocket connections
active_connections: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except:
        active_connections.remove(websocket)

async def broadcast_update(data: dict):
    """Broadcast updates to all connected clients"""
    for connection in active_connections:
        try:
            await connection.send_json(data)
        except:
            active_connections.remove(connection)

@app.post("/api/metrics/analyze")
async def analyze_metric_cost(metric: MetricData):
    """Analyze cost for a specific metric"""
    cost_analysis = optimizer.calculate_metric_cost(metric)
    optimizer.update_service_cost(metric.service, "metrics", cost_analysis["total_monthly_cost"])
    
    await broadcast_update({
        "type": "metric_cost_update",
        "data": cost_analysis
    })
    
    return cost_analysis

@app.post("/api/traces/analyze")
async def analyze_trace_cost(trace: TraceData):
    """Analyze cost for traces and recommend sampling"""
    cost_analysis = optimizer.calculate_trace_cost(trace)
    optimizer.update_service_cost(trace.service, "traces", cost_analysis["total_monthly_cost"])
    
    # Store optimal sampling rate
    optimizer.sampling_rates[trace.service] = cost_analysis["optimal_sample_rate"]
    
    await broadcast_update({
        "type": "trace_cost_update",
        "data": cost_analysis
    })
    
    return cost_analysis

@app.get("/api/retention/optimize/{service}")
async def optimize_retention(service: str, current_gb: float):
    """Calculate retention optimization savings"""
    savings = optimizer.calculate_retention_savings(service, current_gb)
    optimizer.update_service_cost(service, "storage", savings["optimized_monthly_cost"])
    
    await broadcast_update({
        "type": "retention_optimization",
        "data": savings
    })
    
    return savings

@app.get("/api/alerts/cost/{service}")
async def calculate_alert_costs(service: str, alerts_per_day: int = 100):
    """Calculate alerting costs"""
    alert_types = {
        "sms": int(alerts_per_day * 0.1),
        "pagerduty": int(alerts_per_day * 0.05),
        "webhook": int(alerts_per_day * 0.85)
    }
    
    alert_cost = optimizer.calculate_alert_cost(service, alerts_per_day, alert_types)
    optimizer.update_service_cost(service, "alerts", alert_cost["total_monthly_cost"])
    
    await broadcast_update({
        "type": "alert_cost_update",
        "data": alert_cost
    })
    
    return alert_cost

@app.get("/api/costs/breakdown")
async def get_cost_breakdown():
    """Get cost breakdown by service"""
    breakdown = []
    total_cost = 0.0
    
    for service, costs in optimizer.service_costs.items():
        breakdown.append({
            "service": service,
            **costs
        })
        total_cost += costs["total"]
    
    # Sort by total cost descending
    breakdown.sort(key=lambda x: x["total"], reverse=True)
    
    return {
        "services": breakdown,
        "total_monthly_cost": round(total_cost, 2),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/roi/calculate")
async def calculate_roi():
    """Calculate observability ROI"""
    total_cost = sum(costs["total"] for costs in optimizer.service_costs.values())
    roi = optimizer.calculate_roi(total_cost)
    
    await broadcast_update({
        "type": "roi_update",
        "data": roi
    })
    
    return roi

@app.get("/api/recommendations")
async def get_recommendations():
    """Get cost optimization recommendations"""
    recommendations = []
    
    # Analyze service costs for recommendations
    for service, costs in optimizer.service_costs.items():
        if costs["metrics"] > 1000:
            recommendations.append({
                "service": service,
                "type": "HIGH_CARDINALITY",
                "severity": "HIGH",
                "message": f"Service has high metric costs (${costs['metrics']:.2f}/mo). Review cardinality.",
                "potential_savings": round(costs["metrics"] * 0.4, 2)
            })
        
        if costs["traces"] > 500:
            sample_rate = optimizer.sampling_rates.get(service, 1.0)
            if sample_rate > 0.5:
                recommendations.append({
                    "service": service,
                    "type": "AGGRESSIVE_SAMPLING",
                    "severity": "MEDIUM",
                    "message": f"Enable intelligent sampling (current: 100%, recommended: {sample_rate*100:.1f}%)",
                    "potential_savings": round(costs["traces"] * (1 - sample_rate), 2)
                })
        
        if costs["alerts"] > 100:
            recommendations.append({
                "service": service,
                "type": "ALERT_OPTIMIZATION",
                "severity": "MEDIUM",
                "message": f"High alert costs (${costs['alerts']:.2f}/mo). Implement deduplication.",
                "potential_savings": round(costs["alerts"] * 0.6, 2)
            })
    
    # Sort by potential savings
    recommendations.sort(key=lambda x: x["potential_savings"], reverse=True)
    
    return {
        "recommendations": recommendations[:10],  # Top 10
        "total_potential_savings": sum(r["potential_savings"] for r in recommendations)
    }

@app.post("/api/roi/update")
async def update_roi_metrics(mttr_hours: float = 0, incidents_prevented: int = 0, 
                             optimization_savings: float = 0):
    """Update ROI tracking metrics"""
    optimizer.roi_metrics["mttr_reduction_hours"] += mttr_hours
    optimizer.roi_metrics["incidents_prevented"] += incidents_prevented
    optimizer.roi_metrics["optimization_savings"] += optimization_savings
    
    return {"status": "updated", "metrics": optimizer.roi_metrics}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cost-optimizer"}

# Background task to simulate real-time cost tracking
async def simulate_cost_tracking():
    """Simulate real-time cost tracking for demo"""
    services = ["api-gateway", "user-service", "payment-service", "inventory-service"]
    
    while True:
        await asyncio.sleep(5)
        
        # Simulate metric analysis
        service = random.choice(services)
        metric = MetricData(
            service=service,
            metric_name=f"http_requests_total",
            cardinality=random.randint(100, 2000),
            samples_per_second=random.uniform(10, 100),
            data_size_mb=random.uniform(1, 50)
        )
        
        await analyze_metric_cost(metric)
        
        # Simulate trace analysis
        trace = TraceData(
            service=service,
            traces_per_second=random.uniform(5, 50),
            avg_spans_per_trace=random.randint(5, 20),
            error_rate=random.uniform(0.001, 0.05)
        )
        
        await analyze_trace_cost(trace)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulate_cost_tracking())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
