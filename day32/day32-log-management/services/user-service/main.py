from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_config import setup_logger
import random
import time
from datetime import datetime

app = FastAPI(title="User Service")
logger = setup_logger("user-service")

class LoginRequest(BaseModel):
    username: str
    password: str

class User(BaseModel):
    user_id: int
    username: str
    email: str

# Simulate user database
users_db = {
    "alice": {"user_id": 1001, "password": "pass123", "email": "alice@example.com"},
    "bob": {"user_id": 1002, "password": "pass456", "email": "bob@example.com"},
    "charlie": {"user_id": 1003, "password": "pass789", "email": "charlie@example.com"}
}

request_count = 0
error_count = 0

@app.post("/api/login")
async def login(request: LoginRequest):
    global request_count, error_count
    request_count += 1
    
    start_time = time.time()
    
    # Simulate various scenarios for realistic logging
    scenario = random.random()
    
    try:
        if scenario < 0.05:  # 5% - simulate database timeout
            logger.error("Database connection timeout", extra={
                "event": "db_timeout",
                "username": request.username,
                "duration_ms": 5000,
                "request_id": f"req-{request_count}"
            })
            error_count += 1
            raise HTTPException(status_code=503, detail="Service temporarily unavailable")
        
        if scenario < 0.10:  # 5% - invalid credentials
            logger.warning("Authentication failed - invalid credentials", extra={
                "event": "auth_failed",
                "username": request.username,
                "reason": "invalid_password",
                "request_id": f"req-{request_count}"
            })
            error_count += 1
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if request.username not in users_db:
            logger.warning("Authentication failed - user not found", extra={
                "event": "auth_failed",
                "username": request.username,
                "reason": "user_not_found",
                "request_id": f"req-{request_count}"
            })
            error_count += 1
            raise HTTPException(status_code=404, detail="User not found")
        
        user = users_db[request.username]
        if user["password"] != request.password:
            logger.warning("Authentication failed - wrong password", extra={
                "event": "auth_failed",
                "username": request.username,
                "reason": "invalid_password",
                "request_id": f"req-{request_count}"
            })
            error_count += 1
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        duration_ms = (time.time() - start_time) * 1000
        logger.info("User authenticated successfully", extra={
            "event": "auth_success",
            "user_id": user["user_id"],
            "username": request.username,
            "duration_ms": round(duration_ms, 2),
            "request_id": f"req-{request_count}"
        })
        
        return {
            "user_id": user["user_id"],
            "username": request.username,
            "email": user["email"],
            "token": f"token-{user['user_id']}-{int(time.time())}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error("Unexpected error during authentication", extra={
            "event": "auth_error",
            "error": str(e),
            "username": request.username,
            "duration_ms": round(duration_ms, 2),
            "request_id": f"req-{request_count}"
        })
        error_count += 1
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    logger.debug("Fetching user details", extra={
        "event": "user_fetch",
        "user_id": user_id
    })
    
    for username, data in users_db.items():
        if data["user_id"] == user_id:
            logger.info("User details retrieved", extra={
                "event": "user_retrieved",
                "user_id": user_id
            })
            return User(user_id=data["user_id"], username=username, email=data["email"])
    
    logger.warning("User not found", extra={
        "event": "user_not_found",
        "user_id": user_id
    })
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "user-service"}

@app.get("/metrics")
async def metrics():
    error_rate = (error_count / request_count * 100) if request_count > 0 else 0
    return {
        "total_requests": request_count,
        "error_count": error_count,
        "error_rate": round(error_rate, 2)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_config=None)
