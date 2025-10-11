from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import httpx
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import PlainTextResponse
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource

# OpenTelemetry setup
resource = Resource(attributes={"service.name": "user-service"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv("JAEGER_AGENT_HOST", "jaeger-agent"),
    agent_port=int(os.getenv("JAEGER_AGENT_PORT", 6831)),
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

app = FastAPI(title="User Service", version="1.0.0")
FastAPIInstrumentor.instrument_app(app)

# Metrics
REQUEST_COUNT = Counter('user_requests_total', 'Total user requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('user_request_duration_seconds', 'User request duration')

class User(BaseModel):
    id: int
    name: str
    email: str
    tier: str = "standard"  # standard, premium

users_db = {
    1: User(id=1, name="John Doe", email="john@example.com", tier="premium"),
    2: User(id=2, name="Jane Smith", email="jane@example.com", tier="standard"),
    3: User(id=3, name="Bob Wilson", email="bob@example.com", tier="premium"),
}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "user-service"}

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    REQUEST_COUNT.labels(method="GET", endpoint="/users").inc()
    
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Simulate getting recommendations
    with tracer.start_as_current_span("get_recommendations"):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://recommendation-service:8080/recommendations/{user_id}")
                recommendations = response.json() if response.status_code == 200 else []
        except Exception:
            recommendations = []
    
    user = users_db[user_id]
    return {
        **user.dict(),
        "recommendations": recommendations
    }

@app.get("/users")
async def list_users():
    REQUEST_COUNT.labels(method="GET", endpoint="/users").inc()
    return list(users_db.values())

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
