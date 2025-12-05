from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import redis
import httpx
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from shared.config import Config

app = FastAPI(title="SLO Calculator Service")

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

async def query_prometheus(query: str) -> float:
    """Query Prometheus and return scalar result"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{Config.PROMETHEUS_URL}/api/v1/query",
                params={"query": query},
                timeout=10.0
            )
            data = response.json()
            if data['status'] == 'success' and data['data']['result']:
                return float(data['data']['result'][0]['value'][1])
            return 0.0
    except Exception as e:
        print(f"Prometheus query error: {e}")
        return 0.0

async def calculate_error_rate(service: str, window: str) -> float:
    """Calculate error rate for a service over a time window"""
    query = f'''
    sum(rate(http_requests_total{{service="{service}", status=~"5.."}}[{window}])) /
    sum(rate(http_requests_total{{service="{service}"}}[{window}]))
    '''
    error_rate = await query_prometheus(query)
    return error_rate * 100  # Convert to percentage

async def calculate_latency_percentile(service: str, percentile: int, window: str) -> float:
    """Calculate latency percentile for a service"""
    query = f'''
    histogram_quantile(
        {percentile / 100},
        sum(rate(http_request_duration_seconds_bucket{{service="{service}"}}[{window}])) by (le)
    )
    '''
    latency = await query_prometheus(query)
    return latency * 1000  # Convert to milliseconds

async def calculate_slo_metrics():
    """Background task to calculate SLO metrics every minute"""
    while True:
        try:
            for service, slo_config in Config.SLOS.items():
                target_availability = slo_config['availability']
                error_budget = 100 - target_availability
                
                for window in Config.TIME_WINDOWS:
                    # Calculate error rate
                    error_rate = await calculate_error_rate(service, window)
                    
                    # Calculate burn rate
                    burn_rate = error_rate / error_budget if error_budget > 0 else 0
                    
                    # Calculate budget remaining
                    budget_remaining = error_budget - error_rate
                    
                    # Calculate time to exhaustion (in hours)
                    if error_rate > 0:
                        window_hours = {'1h': 1, '6h': 6, '24h': 24, '72h': 72}[window]
                        time_to_exhaustion = (budget_remaining / error_rate) * window_hours
                    else:
                        time_to_exhaustion = float('inf')
                    
                    # Store in Redis
                    metrics = {
                        'error_rate': round(error_rate, 4),
                        'burn_rate': round(burn_rate, 2),
                        'budget_remaining': round(budget_remaining, 4),
                        'time_to_exhaustion': round(time_to_exhaustion, 2) if time_to_exhaustion != float('inf') else 999999,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    redis_client.setex(
                        f"slo:{service}:{window}",
                        7200,  # 2 hour TTL
                        json.dumps(metrics)
                    )
                
                # Calculate latency percentiles
                p95_latency = await calculate_latency_percentile(service, 95, '1h')
                p99_latency = await calculate_latency_percentile(service, 99, '1h')
                
                latency_metrics = {
                    'p95': round(p95_latency, 2),
                    'p99': round(p99_latency, 2),
                    'p95_slo': slo_config['latency_p95'],
                    'p99_slo': slo_config['latency_p99'],
                    'p95_violation': p95_latency > slo_config['latency_p95'],
                    'p99_violation': p99_latency > slo_config['latency_p99'],
                    'timestamp': datetime.now().isoformat()
                }
                
                redis_client.setex(
                    f"latency:{service}",
                    7200,
                    json.dumps(latency_metrics)
                )
            
            print(f"[{datetime.now()}] SLO metrics calculated for all services")
            
        except Exception as e:
            print(f"Error calculating SLO metrics: {e}")
        
        await asyncio.sleep(60)  # Run every minute

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(calculate_slo_metrics())

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "slo-calculator"}

@app.get("/api/slo/{service}")
async def get_slo_metrics(service: str):
    """Get SLO metrics for a specific service"""
    metrics = {}
    
    for window in Config.TIME_WINDOWS:
        key = f"slo:{service}:{window}"
        data = redis_client.get(key)
        if data:
            metrics[window] = json.loads(data)
    
    # Get latency metrics
    latency_key = f"latency:{service}"
    latency_data = redis_client.get(latency_key)
    if latency_data:
        metrics['latency'] = json.loads(latency_data)
    
    # Get SLO configuration
    metrics['slo_config'] = Config.SLOS.get(service, {})
    
    return metrics

@app.get("/api/slo/all/summary")
async def get_all_slo_summary():
    """Get summary of all services' SLO compliance"""
    summary = {}
    
    for service in Config.SLOS.keys():
        service_summary = {
            'windows': {},
            'latency': {}
        }
        
        # Get 1h window (most recent) for summary
        key = f"slo:{service}:1h"
        data = redis_client.get(key)
        if data:
            metrics = json.loads(data)
            service_summary['windows']['1h'] = metrics
        
        # Get latency
        latency_key = f"latency:{service}"
        latency_data = redis_client.get(latency_key)
        if latency_data:
            service_summary['latency'] = json.loads(latency_data)
        
        service_summary['slo_config'] = Config.SLOS[service]
        summary[service] = service_summary
    
    return summary

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
