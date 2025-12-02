from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx
import asyncio
import json
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="APM Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JAEGER_QUERY_URL = "http://localhost:16686"

active_connections = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket client connected. Total connections: {len(active_connections)}")
    try:
        while True:
            await asyncio.sleep(2)
            # Send metrics update
            try:
                metrics = await get_live_metrics()
                await websocket.send_json(metrics)
            except Exception as metric_error:
                logger.warning(f"Error sending metrics: {metric_error}")
                # Send a minimal response instead of failing
                await websocket.send_json({
                    "timestamp": datetime.now().isoformat(),
                    "error": "Metrics temporarily unavailable"
                })
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(active_connections)}")

async def get_live_metrics():
    """Fetch metrics from Jaeger and aggregate"""
    try:
        async with httpx.AsyncClient() as client:
            # Query recent traces
            lookback = int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000000)
            response = await client.get(
                f"{JAEGER_QUERY_URL}/api/traces",
                params={"service": "order-service", "limit": 100, "start": lookback},
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                traces = data.get("data", [])
                
                # Aggregate metrics
                service_latencies = defaultdict(list)
                error_count = 0
                total_requests = len(traces)
                
                for trace in traces:
                    for span in trace.get("spans", []):
                        service = span.get("process", {}).get("serviceName", "unknown")
                        duration_ms = span.get("duration", 0) / 1000
                        service_latencies[service].append(duration_ms)
                        
                        # Check for errors
                        tags = {tag["key"]: tag["value"] for tag in span.get("tags", [])}
                        if tags.get("error") == "true":
                            error_count += 1
                
                # Calculate percentiles
                metrics_by_service = {}
                for service, latencies in service_latencies.items():
                    if latencies:
                        sorted_lat = sorted(latencies)
                        p50_idx = int(len(sorted_lat) * 0.5)
                        p95_idx = int(len(sorted_lat) * 0.95)
                        p99_idx = int(len(sorted_lat) * 0.99)
                        
                        metrics_by_service[service] = {
                            "p50": sorted_lat[p50_idx],
                            "p95": sorted_lat[p95_idx],
                            "p99": sorted_lat[p99_idx],
                            "count": len(latencies)
                        }
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "total_requests": total_requests,
                    "error_count": error_count,
                    "error_rate": (error_count / total_requests * 100) if total_requests > 0 else 0,
                    "services": metrics_by_service
                }
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
    
    return {"timestamp": datetime.now().isoformat(), "error": "Unable to fetch metrics"}

@app.get("/api/services")
async def get_services():
    """Get list of services from Jaeger"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{JAEGER_QUERY_URL}/api/services", timeout=5.0)
            if response.status_code == 200:
                return {"services": response.json().get("data", [])}
    except Exception as e:
        logger.error(f"Error fetching services: {e}")
    return {"services": []}

@app.get("/api/traces/recent")
async def get_recent_traces(limit: int = 20):
    """Get recent traces"""
    try:
        async with httpx.AsyncClient() as client:
            lookback = int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000000)
            response = await client.get(
                f"{JAEGER_QUERY_URL}/api/traces",
                params={"service": "order-service", "limit": limit, "start": lookback},
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Error fetching traces: {e}")
    return {"data": []}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
