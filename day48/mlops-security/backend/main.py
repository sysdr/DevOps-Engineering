from fastapi import FastAPI, HTTPException, WebSocket, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
from datetime import datetime
import hashlib

app = FastAPI(title="MLOps Security & Governance")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
governance_workflows = {}
audit_chain = []
bias_metrics = {}
security_stats = {
    "total_requests": 0,
    "adversarial_blocked": 0,
    "clean_requests": 0
}

from security_gateway import SecurityGateway
from governance_engine import GovernanceEngine
from bias_monitor import BiasMonitor
from compliance_tracker import ComplianceTracker
from audit_system import AuditSystem

security_gateway = SecurityGateway()
governance_engine = GovernanceEngine()
bias_monitor = BiasMonitor()
compliance_tracker = ComplianceTracker()
audit_system = AuditSystem()

class ValidationRequest(BaseModel):
    model_id: str
    input: Dict[str, Any]

class SubmitModelRequest(BaseModel):
    model_id: str
    metadata: Dict[str, Any]

class ApprovalRequest(BaseModel):
    workflow_id: str
    stage: str
    approver: str
    decision: str

class BiasAnalysisRequest(BaseModel):
    model_id: str
    predictions: List[Dict[str, Any]]

@app.post("/api/security/validate")
async def validate_input(request: ValidationRequest):
    result = security_gateway.detect_adversarial(request.model_id, request.input)
    
    security_stats["total_requests"] += 1
    if result["adversarial"]:
        security_stats["adversarial_blocked"] += 1
    else:
        security_stats["clean_requests"] += 1
    
    audit_system.log_event({
        "type": "security_check",
        "model_id": request.model_id,
        "adversarial": result["adversarial"],
        "confidence": result["confidence"]
    })
    
    return result

@app.post("/api/governance/submit")
async def submit_model(request: SubmitModelRequest):
    workflow = governance_engine.create_workflow(request.model_id, request.metadata)
    
    audit_system.log_event({
        "type": "governance_submission",
        "model_id": request.model_id,
        "workflow_id": workflow["workflow_id"]
    })
    
    return workflow

@app.post("/api/governance/approve")
async def approve_stage(request: ApprovalRequest):
    result = governance_engine.approve_stage(
        request.workflow_id,
        request.stage,
        request.approver,
        request.decision
    )
    
    audit_system.log_event({
        "type": "governance_approval",
        "workflow_id": request.workflow_id,
        "stage": request.stage,
        "approver": request.approver,
        "decision": request.decision
    })
    
    return result

@app.post("/api/bias/analyze")
async def analyze_bias(request: BiasAnalysisRequest):
    result = bias_monitor.calculate_fairness_metrics(
        request.model_id,
        request.predictions
    )
    
    audit_system.log_event({
        "type": "bias_analysis",
        "model_id": request.model_id,
        "violations": result.get("violations", [])
    })
    
    return result

@app.get("/api/compliance/model-card/{model_id}/download")
async def download_model_card(model_id: str):
    card = compliance_tracker.generate_model_card(model_id)
    json_str = json.dumps(card, indent=2)
    filename = f"{model_id}_model_card.json"
    
    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@app.get("/api/compliance/model-card/{model_id}")
async def get_model_card(model_id: str):
    card = compliance_tracker.generate_model_card(model_id)
    return card

@app.get("/api/audit/events")
async def get_audit_events(limit: int = 10, model_id: Optional[str] = None):
    events = audit_system.get_events(limit, model_id)
    return {"events": events}

@app.get("/api/audit/verify")
async def verify_audit_chain():
    result = audit_system.verify_chain_integrity()
    return result

@app.get("/api/stats")
async def get_stats():
    return {
        "security": security_stats,
        "governance": governance_engine.get_stats(),
        "bias": bias_monitor.get_stats(),
        "audit": audit_system.get_stats()
    }

@app.websocket("/ws/stats")
async def websocket_stats(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            stats = {
                "security": security_stats,
                "governance": governance_engine.get_stats(),
                "bias": bias_monitor.get_stats(),
                "audit": audit_system.get_stats(),
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_json(stats)
            await asyncio.sleep(1)
    except:
        pass

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
