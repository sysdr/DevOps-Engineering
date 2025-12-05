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

app = FastAPI(title="Notification Service")

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "notification"}

@app.post("/api/notifications/send")
@track_sli("notification")
async def send_notification(notification: dict):
    await asyncio.sleep(random.uniform(0.2, 1.5))
    
    # Notification service has lower SLO (1% error rate acceptable)
    if random.random() < 0.01:
        raise HTTPException(status_code=500, detail="Email service unavailable")
    
    # Frequently slow (10% exceed SLO - acceptable for non-critical)
    if random.random() < 0.10:
        await asyncio.sleep(random.uniform(2.0, 3.0))
    
    return {
        "notification_id": f"NOT-{random.randint(10000, 99999)}",
        "status": "sent",
        "channel": notification.get("channel", "email"),
        "recipient": notification.get("recipient", "user@example.com")
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
