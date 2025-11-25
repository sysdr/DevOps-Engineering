from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_config import setup_logger
import random
import time

app = FastAPI(title="Payment Service")
logger = setup_logger("payment-service")

class PaymentRequest(BaseModel):
    order_id: int
    amount: float
    payment_method: str

payments_db = {}
request_count = 0
error_count = 0

@app.post("/api/payments")
async def process_payment(request: PaymentRequest):
    global request_count, error_count
    request_count += 1
    
    start_time = time.time()
    
    try:
        # Simulate various scenarios
        scenario = random.random()
        
        if scenario < 0.02:  # 2% - payment gateway timeout
            logger.error("Payment gateway timeout", extra={
                "event": "payment_timeout",
                "order_id": request.order_id,
                "amount": request.amount,
                "timeout_ms": 15000
            })
            error_count += 1
            raise HTTPException(status_code=504, detail="Payment gateway timeout")
        
        if scenario < 0.06:  # 4% - payment declined
            logger.warning("Payment declined", extra={
                "event": "payment_declined",
                "order_id": request.order_id,
                "amount": request.amount,
                "payment_method": request.payment_method,
                "reason": "insufficient_funds"
            })
            error_count += 1
            raise HTTPException(status_code=402, detail="Payment declined")
        
        if scenario < 0.08:  # 2% - fraud detection triggered
            logger.warning("Fraud detection triggered", extra={
                "event": "fraud_detected",
                "order_id": request.order_id,
                "amount": request.amount,
                "risk_score": 0.85
            })
            error_count += 1
            raise HTTPException(status_code=403, detail="Payment blocked - fraud detection")
        
        transaction_id = f"txn-{int(time.time())}-{request.order_id}"
        payment_data = {
            "transaction_id": transaction_id,
            "order_id": request.order_id,
            "amount": request.amount,
            "payment_method": request.payment_method,
            "status": "completed",
            "processed_at": time.time()
        }
        payments_db[transaction_id] = payment_data
        
        duration_ms = (time.time() - start_time) * 1000
        logger.info("Payment processed successfully", extra={
            "event": "payment_success",
            "transaction_id": transaction_id,
            "order_id": request.order_id,
            "amount": request.amount,
            "payment_method": request.payment_method,
            "duration_ms": round(duration_ms, 2)
        })
        
        return {
            "transaction_id": transaction_id,
            "status": "completed",
            "amount": request.amount
        }
    
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error("Payment processing failed", extra={
            "event": "payment_error",
            "error": str(e),
            "order_id": request.order_id,
            "duration_ms": round(duration_ms, 2)
        })
        error_count += 1
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "payment-service"}

@app.get("/metrics")
async def metrics():
    error_rate = (error_count / request_count * 100) if request_count > 0 else 0
    return {
        "total_requests": request_count,
        "error_count": error_count,
        "error_rate": round(error_rate, 2)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003, log_config=None)
