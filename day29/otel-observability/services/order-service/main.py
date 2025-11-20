import os
import json
import logging
import structlog
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.trace import Status, StatusCode

# Configuration
SERVICE_NAME = "order-service"
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
INVENTORY_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8001")
PAYMENT_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8002")

# Setup OpenTelemetry Resource
resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: SERVICE_NAME,
    ResourceAttributes.SERVICE_VERSION: "1.0.0",
    ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "development"
})

# Setup Tracing
trace_provider = TracerProvider(resource=resource)
trace_exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

# Setup Metrics
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True),
    export_interval_millis=5000
)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

# Custom Metrics
orders_created = meter.create_counter(
    "orders.created.total",
    description="Total number of orders created",
    unit="1"
)

orders_failed = meter.create_counter(
    "orders.failed.total",
    description="Total number of failed orders",
    unit="1"
)

order_value = meter.create_histogram(
    "orders.value",
    description="Distribution of order values",
    unit="USD"
)

order_processing_duration = meter.create_histogram(
    "orders.processing.duration",
    description="Order processing duration",
    unit="ms"
)

active_orders = meter.create_up_down_counter(
    "orders.active",
    description="Currently processing orders",
    unit="1"
)

# Setup Structured Logging
def add_trace_context(logger, method_name, event_dict):
    span = trace.get_current_span()
    if span:
        ctx = span.get_span_context()
        if ctx.is_valid:
            event_dict["trace_id"] = format(ctx.trace_id, '032x')
            event_dict["span_id"] = format(ctx.span_id, '016x')
    return event_dict

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_trace_context,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(SERVICE_NAME)
LoggingInstrumentor().instrument(set_logging_format=True)

# HTTP Client with instrumentation
HTTPXClientInstrumentor().instrument()

# Models
class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class OrderRequest(BaseModel):
    customer_id: str
    items: list[OrderItem]
    payment_method: str = "credit_card"

class Order(BaseModel):
    order_id: str
    customer_id: str
    items: list[OrderItem]
    total: float
    status: str
    created_at: str

# Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("order_service_starting", service=SERVICE_NAME)
    yield
    logger.info("order_service_stopping", service=SERVICE_NAME)
    trace_provider.shutdown()
    meter_provider.shutdown()

app = FastAPI(
    title="Order Service",
    description="Order processing with OpenTelemetry",
    version="1.0.0",
    lifespan=lifespan
)

FastAPIInstrumentor.instrument_app(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
orders_db: dict[str, Order] = {}
order_counter = 0

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": SERVICE_NAME}

@app.post("/orders", response_model=Order)
async def create_order(request: OrderRequest):
    global order_counter
    
    start_time = datetime.now()
    active_orders.add(1)
    
    with tracer.start_as_current_span("create_order") as span:
        span.set_attribute("customer.id", request.customer_id)
        span.set_attribute("items.count", len(request.items))
        
        order_counter += 1
        order_id = f"ORD-{order_counter:06d}"
        span.set_attribute("order.id", order_id)
        
        total = sum(item.price * item.quantity for item in request.items)
        span.set_attribute("order.total", total)
        
        logger.info(
            "order_created",
            order_id=order_id,
            customer_id=request.customer_id,
            total=total,
            items_count=len(request.items)
        )
        
        # Check inventory
        with tracer.start_as_current_span("check_inventory") as inv_span:
            try:
                async with httpx.AsyncClient() as client:
                    for item in request.items:
                        inv_span.add_event(
                            "checking_item",
                            {"product_id": item.product_id, "quantity": item.quantity}
                        )
                        
                        response = await client.post(
                            f"{INVENTORY_URL}/inventory/check",
                            json={"product_id": item.product_id, "quantity": item.quantity},
                            timeout=5.0
                        )
                        
                        if response.status_code != 200:
                            inv_span.set_status(Status(StatusCode.ERROR, "Inventory check failed"))
                            logger.warning(
                                "inventory_check_failed",
                                order_id=order_id,
                                product_id=item.product_id
                            )
                            orders_failed.add(1, {"reason": "inventory"})
                            raise HTTPException(status_code=400, detail=f"Product {item.product_id} not available")
                        
                        inv_span.add_event("item_available", {"product_id": item.product_id})
                        
            except httpx.RequestError as e:
                inv_span.set_status(Status(StatusCode.ERROR, str(e)))
                logger.error("inventory_service_error", order_id=order_id, error=str(e))
                orders_failed.add(1, {"reason": "inventory_service_down"})
                raise HTTPException(status_code=503, detail="Inventory service unavailable")
        
        # Process payment
        with tracer.start_as_current_span("process_payment") as pay_span:
            pay_span.set_attribute("payment.method", request.payment_method)
            pay_span.set_attribute("payment.amount", total)
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{PAYMENT_URL}/payments/process",
                        json={
                            "order_id": order_id,
                            "amount": total,
                            "method": request.payment_method,
                            "customer_id": request.customer_id
                        },
                        timeout=10.0
                    )
                    
                    if response.status_code != 200:
                        pay_span.set_status(Status(StatusCode.ERROR, "Payment failed"))
                        logger.error(
                            "payment_failed",
                            order_id=order_id,
                            amount=total,
                            method=request.payment_method
                        )
                        orders_failed.add(1, {"reason": "payment"})
                        raise HTTPException(status_code=400, detail="Payment processing failed")
                    
                    payment_result = response.json()
                    pay_span.set_attribute("payment.transaction_id", payment_result.get("transaction_id", ""))
                    pay_span.add_event("payment_successful", {"transaction_id": payment_result.get("transaction_id", "")})
                    
            except httpx.RequestError as e:
                pay_span.set_status(Status(StatusCode.ERROR, str(e)))
                logger.error("payment_service_error", order_id=order_id, error=str(e))
                orders_failed.add(1, {"reason": "payment_service_down"})
                raise HTTPException(status_code=503, detail="Payment service unavailable")
        
        # Create order
        order = Order(
            order_id=order_id,
            customer_id=request.customer_id,
            items=request.items,
            total=total,
            status="completed",
            created_at=datetime.utcnow().isoformat()
        )
        
        orders_db[order_id] = order
        
        # Record metrics
        duration = (datetime.now() - start_time).total_seconds() * 1000
        orders_created.add(1, {"payment_method": request.payment_method})
        order_value.record(total, {"customer_tier": "standard"})
        order_processing_duration.record(duration, {"status": "success"})
        
        active_orders.add(-1)
        
        span.set_status(Status(StatusCode.OK))
        logger.info(
            "order_completed",
            order_id=order_id,
            duration_ms=duration,
            total=total
        )
        
        return order

@app.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str):
    with tracer.start_as_current_span("get_order") as span:
        span.set_attribute("order.id", order_id)
        
        if order_id not in orders_db:
            span.set_status(Status(StatusCode.ERROR, "Order not found"))
            logger.warning("order_not_found", order_id=order_id)
            raise HTTPException(status_code=404, detail="Order not found")
        
        logger.info("order_retrieved", order_id=order_id)
        return orders_db[order_id]

@app.get("/orders")
async def list_orders():
    with tracer.start_as_current_span("list_orders") as span:
        span.set_attribute("orders.count", len(orders_db))
        logger.info("orders_listed", count=len(orders_db))
        return list(orders_db.values())

@app.get("/metrics/custom")
async def get_custom_metrics():
    """Endpoint for dashboard to get current metric values"""
    return {
        "orders_total": order_counter,
        "service": SERVICE_NAME
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
