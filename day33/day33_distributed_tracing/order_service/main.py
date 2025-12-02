from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx
import asyncio
import random
import logging
from datetime import datetime
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize tracing
resource = Resource.create({"service.name": "order-service"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

app = FastAPI(title="Order Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()

class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class Order(BaseModel):
    customer_id: str
    items: list[OrderItem]

class OrderResponse(BaseModel):
    order_id: str
    status: str
    total_amount: float
    trace_id: str

INVENTORY_URL = "http://localhost:8002"
PAYMENT_URL = "http://localhost:8003"

@app.get("/")
async def root():
    return {
        "service": "order-service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "create_order": "POST /orders",
            "get_order": "GET /orders/{order_id}",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "order"}

@app.post("/orders", response_model=OrderResponse)
async def create_order(order: Order):
    span = trace.get_current_span()
    trace_id = format(span.get_span_context().trace_id, '032x')
    
    span.set_attribute("order.customer_id", order.customer_id)
    span.set_attribute("order.items_count", len(order.items))
    
    logger.info(f"Creating order for customer {order.customer_id}, trace_id: {trace_id}")
    
    order_id = f"ORD-{random.randint(10000, 99999)}"
    
    # Step 1: Validate cart
    with tracer.start_as_current_span("validate_cart") as validate_span:
        validate_span.set_attribute("validation.type", "cart")
        await asyncio.sleep(0.015)  # Simulate validation
        total_amount = sum(item.price * item.quantity for item in order.items)
        validate_span.set_attribute("order.total_amount", total_amount)
    
    # Step 2: Check inventory
    with tracer.start_as_current_span("check_inventory") as inv_span:
        inv_span.set_attribute("http.url", f"{INVENTORY_URL}/inventory/check")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{INVENTORY_URL}/inventory/check",
                    json={"items": [{"product_id": item.product_id, "quantity": item.quantity} for item in order.items]},
                    timeout=5.0
                )
                if response.status_code != 200:
                    inv_span.set_status(Status(StatusCode.ERROR))
                    raise HTTPException(status_code=400, detail="Insufficient inventory")
                
                inv_result = response.json()
                inv_span.set_attribute("inventory.available", inv_result["available"])
        except httpx.RequestError as e:
            inv_span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=503, detail="Inventory service unavailable")
    
    # Step 3: Process payment
    with tracer.start_as_current_span("process_payment") as pay_span:
        pay_span.set_attribute("http.url", f"{PAYMENT_URL}/payments/process")
        pay_span.set_attribute("payment.amount", total_amount)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{PAYMENT_URL}/payments/process",
                    json={"order_id": order_id, "amount": total_amount, "customer_id": order.customer_id},
                    timeout=5.0
                )
                if response.status_code != 200:
                    pay_span.set_status(Status(StatusCode.ERROR))
                    raise HTTPException(status_code=400, detail="Payment failed")
                
                pay_result = response.json()
                pay_span.set_attribute("payment.transaction_id", pay_result["transaction_id"])
        except httpx.RequestError as e:
            pay_span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=503, detail="Payment service unavailable")
    
    logger.info(f"Order {order_id} created successfully, trace_id: {trace_id}")
    
    return OrderResponse(
        order_id=order_id,
        status="completed",
        total_amount=total_amount,
        trace_id=trace_id
    )

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    span = trace.get_current_span()
    span.set_attribute("order.id", order_id)
    
    # Simulate database lookup
    with tracer.start_as_current_span("database_lookup") as db_span:
        db_span.set_attribute("db.system", "postgresql")
        db_span.set_attribute("db.operation", "SELECT")
        await asyncio.sleep(0.020)
    
    return {
        "order_id": order_id,
        "status": "completed",
        "items": 3,
        "total": 299.99
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
