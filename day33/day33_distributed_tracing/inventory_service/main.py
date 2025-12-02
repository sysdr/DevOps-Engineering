from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import random
import logging
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize tracing
resource = Resource.create({"service.name": "inventory-service"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

app = FastAPI(title="Inventory Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app)

class InventoryItem(BaseModel):
    product_id: str
    quantity: int

class InventoryCheckRequest(BaseModel):
    items: list[InventoryItem]

# Simulated inventory database
INVENTORY_DB = {
    "PROD-001": 100,
    "PROD-002": 50,
    "PROD-003": 200,
    "PROD-004": 5,  # Low stock item
    "PROD-005": 0,  # Out of stock
}

@app.get("/")
async def root():
    return {
        "service": "inventory-service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "check_inventory": "POST /inventory/check",
            "get_stock": "GET /inventory/{product_id}",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "inventory"}

@app.post("/inventory/check")
async def check_inventory(request: InventoryCheckRequest):
    span = trace.get_current_span()
    span.set_attribute("inventory.items_count", len(request.items))
    
    trace_id = format(span.get_span_context().trace_id, '032x')
    logger.info(f"Checking inventory for {len(request.items)} items, trace_id: {trace_id}")
    
    # Simulate database query
    with tracer.start_as_current_span("database_query") as db_span:
        db_span.set_attribute("db.system", "postgresql")
        db_span.set_attribute("db.operation", "SELECT")
        
        # Simulate variable query time (some items are slower to check)
        slow_check = any(item.product_id == "PROD-004" for item in request.items)
        if slow_check:
            db_span.set_attribute("query.slow", True)
            await asyncio.sleep(0.080)  # Slow query simulation
        else:
            await asyncio.sleep(0.025)
    
    # Check each item
    all_available = True
    for item in request.items:
        with tracer.start_as_current_span("check_item") as item_span:
            item_span.set_attribute("product.id", item.product_id)
            item_span.set_attribute("product.requested_quantity", item.quantity)
            
            available_stock = INVENTORY_DB.get(item.product_id, 0)
            item_span.set_attribute("product.available_stock", available_stock)
            
            if available_stock < item.quantity:
                all_available = False
                item_span.set_attribute("stock.sufficient", False)
                item_span.set_status(Status(StatusCode.ERROR, "Insufficient stock"))
            else:
                item_span.set_attribute("stock.sufficient", True)
    
    if not all_available:
        span.set_status(Status(StatusCode.ERROR, "Insufficient inventory"))
        raise HTTPException(status_code=400, detail="Insufficient inventory")
    
    # Reserve items
    with tracer.start_as_current_span("reserve_items") as reserve_span:
        reserve_span.set_attribute("reservation.count", len(request.items))
        await asyncio.sleep(0.025)
        logger.info(f"Reserved {len(request.items)} items, trace_id: {trace_id}")
    
    return {"available": True, "reserved": len(request.items)}

@app.get("/inventory/{product_id}")
async def get_stock(product_id: str):
    span = trace.get_current_span()
    span.set_attribute("product.id", product_id)
    
    stock = INVENTORY_DB.get(product_id, 0)
    span.set_attribute("product.stock", stock)
    
    return {"product_id": product_id, "stock": stock}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
