from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import docker
import requests
import json
import subprocess
import os
from typing import List, Dict, Any
from datetime import datetime
import hashlib

app = FastAPI(title="Artifact Security API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Docker client
docker_client = docker.from_env()

class ImageSignRequest(BaseModel):
    image: str
    tag: str

class ImageScanRequest(BaseModel):
    image: str

class PolicyEvalRequest(BaseModel):
    image: str

class PromoteRequest(BaseModel):
    source_image: str
    target_env: str

# In-memory storage for demo
image_registry = {}
scan_results = {}
signatures = {}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/api/images")
async def list_images():
    try:
        images = docker_client.images.list()
        image_list = []
        for img in images[:10]:  # Limit for demo
            if img.tags:
                image_data = {
                    "id": img.short_id,
                    "tags": img.tags,
                    "created": str(img.attrs.get('Created', '')),
                    "size": img.attrs.get('Size', 0),
                    "signed": img.tags[0] in signatures if img.tags else False
                }
                image_list.append(image_data)
        return {"images": image_list, "count": len(image_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sign")
async def sign_image(request: ImageSignRequest):
    image_name = f"{request.image}:{request.tag}"
    
    try:
        # Pull image if not exists
        docker_client.images.pull(request.image, tag=request.tag)
        
        # Add to image registry
        image_registry[image_name] = {
            "image": image_name,
            "added_at": datetime.utcnow().isoformat(),
            "status": "available"
        }
        
        # Simulate Cosign signing (in production, use actual cosign)
        signature_data = {
            "image": image_name,
            "signature": hashlib.sha256(image_name.encode()).hexdigest(),
            "signed_at": datetime.utcnow().isoformat(),
            "algorithm": "ecdsa-p256",
            "keyless": True,
            "transparency_log": "rekor.sigstore.dev"
        }
        
        signatures[image_name] = signature_data
        
        return {
            "message": f"Image {image_name} signed successfully",
            "signature": signature_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signing failed: {str(e)}")

@app.post("/api/scan")
async def scan_image(request: ImageScanRequest):
    try:
        # Add to image registry if not already present
        if request.image not in image_registry:
            image_registry[request.image] = {
                "image": request.image,
                "added_at": datetime.utcnow().isoformat(),
                "status": "scanned"
            }
        
        # Simulate vulnerability scanning (Trivy integration)
        vulnerabilities = [
            {"id": "CVE-2023-1234", "severity": "HIGH", "package": "openssl"},
            {"id": "CVE-2023-5678", "severity": "MEDIUM", "package": "curl"},
            {"id": "CVE-2023-9012", "severity": "LOW", "package": "bash"}
        ]
        
        scan_result = {
            "image": request.image,
            "scanned_at": datetime.utcnow().isoformat(),
            "vulnerabilities": vulnerabilities,
            "total_vulnerabilities": len(vulnerabilities),
            "high_severity": len([v for v in vulnerabilities if v["severity"] == "HIGH"]),
            "medium_severity": len([v for v in vulnerabilities if v["severity"] == "MEDIUM"]),
            "low_severity": len([v for v in vulnerabilities if v["severity"] == "LOW"])
        }
        
        scan_results[request.image] = scan_result
        
        return scan_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@app.post("/api/policy/evaluate")
async def evaluate_policy(request: PolicyEvalRequest):
    image = request.image
    
    # Check if signed
    is_signed = image in signatures
    
    # Check scan results
    scan_data = scan_results.get(image, {})
    high_vulns = scan_data.get("high_severity", 0)
    
    # Policy evaluation
    policy_result = {
        "image": image,
        "evaluated_at": datetime.utcnow().isoformat(),
        "policies": {
            "signature_required": {"status": "PASS" if is_signed else "FAIL", "required": True},
            "max_high_vulnerabilities": {"status": "PASS" if high_vulns <= 2 else "FAIL", "limit": 2, "actual": high_vulns},
            "trusted_registry": {"status": "PASS", "registry": "localhost:8080"}
        },
        "overall_status": "APPROVED" if is_signed and high_vulns <= 2 else "REJECTED"
    }
    
    return policy_result

@app.post("/api/promote")
async def promote_image(request: PromoteRequest):
    try:
        # Check policy compliance first
        policy_result = await evaluate_policy(PolicyEvalRequest(image=request.source_image))
        
        if policy_result["overall_status"] != "APPROVED":
            raise HTTPException(status_code=403, detail="Image failed policy evaluation")
        
        promotion_result = {
            "source_image": request.source_image,
            "target_environment": request.target_env,
            "promoted_at": datetime.utcnow().isoformat(),
            "status": "SUCCESS",
            "attestation": {
                "signature_verified": True,
                "vulnerabilities_acceptable": True,
                "promotion_approved_by": "system"
            }
        }
        
        return promotion_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Promotion failed: {str(e)}")

@app.get("/api/security-metrics")
async def get_security_metrics():
    try:
        # Get actual Docker images count
        docker_images = docker_client.images.list()
        total_images = len(docker_images)
        signed_images = len(signatures)
        scanned_images = len(scan_results)
        
        return {
            "total_images": total_images,
            "signed_images": signed_images,
            "scanned_images": scanned_images,
            "signature_coverage": round((signed_images / max(total_images, 1)) * 100, 2),
            "high_risk_images": sum(1 for scan in scan_results.values() if scan.get("high_severity", 0) > 2),
            "compliance_score": round(((signed_images + scanned_images) / max(total_images * 2, 1)) * 100, 2)
        }
    except Exception as e:
        # Fallback to in-memory data if Docker is not available
        total_images = len(image_registry) + 10
        signed_images = len(signatures)
        scanned_images = len(scan_results)
        
        return {
            "total_images": total_images,
            "signed_images": signed_images,
            "scanned_images": scanned_images,
            "signature_coverage": round((signed_images / max(total_images, 1)) * 100, 2),
            "high_risk_images": sum(1 for scan in scan_results.values() if scan.get("high_severity", 0) > 2),
            "compliance_score": round(((signed_images + scanned_images) / max(total_images * 2, 1)) * 100, 2)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
