from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, Histogram, generate_latest
import time
import redis
import json
from typing import Optional
import uvicorn

app = FastAPI(title="Ingress Demo Service", version="1.0.0")

# Redis for rate limiting
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Rate limiting check
    client_ip = request.client.host
    rate_limit_key = f"rate_limit:{client_ip}"
    
    try:
        current_requests = redis_client.incr(rate_limit_key)
        if current_requests == 1:
            redis_client.expire(rate_limit_key, 60)  # 1 minute window
        
        if current_requests > 100:  # 100 requests per minute per IP
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except redis.ConnectionError:
        pass  # Continue without rate limiting if Redis unavailable
    
    response = await call_next(request)
    
    # Record metrics
    process_time = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_DURATION.observe(process_time)
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/")
async def root():
    return {"message": "Ingress Demo Service", "service": "backend", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")

@app.get("/api/services")
async def get_services():
    return {
        "services": [
            {"name": "backend", "status": "healthy", "version": "1.0.0"},
            {"name": "frontend", "status": "healthy", "version": "1.0.0"},
            {"name": "redis", "status": "healthy", "version": "7.0"}
        ]
    }

@app.get("/api/load-test")
async def simulate_load():
    """Endpoint to simulate processing load"""
    import random
    processing_time = random.uniform(0.1, 1.0)
    time.sleep(processing_time)
    return {"processing_time": processing_time, "status": "completed"}

@app.get("/api/ssl-info")
async def ssl_info(request: Request):
    """Return SSL/TLS information"""
    headers = dict(request.headers)
    return {
        "ssl_terminated": "x-forwarded-proto" in headers,
        "protocol": headers.get("x-forwarded-proto", "http"),
        "host": headers.get("host", "unknown"),
        "user_agent": headers.get("user-agent", "unknown")
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
