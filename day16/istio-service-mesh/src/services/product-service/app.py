from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import random
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import PlainTextResponse
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource

# OpenTelemetry setup
resource = Resource(attributes={"service.name": "product-service"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv("JAEGER_AGENT_HOST", "jaeger-agent"),
    agent_port=int(os.getenv("JAEGER_AGENT_PORT", 6831)),
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

app = FastAPI(title="Product Service", version="1.0.0")
FastAPIInstrumentor.instrument_app(app)

# Metrics
REQUEST_COUNT = Counter('product_requests_total', 'Total product requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('product_request_duration_seconds', 'Product request duration')

class Product(BaseModel):
    id: int
    name: str
    price: float
    category: str
    stock: int

products_db = {
    1: Product(id=1, name="Laptop Pro", price=1299.99, category="electronics", stock=50),
    2: Product(id=2, name="Wireless Headphones", price=199.99, category="electronics", stock=100),
    3: Product(id=3, name="Coffee Maker", price=89.99, category="home", stock=25),
    4: Product(id=4, name="Running Shoes", price=129.99, category="sports", stock=75),
}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "product-service"}

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    REQUEST_COUNT.labels(method="GET", endpoint="/products").inc()
    
    # Simulate occasional failures for circuit breaker testing
    if random.random() < 0.1:  # 10% failure rate
        raise HTTPException(status_code=500, detail="Internal server error")
    
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return products_db[product_id]

@app.get("/products")
async def list_products(category: str = None):
    REQUEST_COUNT.labels(method="GET", endpoint="/products").inc()
    
    products = list(products_db.values())
    if category:
        products = [p for p in products if p.category == category]
    
    return products

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
