import os
import random
import structlog
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
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
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.trace import Status, StatusCode

# Configuration
SERVICE_NAME = "inventory-service"
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

# Setup OpenTelemetry
resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: SERVICE_NAME,
    ResourceAttributes.SERVICE_VERSION: "1.0.0",
    ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "development"
})

# Tracing
trace_provider = TracerProvider(resource=resource)
trace_exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

# Metrics
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True),
    export_interval_millis=5000
)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

# Custom Metrics
inventory_checks = meter.create_counter(
    "inventory.checks.total",
    description="Total inventory checks",
    unit="1"
)

inventory_available = meter.create_counter(
    "inventory.available.total",
    description="Successful availability checks",
    unit="1"
)

inventory_unavailable = meter.create_counter(
    "inventory.unavailable.total",
    description="Failed availability checks",
    unit="1"
)

stock_level = meter.create_histogram(
    "inventory.stock.level",
    description="Stock levels when checked",
    unit="items"
)

# Structured Logging
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

# Models
class InventoryCheck(BaseModel):
    product_id: str
    quantity: int

class InventoryResponse(BaseModel):
    product_id: str
    available: bool
    stock: int
    requested: int

# Simulated inventory
inventory_stock = {
    "PROD-001": 100,
    "PROD-002": 50,
    "PROD-003": 25,
    "PROD-004": 200,
    "PROD-005": 0,
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("inventory_service_starting", service=SERVICE_NAME)
    yield
    logger.info("inventory_service_stopping", service=SERVICE_NAME)
    trace_provider.shutdown()
    meter_provider.shutdown()

app = FastAPI(
    title="Inventory Service",
    description="Inventory management with OpenTelemetry",
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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": SERVICE_NAME}

@app.post("/inventory/check", response_model=InventoryResponse)
async def check_inventory(request: InventoryCheck):
    with tracer.start_as_current_span("check_inventory") as span:
        span.set_attribute("product.id", request.product_id)
        span.set_attribute("quantity.requested", request.quantity)
        
        # Simulate processing time
        import asyncio
        await asyncio.sleep(random.uniform(0.01, 0.05))
        
        inventory_checks.add(1, {"product_id": request.product_id})
        
        # Check if product exists
        if request.product_id not in inventory_stock:
            # Add product with random stock for demo
            inventory_stock[request.product_id] = random.randint(10, 100)
        
        current_stock = inventory_stock[request.product_id]
        span.set_attribute("stock.current", current_stock)
        
        stock_level.record(current_stock, {"product_id": request.product_id})
        
        available = current_stock >= request.quantity
        
        if available:
            # Reserve stock
            inventory_stock[request.product_id] -= request.quantity
            inventory_available.add(1, {"product_id": request.product_id})
            span.add_event("stock_reserved", {
                "product_id": request.product_id,
                "quantity": request.quantity,
                "remaining": inventory_stock[request.product_id]
            })
            logger.info(
                "inventory_reserved",
                product_id=request.product_id,
                quantity=request.quantity,
                remaining=inventory_stock[request.product_id]
            )
        else:
            inventory_unavailable.add(1, {"product_id": request.product_id})
            span.set_status(Status(StatusCode.ERROR, "Insufficient stock"))
            span.add_event("insufficient_stock", {
                "product_id": request.product_id,
                "requested": request.quantity,
                "available": current_stock
            })
            logger.warning(
                "inventory_insufficient",
                product_id=request.product_id,
                requested=request.quantity,
                available=current_stock
            )
        
        return InventoryResponse(
            product_id=request.product_id,
            available=available,
            stock=current_stock,
            requested=request.quantity
        )

@app.get("/inventory")
async def get_inventory():
    with tracer.start_as_current_span("get_inventory") as span:
        span.set_attribute("products.count", len(inventory_stock))
        logger.info("inventory_listed", count=len(inventory_stock))
        return inventory_stock

@app.post("/inventory/restock")
async def restock(product_id: str, quantity: int):
    with tracer.start_as_current_span("restock_inventory") as span:
        span.set_attribute("product.id", product_id)
        span.set_attribute("quantity.added", quantity)
        
        if product_id not in inventory_stock:
            inventory_stock[product_id] = 0
        
        inventory_stock[product_id] += quantity
        
        logger.info(
            "inventory_restocked",
            product_id=product_id,
            added=quantity,
            total=inventory_stock[product_id]
        )
        
        return {"product_id": product_id, "new_stock": inventory_stock[product_id]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
