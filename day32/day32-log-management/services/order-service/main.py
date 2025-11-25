from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_config import setup_logger
import random
import time
from typing import List

app = FastAPI(title="Order Service")
logger = setup_logger("order-service")

class OrderItem(BaseModel):
    product_id: int
    quantity: int
    price: float

class CreateOrderRequest(BaseModel):
    user_id: int
    items: List[OrderItem]

orders_db = {}
order_counter = 1000
request_count = 0
error_count = 0

@app.post("/api/orders")
async def create_order(request: CreateOrderRequest):
    global order_counter, request_count, error_count
    request_count += 1
    order_counter += 1
    
    start_time = time.time()
    
    try:
        # Simulate various scenarios
        scenario = random.random()
        
        if scenario < 0.03:  # 3% - inventory service timeout
            logger.error("Inventory service timeout", extra={
                "event": "inventory_timeout",
                "user_id": request.user_id,
                "order_id": order_counter,
                "timeout_ms": 10000
            })
            error_count += 1
            raise HTTPException(status_code=504, detail="Inventory service timeout")
        
        if scenario < 0.07:  # 4% - insufficient inventory
            logger.warning("Insufficient inventory", extra={
                "event": "insufficient_inventory",
                "user_id": request.user_id,
                "order_id": order_counter,
                "items": len(request.items)
            })
            error_count += 1
            raise HTTPException(status_code=400, detail="Insufficient inventory")
        
        total_amount = sum(item.price * item.quantity for item in request.items)
        
        order_data = {
            "order_id": order_counter,
            "user_id": request.user_id,
            "items": request.items,
            "total_amount": total_amount,
            "status": "pending",
            "created_at": time.time()
        }
        orders_db[order_counter] = order_data
        
        duration_ms = (time.time() - start_time) * 1000
        logger.info("Order created successfully", extra={
            "event": "order_created",
            "order_id": order_counter,
            "user_id": request.user_id,
            "total_amount": total_amount,
            "item_count": len(request.items),
            "duration_ms": round(duration_ms, 2)
        })
        
        return {
            "order_id": order_counter,
            "status": "pending",
            "total_amount": total_amount
        }
    
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error("Order creation failed", extra={
            "event": "order_error",
            "error": str(e),
            "user_id": request.user_id,
            "duration_ms": round(duration_ms, 2)
        })
        error_count += 1
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/orders/{order_id}")
async def get_order(order_id: int):
    if order_id in orders_db:
        logger.info("Order retrieved", extra={
            "event": "order_retrieved",
            "order_id": order_id
        })
        return orders_db[order_id]
    
    logger.warning("Order not found", extra={
        "event": "order_not_found",
        "order_id": order_id
    })
    raise HTTPException(status_code=404, detail="Order not found")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "order-service"}

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
    uvicorn.run(app, host="0.0.0.0", port=8002, log_config=None)
