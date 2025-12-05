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

app = FastAPI(title="Payment Service")

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "payment"}

@app.post("/api/payments")
@track_sli("payment")
async def process_payment(payment: dict):
    await asyncio.sleep(random.uniform(0.1, 0.8))
    
    # Payment service has higher reliability (0.05% error rate)
    if random.random() < 0.0005:
        raise HTTPException(status_code=500, detail="Payment gateway error")
    
    # Occasional slow payments (2% exceed SLO)
    if random.random() < 0.02:
        await asyncio.sleep(random.uniform(1.0, 2.0))
    
    return {
        "payment_id": f"PAY-{random.randint(10000, 99999)}",
        "status": "completed",
        "amount": payment.get("amount", 0),
        "method": payment.get("method", "credit_card")
    }

@app.get("/api/payments/{payment_id}")
@track_sli("payment")
async def get_payment(payment_id: str):
    await asyncio.sleep(random.uniform(0.05, 0.2))
    
    return {
        "payment_id": payment_id,
        "status": "completed",
        "timestamp": "2025-06-01T10:05:00Z"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
