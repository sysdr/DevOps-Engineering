from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import jwt
from jwt import PyJWTError
import httpx
from datetime import datetime, timedelta
import json
import os

app = FastAPI(title="Zero-Trust Auth Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated OIDC configuration (in production, this would be Keycloak)
SECRET_KEY = "zero-trust-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Simulated user database
USERS_DB = {
    "alice@company.com": {
        "username": "alice@company.com",
        "full_name": "Alice Developer",
        "groups": ["developers", "platform-team"],
        "roles": ["developer", "deployer"],
        "password": "alice123"  # In production, use hashed passwords
    },
    "bob@company.com": {
        "username": "bob@company.com",
        "full_name": "Bob Operator",
        "groups": ["operations", "sre-team"],
        "roles": ["operator", "admin"],
        "password": "bob123"
    },
    "eve@company.com": {
        "username": "eve@company.com",
        "full_name": "Eve Viewer",
        "groups": ["viewers"],
        "roles": ["readonly"],
        "password": "eve123"
    }
}

# Authentication events for monitoring
auth_events = []

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_info: Dict

class TokenValidation(BaseModel):
    valid: bool
    claims: Optional[Dict] = None
    error: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": "zero-trust-auth-service",
        "aud": "zero-trust-services"
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience="zero-trust-services")
        return payload
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user and issue JWT token"""
    user = USERS_DB.get(request.username)
    
    # Log authentication attempt
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "authentication_attempt",
        "username": request.username,
        "success": False
    }
    
    if not user or user["password"] != request.password:
        event["reason"] = "invalid_credentials"
        auth_events.append(event)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token with user claims
    token_data = {
        "sub": user["username"],
        "name": user["full_name"],
        "groups": user["groups"],
        "roles": user["roles"],
        "email": user["username"]
    }
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    event["success"] = True
    event["groups"] = user["groups"]
    event["roles"] = user["roles"]
    auth_events.append(event)
    
    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_info={
            "username": user["username"],
            "full_name": user["full_name"],
            "groups": user["groups"],
            "roles": user["roles"]
        }
    )

@app.post("/auth/validate", response_model=TokenValidation)
async def validate_token(authorization: str = Header(None)):
    """Validate JWT token and return claims"""
    if not authorization or not authorization.startswith("Bearer "):
        return TokenValidation(valid=False, error="Missing or invalid Authorization header")
    
    token = authorization.split(" ")[1]
    
    try:
        claims = verify_token(token)
        
        # Log successful validation
        auth_events.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "token_validation",
            "username": claims.get("sub"),
            "success": True
        })
        
        return TokenValidation(valid=True, claims=claims)
    except HTTPException as e:
        # Log failed validation
        auth_events.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "token_validation",
            "success": False,
            "reason": str(e.detail)
        })
        return TokenValidation(valid=False, error=str(e.detail))

@app.get("/auth/events")
async def get_auth_events(limit: int = 50):
    """Get recent authentication events"""
    return {"events": auth_events[-limit:]}

@app.get("/auth/users")
async def list_users():
    """List all users (for demo purposes)"""
    return {
        "users": [
            {
                "username": username,
                "full_name": user["full_name"],
                "groups": user["groups"],
                "roles": user["roles"]
            }
            for username, user in USERS_DB.items()
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "auth"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
