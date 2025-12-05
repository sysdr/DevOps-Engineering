from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import uvicorn
import random
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from shared.sli_decorator import track_sli

app = FastAPI(title="Order Service")

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "order"}

@app.post("/api/orders")
@track_sli("order")
async def create_order(order: dict):
    # Simulate variable latency
    await asyncio.sleep(random.uniform(0.05, 0.4))
    
    # Simulate occasional failures (1% error rate baseline)
    if random.random() < 0.01:
        raise HTTPException(status_code=500, detail="Order processing failed")
    
    # Simulate slow requests (5% exceed SLO)
    if random.random() < 0.05:
        await asyncio.sleep(random.uniform(0.5, 1.0))
    
    return {
        "order_id": f"ORD-{random.randint(10000, 99999)}",
        "status": "created",
        "items": order.get("items", []),
        "total": random.uniform(50, 500)
    }

@app.get("/api/orders/{order_id}")
@track_sli("order")
async def get_order(order_id: str):
    await asyncio.sleep(random.uniform(0.02, 0.15))
    
    if random.random() < 0.005:
        raise HTTPException(status_code=500, detail="Database error")
    
    return {
        "order_id": order_id,
        "status": random.choice(["pending", "processing", "completed"]),
        "created_at": "2025-06-01T10:00:00Z"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
