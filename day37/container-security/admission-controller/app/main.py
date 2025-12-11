from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import sqlite3

app = FastAPI(title="Admission Controller")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
def init_db():
    conn = sqlite3.connect('admission.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS decisions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT NOT NULL,
                  allowed INTEGER NOT NULL,
                  pod_name TEXT,
                  namespace TEXT,
                  image TEXT,
                  reason TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS policies
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL,
                  check_type TEXT NOT NULL,
                  value TEXT,
                  action TEXT NOT NULL,
                  enabled INTEGER DEFAULT 1)''')
    
    # Insert default policies
    default_policies = [
        ("no-root-user", "security_context", "runAsNonRoot", "reject", 1),
        ("no-privileged", "security_context", "privileged", "reject", 1),
        ("require-resource-limits", "resources", "limits", "reject", 1),
        ("trusted-registry", "image", "trusted-registry.com", "reject", 1),
        ("no-host-path", "volumes", "hostPath", "reject", 1)
    ]
    
    for policy in default_policies:
        c.execute('INSERT OR IGNORE INTO policies (name, check_type, value, action, enabled) VALUES (?, ?, ?, ?, ?)', policy)
    
    conn.commit()
    conn.close()

init_db()

class AdmissionRequest(BaseModel):
    uid: str
    kind: Dict
    resource: Dict
    name: Optional[str]
    namespace: Optional[str]
    operation: str
    object: Dict

class AdmissionResponse(BaseModel):
    uid: str
    allowed: bool
    status: Optional[Dict] = None

class AdmissionReview(BaseModel):
    apiVersion: str = "admission.k8s.io/v1"
    kind: str = "AdmissionReview"
    request: AdmissionRequest

def check_security_context(pod_spec: Dict) -> tuple:
    """Check pod security context"""
    violations = []
    
    containers = pod_spec.get("containers", [])
    
    for container in containers:
        security_context = container.get("securityContext", {})
        
        # Check for root user
        if not security_context.get("runAsNonRoot", False):
            violations.append(f"Container '{container.get('name')}' does not run as non-root user")
        
        # Check for privileged mode
        if security_context.get("privileged", False):
            violations.append(f"Container '{container.get('name')}' runs in privileged mode")
        
        # Check resource limits
        resources = container.get("resources", {})
        if not resources.get("limits"):
            violations.append(f"Container '{container.get('name')}' missing resource limits")
    
    return len(violations) == 0, violations

def check_image_registry(pod_spec: Dict) -> tuple:
    """Check if images are from trusted registry"""
    violations = []
    trusted_registries = ["docker.io", "gcr.io", "trusted-registry.com"]
    
    containers = pod_spec.get("containers", [])
    
    for container in containers:
        image = container.get("image", "")
        
        # Check if image is from trusted registry
        is_trusted = any(image.startswith(registry) for registry in trusted_registries)
        if not is_trusted and "/" in image:
            violations.append(f"Image '{image}' not from trusted registry")
    
    return len(violations) == 0, violations

def check_volumes(pod_spec: Dict) -> tuple:
    """Check for restricted volume types"""
    violations = []
    
    volumes = pod_spec.get("volumes", [])
    
    for volume in volumes:
        if "hostPath" in volume:
            violations.append(f"Volume '{volume.get('name')}' uses restricted hostPath")
    
    return len(violations) == 0, violations

@app.post("/validate")
async def validate(review: Dict):
    """Validate admission request"""
    
    request_data = review.get("request", {})
    uid = request_data.get("uid")
    obj = request_data.get("object", {})
    
    # Extract pod information
    metadata = obj.get("metadata", {})
    pod_name = metadata.get("name", "unknown")
    namespace = request_data.get("namespace", "default")
    
    spec = obj.get("spec", {})
    
    # Get first container image for logging
    containers = spec.get("containers", [])
    image = containers[0].get("image", "unknown") if containers else "unknown"
    
    # Perform checks
    all_passed = True
    all_violations = []
    
    # Security context checks
    passed, violations = check_security_context(spec)
    if not passed:
        all_passed = False
        all_violations.extend(violations)
    
    # Image registry checks
    passed, violations = check_image_registry(spec)
    if not passed:
        all_passed = False
        all_violations.extend(violations)
    
    # Volume checks
    passed, violations = check_volumes(spec)
    if not passed:
        all_passed = False
        all_violations.extend(violations)
    
    # Log decision
    conn = sqlite3.connect('admission.db')
    c = conn.cursor()
    c.execute('''INSERT INTO decisions (timestamp, allowed, pod_name, namespace, image, reason)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (datetime.utcnow().isoformat(), 1 if all_passed else 0,
               pod_name, namespace, image, "; ".join(all_violations) if all_violations else "Approved"))
    conn.commit()
    conn.close()
    
    # Build response
    response = {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": {
            "uid": uid,
            "allowed": all_passed
        }
    }
    
    if not all_passed:
        response["response"]["status"] = {
            "code": 403,
            "message": "Pod violates security policies: " + "; ".join(all_violations)
        }
    
    return response

@app.get("/decisions")
async def get_decisions(limit: int = 50):
    """Get recent admission decisions"""
    conn = sqlite3.connect('admission.db')
    c = conn.cursor()
    c.execute('SELECT * FROM decisions ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    
    decisions = []
    for row in rows:
        decisions.append({
            "id": row[0],
            "timestamp": row[1],
            "allowed": bool(row[2]),
            "pod_name": row[3],
            "namespace": row[4],
            "image": row[5],
            "reason": row[6]
        })
    
    return {"decisions": decisions}

@app.get("/stats")
async def get_stats():
    """Get admission statistics"""
    conn = sqlite3.connect('admission.db')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM decisions WHERE allowed = 1")
    allowed_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM decisions WHERE allowed = 0")
    rejected_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM decisions WHERE timestamp > datetime('now', '-1 hour')")
    recent_count = c.fetchone()[0]
    
    conn.close()
    
    return {
        "allowed": allowed_count,
        "rejected": rejected_count,
        "recent": recent_count,
        "total": allowed_count + rejected_count
    }

@app.get("/policies")
async def get_policies():
    """Get admission policies"""
    conn = sqlite3.connect('admission.db')
    c = conn.cursor()
    c.execute('SELECT * FROM policies WHERE enabled = 1')
    rows = c.fetchall()
    conn.close()
    
    policies = []
    for row in rows:
        policies.append({
            "id": row[0],
            "name": row[1],
            "check_type": row[2],
            "value": row[3],
            "action": row[4],
            "enabled": bool(row[5])
        })
    
    return {"policies": policies}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "admission-controller"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
