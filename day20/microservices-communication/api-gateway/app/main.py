from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
from typing import Optional
import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.utils.circuit_breaker import CircuitBreakerService
from shared.utils.service_discovery import ServiceDiscovery
from shared.utils.health_check import HealthChecker

app = FastAPI(title="API Gateway", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
service_discovery = ServiceDiscovery()
health_checker = HealthChecker("api-gateway")
circuit_breakers = {}

# Initialize circuit breakers for each service
services = ["user-service", "order-service", "notification-service"]
for service in services:
    circuit_breakers[service] = CircuitBreakerService(
        failure_threshold=3,
        recovery_timeout=30
    )

@app.on_event("startup")
async def startup_event():
    # Register services
    service_discovery.register_service("user-service", "localhost", 8001)
    service_discovery.register_service("order-service", "localhost", 8002)
    service_discovery.register_service("notification-service", "localhost", 8003)
    logging.info("API Gateway started and services registered")

@app.get("/health")
async def health_check():
    return health_checker.get_health_status()

@app.get("/")
async def root():
    return {"message": "API Gateway is running", "services": list(circuit_breakers.keys())}

async def make_service_request(service_name: str, endpoint: str, method: str = "GET", data: dict = None):
    service_url = await service_discovery.discover_service(service_name)
    if not service_url:
        raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")
    
    circuit_breaker = circuit_breakers.get(service_name)
    if not circuit_breaker:
        raise HTTPException(status_code=500, detail=f"No circuit breaker for {service_name}")
    
    async def service_call():
        async with httpx.AsyncClient() as client:
            url = f"{service_url}{endpoint}"
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=data)
            elif method == "PUT":
                response = await client.put(url, json=data)
            elif method == "DELETE":
                response = await client.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code >= 400:
                raise httpx.HTTPStatusError(f"Service error: {response.status_code}", request=response.request, response=response)
            
            return response.json()
    
    try:
        return await circuit_breaker.call(service_call)
    except Exception as e:
        logging.error(f"Request to {service_name}{endpoint} failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service {service_name} temporarily unavailable")

# User service endpoints
@app.get("/api/users/")
async def get_users():
    return await make_service_request("user-service", "/users/")

@app.post("/api/users/")
async def create_user(request: Request):
    user_data = await request.json()
    return await make_service_request("user-service", "/users/", "POST", user_data)

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    return await make_service_request("user-service", f"/users/{user_id}")

# Order service endpoints
@app.get("/api/orders/")
async def get_orders():
    return await make_service_request("order-service", "/orders/")

@app.post("/api/orders/")
async def create_order(request: Request):
    order_data = await request.json()
    return await make_service_request("order-service", "/orders/", "POST", order_data)

@app.get("/api/orders/{order_id}")
async def get_order(order_id: int):
    return await make_service_request("order-service", f"/orders/{order_id}")

# Notification service endpoints
@app.get("/api/notifications/")
async def get_notifications():
    return await make_service_request("notification-service", "/notifications/")

# Circuit breaker status endpoints
@app.get("/api/circuit-breakers/")
async def get_circuit_breaker_status():
    status = {}
    for service_name, cb in circuit_breakers.items():
        status[service_name] = cb.get_state()
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
