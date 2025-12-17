"""Main FastAPI application for Supply Chain Security"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import uuid
from datetime import datetime
import asyncio

app = FastAPI(title="Supply Chain Security System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data directories
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
SBOM_DIR = os.path.join(DATA_DIR, "sboms")
SIG_DIR = os.path.join(DATA_DIR, "signatures")
SCAN_DIR = os.path.join(DATA_DIR, "scans")

os.makedirs(SBOM_DIR, exist_ok=True)
os.makedirs(SIG_DIR, exist_ok=True)
os.makedirs(SCAN_DIR, exist_ok=True)

# In-memory storage
artifacts = {}
policies = {}

# Models
class Artifact(BaseModel):
    id: str
    name: str
    version: str
    type: str
    registry: Optional[str] = None
    digest: Optional[str] = None
    created_at: str
    status: str = "UNSIGNED"

class SBOMRequest(BaseModel):
    artifact_id: str
    image_name: str
    format: str = "cyclonedx"

class SignRequest(BaseModel):
    artifact_id: str
    signer: str

class VerifyRequest(BaseModel):
    artifact_id: str

class ScanRequest(BaseModel):
    artifact_id: str

class Policy(BaseModel):
    name: str
    description: str
    rules: List[Dict[str, Any]]
    action: str
    enabled: bool = True

class PolicyEvalRequest(BaseModel):
    artifact_id: str
    policy_name: str

# Helper functions
def generate_mock_sbom(artifact_id: str, image_name: str) -> Dict[str, Any]:
    """Generate mock SBOM in CycloneDX format"""
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "component": {
                "type": "container",
                "name": image_name,
                "version": "latest"
            }
        },
        "components": [
            {
                "type": "library",
                "name": "fastapi",
                "version": "0.109.0",
                "purl": "pkg:pypi/fastapi@0.109.0",
                "licenses": [{"license": {"id": "MIT"}}],
                "hashes": [{"alg": "SHA-256", "content": "abc123..."}]
            },
            {
                "type": "library",
                "name": "uvicorn",
                "version": "0.27.0",
                "purl": "pkg:pypi/uvicorn@0.27.0",
                "licenses": [{"license": {"id": "BSD-3-Clause"}}],
                "hashes": [{"alg": "SHA-256", "content": "def456..."}]
            },
            {
                "type": "library",
                "name": "pydantic",
                "version": "2.5.3",
                "purl": "pkg:pypi/pydantic@2.5.3",
                "licenses": [{"license": {"id": "MIT"}}],
                "hashes": [{"alg": "SHA-256", "content": "ghi789..."}]
            },
            {
                "type": "library",
                "name": "openssl",
                "version": "3.0.2",
                "purl": "pkg:deb/debian/openssl@3.0.2",
                "licenses": [{"license": {"id": "Apache-2.0"}}],
                "hashes": [{"alg": "SHA-256", "content": "jkl012..."}]
            },
            {
                "type": "library",
                "name": "libssl1.1",
                "version": "1.1.1f",
                "purl": "pkg:deb/debian/libssl1.1@1.1.1f",
                "licenses": [{"license": {"id": "OpenSSL"}}],
                "hashes": [{"alg": "SHA-256", "content": "mno345..."}]
            }
        ],
        "dependencies": [
            {
                "ref": "pkg:pypi/fastapi@0.109.0",
                "dependsOn": ["pkg:pypi/pydantic@2.5.3"]
            }
        ]
    }

def generate_mock_vulnerabilities(artifact_id: str) -> List[Dict[str, Any]]:
    """Generate mock vulnerability scan results"""
    return [
        {
            "id": "CVE-2023-44487",
            "severity": "HIGH",
            "cvss_score": 7.5,
            "package": "openssl",
            "version": "3.0.2",
            "fixed_version": "3.0.12",
            "description": "HTTP/2 Rapid Reset vulnerability in OpenSSL",
            "references": ["https://nvd.nist.gov/vuln/detail/CVE-2023-44487"],
            "exploit_available": True,
            "patch_available": True
        },
        {
            "id": "CVE-2023-12345",
            "severity": "CRITICAL",
            "cvss_score": 9.8,
            "package": "libssl1.1",
            "version": "1.1.1f",
            "fixed_version": "1.1.1w",
            "description": "Remote code execution in libssl",
            "references": ["https://nvd.nist.gov/vuln/detail/CVE-2023-12345"],
            "exploit_available": True,
            "patch_available": True
        },
        {
            "id": "CVE-2024-00001",
            "severity": "MEDIUM",
            "cvss_score": 5.3,
            "package": "pydantic",
            "version": "2.5.3",
            "fixed_version": "2.6.0",
            "description": "Input validation bypass",
            "references": ["https://nvd.nist.gov/vuln/detail/CVE-2024-00001"],
            "exploit_available": False,
            "patch_available": True
        }
    ]

def generate_mock_signature(artifact_id: str, signer: str) -> Dict[str, Any]:
    """Generate mock signature"""
    return {
        "artifact_id": artifact_id,
        "signature": f"MEUCIQDxxx...{uuid.uuid4().hex[:16]}",
        "signer": signer,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "algorithm": "ECDSA-SHA256",
        "rekor_entry": f"https://rekor.sigstore.dev/api/v1/log/entries/{uuid.uuid4()}",
        "certificate": "-----BEGIN CERTIFICATE-----\nMIIB...xxx\n-----END CERTIFICATE-----"
    }

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Supply Chain Security System API",
        "version": "1.0.0",
        "endpoints": {
            "artifacts": "/api/artifacts",
            "sbom": "/api/sbom/*",
            "sign": "/api/sign",
            "verify": "/api/verify",
            "scan": "/api/scan/*",
            "policies": "/api/policies/*"
        }
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/artifacts")
async def create_artifact(artifact: Artifact):
    """Register a new artifact"""
    artifacts[artifact.id] = artifact.model_dump()
    return {"status": "success", "artifact": artifacts[artifact.id]}

@app.get("/api/artifacts")
async def list_artifacts():
    """List all registered artifacts"""
    return {"artifacts": list(artifacts.values()), "count": len(artifacts)}

@app.get("/api/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    """Get artifact details"""
    if artifact_id not in artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifacts[artifact_id]

@app.post("/api/sbom/generate")
async def generate_sbom(request: SBOMRequest, background_tasks: BackgroundTasks):
    """Generate SBOM for an artifact"""
    if request.artifact_id not in artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    # Generate SBOM
    sbom_data = generate_mock_sbom(request.artifact_id, request.image_name)
    
    # Save SBOM
    sbom_path = os.path.join(SBOM_DIR, f"{request.artifact_id}.json")
    with open(sbom_path, 'w') as f:
        json.dump(sbom_data, f, indent=2)
    
    # Update artifact status
    artifacts[request.artifact_id]["status"] = "SBOM_GENERATED"
    artifacts[request.artifact_id]["sbom_path"] = sbom_path
    artifacts[request.artifact_id]["component_count"] = len(sbom_data["components"])
    
    return {
        "status": "success",
        "artifact_id": request.artifact_id,
        "sbom_path": sbom_path,
        "component_count": len(sbom_data["components"]),
        "format": request.format
    }

@app.get("/api/sbom/{artifact_id}")
async def get_sbom(artifact_id: str):
    """Retrieve SBOM for an artifact"""
    if artifact_id not in artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    sbom_path = os.path.join(SBOM_DIR, f"{artifact_id}.json")
    if not os.path.exists(sbom_path):
        raise HTTPException(status_code=404, detail="SBOM not found")
    
    with open(sbom_path, 'r') as f:
        sbom_data = json.load(f)
    
    return sbom_data

@app.post("/api/sign")
async def sign_artifact(request: SignRequest):
    """Sign an artifact"""
    if request.artifact_id not in artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    # Generate signature
    signature_data = generate_mock_signature(request.artifact_id, request.signer)
    
    # Save signature
    sig_path = os.path.join(SIG_DIR, f"{request.artifact_id}.json")
    with open(sig_path, 'w') as f:
        json.dump(signature_data, f, indent=2)
    
    # Update artifact status
    artifacts[request.artifact_id]["status"] = "SIGNED"
    artifacts[request.artifact_id]["signature_path"] = sig_path
    artifacts[request.artifact_id]["signer"] = request.signer
    
    return {
        "status": "success",
        "artifact_id": request.artifact_id,
        "signature": signature_data["signature"][:20] + "...",
        "rekor_entry": signature_data["rekor_entry"]
    }

@app.post("/api/verify")
async def verify_signature(request: VerifyRequest):
    """Verify artifact signature"""
    if request.artifact_id not in artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    sig_path = os.path.join(SIG_DIR, f"{request.artifact_id}.json")
    if not os.path.exists(sig_path):
        raise HTTPException(status_code=404, detail="Signature not found")
    
    with open(sig_path, 'r') as f:
        signature_data = json.load(f)
    
    # Mock verification
    verified = True
    
    # Update artifact status
    if verified:
        artifacts[request.artifact_id]["status"] = "VERIFIED"
    
    return {
        "status": "success",
        "artifact_id": request.artifact_id,
        "verified": verified,
        "signer": signature_data["signer"],
        "timestamp": signature_data["timestamp"],
        "rekor_entry": signature_data["rekor_entry"]
    }

@app.post("/api/scan/vulnerabilities")
async def scan_vulnerabilities(request: ScanRequest):
    """Scan artifact for vulnerabilities"""
    if request.artifact_id not in artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    # Generate vulnerability report
    vulnerabilities = generate_mock_vulnerabilities(request.artifact_id)
    
    # Save scan results
    scan_path = os.path.join(SCAN_DIR, f"{request.artifact_id}.json")
    scan_data = {
        "artifact_id": request.artifact_id,
        "scanned_at": datetime.utcnow().isoformat() + "Z",
        "vulnerabilities": vulnerabilities,
        "summary": {
            "total": len(vulnerabilities),
            "critical": sum(1 for v in vulnerabilities if v["severity"] == "CRITICAL"),
            "high": sum(1 for v in vulnerabilities if v["severity"] == "HIGH"),
            "medium": sum(1 for v in vulnerabilities if v["severity"] == "MEDIUM"),
            "low": sum(1 for v in vulnerabilities if v["severity"] == "LOW")
        }
    }
    
    with open(scan_path, 'w') as f:
        json.dump(scan_data, f, indent=2)
    
    # Update artifact status while keeping signing/verification state
    current_status = artifacts[request.artifact_id].get("status", "UNSIGNED")
    artifacts[request.artifact_id]["vulnerabilities"] = scan_data["summary"]
    if scan_data["summary"]["critical"] == 0 and scan_data["summary"]["high"] == 0:
        artifacts[request.artifact_id]["status"] = "COMPLIANT"
    elif current_status in ["SIGNED", "VERIFIED"]:
        artifacts[request.artifact_id]["status"] = current_status
    else:
        artifacts[request.artifact_id]["status"] = "SCANNED"
    
    return scan_data

@app.get("/api/scan/{artifact_id}")
async def get_scan_results(artifact_id: str):
    """Get vulnerability scan results"""
    if artifact_id not in artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    scan_path = os.path.join(SCAN_DIR, f"{artifact_id}.json")
    if not os.path.exists(scan_path):
        raise HTTPException(status_code=404, detail="Scan results not found")
    
    with open(scan_path, 'r') as f:
        scan_data = json.load(f)
    
    return scan_data

@app.post("/api/policies")
async def create_policy(policy: Policy):
    """Create a new policy"""
    policy_id = policy.name.lower().replace(" ", "_")
    policies[policy_id] = policy.model_dump()
    return {"status": "success", "policy_id": policy_id, "policy": policies[policy_id]}

@app.get("/api/policies")
async def list_policies():
    """List all policies"""
    return {"policies": list(policies.values()), "count": len(policies)}

@app.post("/api/policies/evaluate")
async def evaluate_policy(request: PolicyEvalRequest):
    """Evaluate policy against artifact"""
    if request.artifact_id not in artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    if request.policy_name not in policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    artifact = artifacts[request.artifact_id]
    policy = policies[request.policy_name]
    
    # Simple policy evaluation logic
    violations = []
    compliant = True
    
    # Check if artifact has vulnerabilities
    if "vulnerabilities" in artifact:
        vuln_summary = artifact["vulnerabilities"]
        if vuln_summary["critical"] > 0:
            violations.append("Contains CRITICAL vulnerabilities")
            compliant = False
        if vuln_summary["high"] > 2:
            violations.append("Contains more than 2 HIGH vulnerabilities")
            compliant = False
    
    # Check signature status
    if artifact["status"] not in ["VERIFIED", "APPROVED"]:
        violations.append("Artifact not signed or verified")
        compliant = False
    
    # Update artifact status
    if compliant:
        artifacts[request.artifact_id]["status"] = "COMPLIANT"
    else:
        artifacts[request.artifact_id]["status"] = "REJECTED"
    
    return {
        "artifact_id": request.artifact_id,
        "policy_name": request.policy_name,
        "compliant": compliant,
        "violations": violations,
        "evaluated_at": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    total_artifacts = len(artifacts)
    signed = sum(1 for a in artifacts.values() if a.get("status") in ["SIGNED", "VERIFIED", "COMPLIANT"])
    verified = sum(1 for a in artifacts.values() if a.get("status") in ["VERIFIED", "COMPLIANT"])
    compliant = sum(1 for a in artifacts.values() if a.get("status") == "COMPLIANT")
    
    total_vulns = 0
    critical = 0
    high = 0
    
    for artifact in artifacts.values():
        if "vulnerabilities" in artifact:
            v = artifact["vulnerabilities"]
            total_vulns += v.get("total", 0)
            critical += v.get("critical", 0)
            high += v.get("high", 0)
    
    return {
        "artifacts": {
            "total": total_artifacts,
            "signed": signed,
            "verified": verified,
            "compliant": compliant
        },
        "vulnerabilities": {
            "total": total_vulns,
            "critical": critical,
            "high": high
        },
        "policies": {
            "total": len(policies),
            "active": sum(1 for p in policies.values() if p.get("enabled", True))
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
