from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import redis
import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List
from enum import Enum

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from shared.config import Config

app = FastAPI(title="Policy Engine Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    decode_responses=True
)

class BudgetState(str, Enum):
    HEALTHY = "HEALTHY"
    CAUTION = "CAUTION"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EXHAUSTED = "EXHAUSTED"

class AlertLevel(str, Enum):
    LOG = "LOG"
    TICKET = "TICKET"
    PAGE = "PAGE"
    CRITICAL = "CRITICAL"

def determine_budget_state(budget_remaining: float) -> BudgetState:
    """Determine budget state based on remaining budget percentage"""
    if budget_remaining <= 0:
        return BudgetState.EXHAUSTED
    elif budget_remaining < 10:
        return BudgetState.CRITICAL
    elif budget_remaining < 25:
        return BudgetState.WARNING
    elif budget_remaining < 50:
        return BudgetState.CAUTION
    else:
        return BudgetState.HEALTHY

def determine_alert_level(burn_rate: float) -> AlertLevel:
    """Determine alert level based on burn rate"""
    if burn_rate >= Config.BURN_RATE_THRESHOLDS['critical']:
        return AlertLevel.CRITICAL
    elif burn_rate >= Config.BURN_RATE_THRESHOLDS['page']:
        return AlertLevel.PAGE
    elif burn_rate >= Config.BURN_RATE_THRESHOLDS['ticket']:
        return AlertLevel.TICKET
    elif burn_rate >= Config.BURN_RATE_THRESHOLDS['log']:
        return AlertLevel.LOG
    else:
        return None

def should_block_deployment(service: str, budget_state: BudgetState, burn_rate: float) -> bool:
    """Determine if deployments should be blocked"""
    if budget_state == BudgetState.EXHAUSTED:
        return True
    if budget_state == BudgetState.CRITICAL and burn_rate >= 10:
        return True
    return False

async def evaluate_policies():
    """Background task to evaluate policies and create alerts"""
    while True:
        try:
            for service in Config.SLOS.keys():
                # Get 1h window metrics (most sensitive)
                key = f"slo:{service}:1h"
                data = redis_client.get(key)
                
                if not data:
                    continue
                
                metrics = json.loads(data)
                burn_rate = metrics['burn_rate']
                budget_remaining = metrics['budget_remaining']
                
                # Determine states
                budget_state = determine_budget_state(budget_remaining)
                alert_level = determine_alert_level(burn_rate)
                deployment_blocked = should_block_deployment(service, budget_state, burn_rate)
                
                # Store policy decision
                policy = {
                    'service': service,
                    'budget_state': budget_state,
                    'alert_level': alert_level,
                    'deployment_blocked': deployment_blocked,
                    'burn_rate': burn_rate,
                    'budget_remaining': budget_remaining,
                    'timestamp': datetime.now().isoformat()
                }
                
                redis_client.setex(
                    f"policy:{service}",
                    3600,
                    json.dumps(policy)
                )
                
                # Create alert if needed
                if alert_level:
                    alert = {
                        'service': service,
                        'level': alert_level,
                        'message': f"{service} burn rate at {burn_rate:.2f}x (threshold: {Config.BURN_RATE_THRESHOLDS[alert_level.lower()]}x)",
                        'burn_rate': burn_rate,
                        'budget_state': budget_state,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    # Store alert (append to list)
                    redis_client.lpush(f"alerts:{service}", json.dumps(alert))
                    redis_client.ltrim(f"alerts:{service}", 0, 99)  # Keep last 100 alerts
                    
                    print(f"[ALERT {alert_level}] {alert['message']}")
                
                if deployment_blocked:
                    print(f"[POLICY] Deployments BLOCKED for {service} - Budget State: {budget_state}")
            
        except Exception as e:
            print(f"Error evaluating policies: {e}")
        
        await asyncio.sleep(60)  # Evaluate every minute

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(evaluate_policies())

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "policy-engine"}

@app.get("/api/policy/{service}")
async def get_policy(service: str):
    """Get current policy state for a service"""
    key = f"policy:{service}"
    data = redis_client.get(key)
    
    if data:
        return json.loads(data)
    
    return {"error": "No policy data found"}

@app.get("/api/policy/all/status")
async def get_all_policies():
    """Get policy status for all services"""
    policies = {}
    
    for service in Config.SLOS.keys():
        key = f"policy:{service}"
        data = redis_client.get(key)
        if data:
            policies[service] = json.loads(data)
    
    return policies

@app.get("/api/alerts/{service}")
async def get_alerts(service: str, limit: int = 10):
    """Get recent alerts for a service"""
    alerts_data = redis_client.lrange(f"alerts:{service}", 0, limit - 1)
    alerts = [json.loads(a) for a in alerts_data]
    return alerts

@app.get("/api/alerts/all/recent")
async def get_all_recent_alerts(limit: int = 20):
    """Get recent alerts across all services"""
    all_alerts = []
    
    for service in Config.SLOS.keys():
        alerts_data = redis_client.lrange(f"alerts:{service}", 0, 9)
        alerts = [json.loads(a) for a in alerts_data]
        all_alerts.extend(alerts)
    
    # Sort by timestamp
    all_alerts.sort(key=lambda x: x['created_at'], reverse=True)
    return all_alerts[:limit]

@app.post("/api/deployment/check/{service}")
async def check_deployment_allowed(service: str):
    """Check if deployment is allowed for a service"""
    key = f"policy:{service}"
    data = redis_client.get(key)
    
    if not data:
        return {"allowed": True, "reason": "No policy data available"}
    
    policy = json.loads(data)
    
    if policy['deployment_blocked']:
        return {
            "allowed": False,
            "reason": f"Deployment blocked: Budget state is {policy['budget_state']}, burn rate at {policy['burn_rate']:.2f}x",
            "policy": policy
        }
    
    return {
        "allowed": True,
        "reason": "Deployment permitted",
        "policy": policy
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)
