from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import httpx
from datetime import datetime
import json

app = FastAPI(title="Zero-Trust Resource Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_SERVICE_URL = "http://localhost:8001"
POLICY_SERVICE_URL = "http://localhost:8003"

# Simulated data store
data_store = {
    "dev": [
        {"id": 1, "name": "Development Data 1", "value": 100},
        {"id": 2, "name": "Development Data 2", "value": 200}
    ],
    "prod": [
        {"id": 101, "name": "Production Data 1", "value": 1000},
        {"id": 102, "name": "Production Data 2", "value": 2000}
    ]
}

access_logs = []

class DataItem(BaseModel):
    name: str
    value: int

async def verify_and_authorize(
    authorization: str = Header(None),
    namespace: str = "default",
    resource: str = "",
    action: str = "GET"
) -> Dict:
    """Verify token and check authorization"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    # Step 1: Validate token with Auth Service
    async with httpx.AsyncClient() as client:
        try:
            auth_response = await client.post(
                f"{AUTH_SERVICE_URL}/auth/validate",
                headers={"Authorization": authorization},
                timeout=5.0
            )
            
            if auth_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Token validation failed")
            
            validation = auth_response.json()
            
            if not validation.get("valid"):
                raise HTTPException(status_code=401, detail=validation.get("error", "Invalid token"))
            
            claims = validation.get("claims", {})
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")
    
    # Step 2: Check authorization with Policy Service
    async with httpx.AsyncClient() as client:
        try:
            policy_response = await client.post(
                f"{POLICY_SERVICE_URL}/policy/evaluate",
                json={
                    "user": claims,
                    "resource": resource,
                    "action": action,
                    "namespace": namespace
                },
                timeout=5.0
            )
            
            if policy_response.status_code != 200:
                raise HTTPException(status_code=503, detail="Policy service unavailable")
            
            policy_result = policy_response.json()
            
            if not policy_result.get("allowed"):
                # Log unauthorized access attempt
                access_logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "user": claims.get("sub"),
                    "resource": resource,
                    "action": action,
                    "namespace": namespace,
                    "allowed": False,
                    "reason": policy_result.get("reason")
                })
                
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied: {policy_result.get('reason')}"
                )
            
            # Log successful access
            access_logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "user": claims.get("sub"),
                "resource": resource,
                "action": action,
                "namespace": namespace,
                "allowed": True,
                "matched_rules": policy_result.get("matched_rules", [])
            })
            
            return claims
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Policy service unavailable: {str(e)}")

@app.get("/api/data/{namespace}")
async def get_data(
    namespace: str,
    authorization: str = Header(None)
):
    """Get data from namespace (requires authentication and authorization)"""
    
    # Verify token and check authorization
    claims = await verify_and_authorize(
        authorization=authorization,
        namespace=namespace,
        resource=f"api/data/{namespace}",
        action="GET"
    )
    
    if namespace not in data_store:
        raise HTTPException(status_code=404, detail=f"Namespace '{namespace}' not found")
    
    return {
        "namespace": namespace,
        "data": data_store[namespace],
        "accessed_by": claims.get("sub"),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/data/{namespace}")
async def create_data(
    namespace: str,
    item: DataItem,
    authorization: str = Header(None)
):
    """Create data in namespace (requires authentication and authorization)"""
    
    # Verify token and check authorization
    claims = await verify_and_authorize(
        authorization=authorization,
        namespace=namespace,
        resource=f"api/data/{namespace}",
        action="POST"
    )
    
    if namespace not in data_store:
        data_store[namespace] = []
    
    new_id = max([d["id"] for d in data_store[namespace]], default=0) + 1
    new_item = {
        "id": new_id,
        "name": item.name,
        "value": item.value
    }
    
    data_store[namespace].append(new_item)
    
    return {
        "message": "Data created successfully",
        "namespace": namespace,
        "item": new_item,
        "created_by": claims.get("sub"),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.delete("/api/data/{namespace}/{item_id}")
async def delete_data(
    namespace: str,
    item_id: int,
    authorization: str = Header(None)
):
    """Delete data from namespace (requires authentication and authorization)"""
    
    # Verify token and check authorization
    claims = await verify_and_authorize(
        authorization=authorization,
        namespace=namespace,
        resource=f"api/data/{namespace}",
        action="DELETE"
    )
    
    if namespace not in data_store:
        raise HTTPException(status_code=404, detail=f"Namespace '{namespace}' not found")
    
    data_store[namespace] = [d for d in data_store[namespace] if d["id"] != item_id]
    
    return {
        "message": "Data deleted successfully",
        "namespace": namespace,
        "item_id": item_id,
        "deleted_by": claims.get("sub"),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/access-logs")
async def get_access_logs(limit: int = 50):
    """Get recent access logs"""
    return {"logs": access_logs[-limit:]}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "resource"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
