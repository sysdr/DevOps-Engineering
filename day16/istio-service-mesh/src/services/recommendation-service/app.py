from fastapi import FastAPI
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
service_version = os.getenv("SERVICE_VERSION", "v1")
resource = Resource(attributes={
    "service.name": "recommendation-service",
    "service.version": service_version
})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv("JAEGER_AGENT_HOST", "jaeger-agent"),
    agent_port=int(os.getenv("JAEGER_AGENT_PORT", 6831)),
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

app = FastAPI(title=f"Recommendation Service {service_version}", version=service_version)
FastAPIInstrumentor.instrument_app(app)

# Metrics
REQUEST_COUNT = Counter('recommendation_requests_total', 'Total recommendation requests', ['method', 'endpoint', 'version'])
REQUEST_DURATION = Histogram('recommendation_request_duration_seconds', 'Recommendation request duration')

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "recommendation-service", "version": service_version}

@app.get("/recommendations/{user_id}")
async def get_recommendations(user_id: int):
    REQUEST_COUNT.labels(method="GET", endpoint="/recommendations", version=service_version).inc()
    
    if service_version == "v1":
        # Basic recommendations
        recommendations = [
            {"product_id": 1, "score": 0.8, "reason": "Popular in electronics"},
            {"product_id": 2, "score": 0.7, "reason": "Frequently bought together"},
        ]
    else:  # v2
        # Enhanced ML-based recommendations
        recommendations = [
            {"product_id": 1, "score": 0.95, "reason": "AI-powered match for your preferences"},
            {"product_id": 2, "score": 0.88, "reason": "Similar users also purchased"},
            {"product_id": 3, "score": 0.76, "reason": "Trending in your category"},
        ]
    
    return {"user_id": user_id, "recommendations": recommendations, "version": service_version}

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
