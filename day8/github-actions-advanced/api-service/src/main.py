from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import redis
import json
import os
from typing import List, Optional

app = FastAPI(title="API Service", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
try:
    redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, decode_responses=True)
except:
    redis_client = None

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    cache_status: str

class APIResponse(BaseModel):
    message: str
    data: Optional[dict] = None
    cached: bool = False

@app.get("/", response_model=HealthResponse)
async def root():
    cache_status = "disconnected"
    if redis_client:
        try:
            redis_client.ping()
            cache_status = "connected"
        except:
            cache_status = "disconnected"
    
    return HealthResponse(
        status="healthy",
        version="1.0.0", 
        environment=os.getenv('ENVIRONMENT', 'development'),
        cache_status=cache_status
    )

@app.get("/api/data", response_model=APIResponse)
async def get_data():
    cache_key = "api:data"
    
    # Try cache first
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return APIResponse(
                    message="Data retrieved from cache",
                    data=json.loads(cached_data),
                    cached=True
                )
        except:
            pass
    
    # Simulate API processing
    data = {
        "timestamp": "2024-01-01T00:00:00Z",
        "items": [
            {"id": 1, "name": "Item 1", "status": "active"},
            {"id": 2, "name": "Item 2", "status": "pending"},
            {"id": 3, "name": "Item 3", "status": "active"}
        ],
        "total": 3
    }
    
    # Cache the data
    if redis_client:
        try:
            redis_client.setex(cache_key, 300, json.dumps(data))
        except:
            pass
    
    return APIResponse(
        message="Data retrieved successfully",
        data=data,
        cached=False
    )

@app.get("/api/users")
async def get_users():
    """Proxy to user service with caching"""
    cache_key = "api:users"
    
    if redis_client:
        try:
            cached_users = redis_client.get(cache_key)
            if cached_users:
                return {
                    "users": json.loads(cached_users),
                    "cached": True
                }
        except:
            pass
    
    # Call user service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://user-service:8001/users")
            users_data = response.json()
            
            if redis_client:
                try:
                    redis_client.setex(cache_key, 120, json.dumps(users_data))
                except:
                    pass
            
            return {
                "users": users_data,
                "cached": False
            }
    except:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
