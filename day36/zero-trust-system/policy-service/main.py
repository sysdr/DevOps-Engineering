from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import json

app = FastAPI(title="Zero-Trust Policy Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Policy evaluation events
policy_events = []

# OPA-style policies written in Python (simplified)
# In production, these would be Rego policies evaluated by OPA

POLICIES = {
    "api_access": {
        "allow_rules": [
            {
                "name": "developers_can_read_dev",
                "groups": ["developers"],
                "resources": ["api/data/*"],
                "actions": ["GET"],
                "namespaces": ["dev"]
            },
            {
                "name": "developers_can_write_dev",
                "groups": ["developers", "platform-team"],
                "resources": ["api/data/*"],
                "actions": ["POST", "PUT"],
                "namespaces": ["dev"]
            },
            {
                "name": "operators_full_access",
                "groups": ["operations", "sre-team"],
                "resources": ["*"],
                "actions": ["*"],
                "namespaces": ["*"]
            },
            {
                "name": "readonly_viewers",
                "groups": ["viewers"],
                "resources": ["api/data/*"],
                "actions": ["GET"],
                "namespaces": ["*"]
            }
        ],
        "deny_rules": [
            {
                "name": "no_delete_in_prod",
                "groups": ["developers"],
                "resources": ["*"],
                "actions": ["DELETE"],
                "namespaces": ["prod", "production"]
            }
        ]
    },
    "network_policies": {
        "allowed_connections": [
            {"from": "frontend", "to": "api-gateway", "port": 8080},
            {"from": "api-gateway", "to": "auth-service", "port": 8001},
            {"from": "api-gateway", "to": "resource-service", "port": 8002},
            {"from": "resource-service", "to": "database", "port": 5432}
        ]
    }
}

class PolicyRequest(BaseModel):
    user: Dict
    resource: str
    action: str
    namespace: Optional[str] = "default"

class PolicyResponse(BaseModel):
    allowed: bool
    reason: str
    matched_rules: List[str]
    timestamp: str

class NetworkPolicyRequest(BaseModel):
    from_service: str
    to_service: str
    port: int

def wildcard_match(pattern: str, value: str) -> bool:
    """Simple wildcard matching"""
    if pattern == "*":
        return True
    if pattern.endswith("/*"):
        prefix = pattern[:-2]
        return value.startswith(prefix)
    return pattern == value

def evaluate_policy(request: PolicyRequest) -> PolicyResponse:
    """Evaluate authorization policy"""
    user_groups = request.user.get("groups", [])
    matched_allow_rules = []
    matched_deny_rules = []
    
    # Check deny rules first (deny takes precedence)
    for rule in POLICIES["api_access"]["deny_rules"]:
        if any(group in rule["groups"] for group in user_groups):
            if wildcard_match(rule["resources"][0] if rule["resources"] else "*", request.resource):
                if request.action in rule["actions"] or "*" in rule["actions"]:
                    if rule["namespaces"][0] == "*" or request.namespace in rule["namespaces"]:
                        matched_deny_rules.append(rule["name"])
    
    if matched_deny_rules:
        return PolicyResponse(
            allowed=False,
            reason=f"Denied by policy: {', '.join(matched_deny_rules)}",
            matched_rules=matched_deny_rules,
            timestamp=datetime.utcnow().isoformat()
        )
    
    # Check allow rules
    for rule in POLICIES["api_access"]["allow_rules"]:
        if any(group in rule["groups"] for group in user_groups):
            if wildcard_match(rule["resources"][0] if rule["resources"] else "*", request.resource):
                if request.action in rule["actions"] or "*" in rule["actions"]:
                    if rule["namespaces"][0] == "*" or request.namespace in rule["namespaces"]:
                        matched_allow_rules.append(rule["name"])
    
    if matched_allow_rules:
        return PolicyResponse(
            allowed=True,
            reason=f"Allowed by policy: {', '.join(matched_allow_rules)}",
            matched_rules=matched_allow_rules,
            timestamp=datetime.utcnow().isoformat()
        )
    
    # Default deny
    return PolicyResponse(
        allowed=False,
        reason="No matching allow policy found (default deny)",
        matched_rules=[],
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/policy/evaluate", response_model=PolicyResponse)
async def evaluate(request: PolicyRequest):
    """Evaluate authorization policy for a request"""
    result = evaluate_policy(request)
    
    # Log policy evaluation
    policy_events.append({
        "timestamp": result.timestamp,
        "user": request.user.get("sub", "unknown"),
        "resource": request.resource,
        "action": request.action,
        "namespace": request.namespace,
        "allowed": result.allowed,
        "reason": result.reason,
        "matched_rules": result.matched_rules
    })
    
    return result

@app.post("/policy/network/check")
async def check_network_policy(request: NetworkPolicyRequest):
    """Check if network connection is allowed"""
    allowed_connections = POLICIES["network_policies"]["allowed_connections"]
    
    for conn in allowed_connections:
        if (conn["from"] == request.from_service and 
            conn["to"] == request.to_service and 
            conn["port"] == request.port):
            
            policy_events.append({
                "timestamp": datetime.utcnow().isoformat(),
                "type": "network_policy",
                "from": request.from_service,
                "to": request.to_service,
                "port": request.port,
                "allowed": True
            })
            
            return {
                "allowed": True,
                "reason": f"Network policy allows {request.from_service} -> {request.to_service}:{request.port}"
            }
    
    policy_events.append({
        "timestamp": datetime.utcnow().isoformat(),
        "type": "network_policy",
        "from": request.from_service,
        "to": request.to_service,
        "port": request.port,
        "allowed": False
    })
    
    return {
        "allowed": False,
        "reason": f"No network policy allows {request.from_service} -> {request.to_service}:{request.port}"
    }

@app.get("/policy/events")
async def get_policy_events(limit: int = 50):
    """Get recent policy evaluation events"""
    return {"events": policy_events[-limit:]}

@app.get("/policy/rules")
async def get_policy_rules():
    """Get all configured policies"""
    return {"policies": POLICIES}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "policy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
