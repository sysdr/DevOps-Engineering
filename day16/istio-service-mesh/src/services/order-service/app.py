from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import httpx
import random
from typing import List
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import PlainTextResponse
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource

# OpenTelemetry setup
resource = Resource(attributes={"service.name": "order-service"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv("JAEGER_AGENT_HOST", "jaeger-agent"),
    agent_port=int(os.getenv("JAEGER_AGENT_PORT", 6831)),
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

app = FastAPI(title="Order Service", version="1.0.0")
FastAPIInstrumentor.instrument_app(app)

# Metrics
REQUEST_COUNT = Counter('order_requests_total', 'Total order requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('order_request_duration_seconds', 'Order request duration')

class OrderItem(BaseModel):
    product_id: int
    quantity: int

class Order(BaseModel):
    id: int
    user_id: int
    items: List[OrderItem]
    total: float
    status: str
    created_at: datetime

class CreateOrderRequest(BaseModel):
    user_id: int
    items: List[OrderItem]

orders_db = {}
order_id_counter = 1

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "order-service"}

@app.post("/orders")
async def create_order(order_request: CreateOrderRequest):
    global order_id_counter
    REQUEST_COUNT.labels(method="POST", endpoint="/orders").inc()
    
    total = 0.0
    
    # Validate products and calculate total
    with tracer.start_as_current_span("validate_products"):
        async with httpx.AsyncClient() as client:
            for item in order_request.items:
                try:
                    response = await client.get(f"http://product-service:8080/products/{item.product_id}")
                    if response.status_code == 200:
                        product = response.json()
                        total += product["price"] * item.quantity
                    else:
                        raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Error validating product {item.product_id}")
    
    # Create order
    order = Order(
        id=order_id_counter,
        user_id=order_request.user_id,
        items=order_request.items,
        total=total,
        status="confirmed",
        created_at=datetime.now()
    )
    
    orders_db[order_id_counter] = order
    order_id_counter += 1
    
    return order

@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    REQUEST_COUNT.labels(method="GET", endpoint="/orders").inc()
    
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return orders_db[order_id]

@app.get("/orders")
async def list_orders(user_id: int = None):
    REQUEST_COUNT.labels(method="GET", endpoint="/orders").inc()
    
    orders = list(orders_db.values())
    if user_id:
        orders = [o for o in orders if o.user_id == user_id]
    
    return orders

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
