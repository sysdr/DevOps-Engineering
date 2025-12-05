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

app = FastAPI(title="Inventory Service")

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "inventory"}

@app.post("/api/inventory/check")
@track_sli("inventory")
async def check_inventory(items: dict):
    await asyncio.sleep(random.uniform(0.08, 0.6))
    
    # Moderate error rate (0.5%)
    if random.random() < 0.005:
        raise HTTPException(status_code=500, detail="Inventory database timeout")
    
    # Some slow queries (3% exceed SLO)
    if random.random() < 0.03:
        await asyncio.sleep(random.uniform(0.8, 1.5))
    
    return {
        "available": random.choice([True, False]),
        "quantity": random.randint(0, 100),
        "warehouse": random.choice(["US-EAST", "US-WEST", "EU-CENTRAL"])
    }

@app.post("/api/inventory/reserve")
@track_sli("inventory")
async def reserve_inventory(reservation: dict):
    await asyncio.sleep(random.uniform(0.1, 0.5))
    
    if random.random() < 0.008:
        raise HTTPException(status_code=500, detail="Reservation failed")
    
    return {
        "reservation_id": f"RES-{random.randint(10000, 99999)}",
        "status": "reserved",
        "expires_at": "2025-06-01T11:00:00Z"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
