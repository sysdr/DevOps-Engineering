from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from enum import Enum
import sys
from pathlib import Path

# Ensure shared config is on path
ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT_DIR / "config"))
from database import get_db, GovernanceWorkflow, ModelMetadata, BiasAnalysis, init_db
from datetime import datetime
import json

app = FastAPI(title="Governance Workflow Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WorkflowState(str, Enum):
    SUBMITTED = "submitted"
    BIAS_ANALYSIS_PENDING = "bias_analysis_pending"
    BIAS_ANALYSIS_FAILED = "bias_analysis_failed"
    BIAS_ANALYSIS_PASSED = "bias_analysis_passed"
    PEER_REVIEW_PENDING = "peer_review_pending"
    ETHICS_REVIEW_PENDING = "ethics_review_pending"
    COMPLIANCE_REVIEW_PENDING = "compliance_review_pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class SubmitRequest(BaseModel):
    model_id: str
    owner: str
    description: Optional[str] = ""

class ReviewRequest(BaseModel):
    model_id: str
    reviewer: str
    decision: str  # approve, reject
    comments: Optional[str] = ""

@app.post("/api/v1/governance/submit")
async def submit_model(request: SubmitRequest, db: Session = Depends(get_db)):
    # Check if already exists
    existing = db.query(GovernanceWorkflow).filter(
        GovernanceWorkflow.model_id == request.model_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Model already in workflow")
    
    # Create new workflow
    workflow = GovernanceWorkflow(
        model_id=request.model_id,
        current_state=WorkflowState.BIAS_ANALYSIS_PENDING,
        submitted_by=request.owner,
        history=json.dumps([{
            'state': WorkflowState.SUBMITTED,
            'timestamp': datetime.utcnow().isoformat(),
            'actor': request.owner
        }]),
        approvals=json.dumps({})
    )
    db.add(workflow)
    db.commit()
    
    return {
        'model_id': request.model_id,
        'state': workflow.current_state,
        'message': 'Model submitted for review. Bias analysis will run automatically.'
    }

@app.post("/api/v1/governance/bias-result")
async def update_bias_result(model_id: str, passed: bool, db: Session = Depends(get_db)):
    workflow = db.query(GovernanceWorkflow).filter(
        GovernanceWorkflow.model_id == model_id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Update state based on bias analysis result
    new_state = WorkflowState.BIAS_ANALYSIS_PASSED if passed else WorkflowState.BIAS_ANALYSIS_FAILED
    
    if passed:
        new_state = WorkflowState.PEER_REVIEW_PENDING
    else:
        new_state = WorkflowState.REJECTED
    
    # Update history
    history = json.loads(workflow.history)
    history.append({
        'state': new_state,
        'timestamp': datetime.utcnow().isoformat(),
        'actor': 'system',
        'bias_passed': passed
    })
    
    workflow.current_state = new_state
    workflow.history = json.dumps(history)
    workflow.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        'model_id': model_id,
        'state': new_state,
        'passed': passed
    }

@app.post("/api/v1/governance/review")
async def submit_review(request: ReviewRequest, db: Session = Depends(get_db)):
    workflow = db.query(GovernanceWorkflow).filter(
        GovernanceWorkflow.model_id == request.model_id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Update approvals
    approvals = json.loads(workflow.approvals) if workflow.approvals else {}
    approvals[workflow.current_state] = {
        'reviewer': request.reviewer,
        'decision': request.decision,
        'comments': request.comments,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Determine next state
    if request.decision == "reject":
        new_state = WorkflowState.REJECTED
    else:
        if workflow.current_state == WorkflowState.PEER_REVIEW_PENDING:
            new_state = WorkflowState.ETHICS_REVIEW_PENDING
        elif workflow.current_state == WorkflowState.ETHICS_REVIEW_PENDING:
            new_state = WorkflowState.COMPLIANCE_REVIEW_PENDING
        elif workflow.current_state == WorkflowState.COMPLIANCE_REVIEW_PENDING:
            new_state = WorkflowState.APPROVED
        else:
            new_state = workflow.current_state
    
    # Update history
    history = json.loads(workflow.history)
    history.append({
        'state': new_state,
        'timestamp': datetime.utcnow().isoformat(),
        'actor': request.reviewer,
        'decision': request.decision,
        'comments': request.comments
    })
    
    workflow.current_state = new_state
    workflow.approvals = json.dumps(approvals)
    workflow.history = json.dumps(history)
    workflow.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        'model_id': request.model_id,
        'new_state': new_state,
        'reviewer': request.reviewer,
        'decision': request.decision
    }

@app.get("/api/v1/governance/status/{model_id}")
async def get_status(model_id: str, db: Session = Depends(get_db)):
    workflow = db.query(GovernanceWorkflow).filter(
        GovernanceWorkflow.model_id == model_id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {
        'model_id': model_id,
        'current_state': workflow.current_state,
        'submitted_by': workflow.submitted_by,
        'submitted_at': workflow.submitted_at.isoformat(),
        'updated_at': workflow.updated_at.isoformat(),
        'history': json.loads(workflow.history),
        'approvals': json.loads(workflow.approvals) if workflow.approvals else {}
    }

@app.get("/api/v1/governance/pending")
async def get_pending_reviews(state: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(GovernanceWorkflow)
    
    if state:
        query = query.filter(GovernanceWorkflow.current_state == state)
    else:
        # All pending states
        query = query.filter(GovernanceWorkflow.current_state.in_([
            WorkflowState.PEER_REVIEW_PENDING,
            WorkflowState.ETHICS_REVIEW_PENDING,
            WorkflowState.COMPLIANCE_REVIEW_PENDING
        ]))
    
    workflows = query.all()
    
    return {
        'pending_count': len(workflows),
        'workflows': [
            {
                'model_id': w.model_id,
                'state': w.current_state,
                'submitted_by': w.submitted_by,
                'submitted_at': w.submitted_at.isoformat(),
                'updated_at': w.updated_at.isoformat()
            }
            for w in workflows
        ]
    }

@app.get("/api/v1/governance/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get aggregated statistics for the dashboard"""
    # Total models (all workflows)
    total_models = db.query(GovernanceWorkflow).count()
    
    # Pending reviews (all pending states)
    pending_reviews = db.query(GovernanceWorkflow).filter(
        GovernanceWorkflow.current_state.in_([
            WorkflowState.PEER_REVIEW_PENDING,
            WorkflowState.ETHICS_REVIEW_PENDING,
            WorkflowState.COMPLIANCE_REVIEW_PENDING,
            WorkflowState.BIAS_ANALYSIS_PENDING
        ])
    ).count()
    
    # Bias detected (failed bias analysis in workflows + failed analyses)
    bias_detected_workflows = db.query(GovernanceWorkflow).filter(
        GovernanceWorkflow.current_state == WorkflowState.BIAS_ANALYSIS_FAILED
    ).count()
    
    # Also count failed bias analyses
    failed_bias_analyses = db.query(BiasAnalysis).filter(
        BiasAnalysis.passed == False
    ).count()
    
    # Use the maximum of both sources (some models might have failed but not in workflow)
    bias_detected = max(bias_detected_workflows, failed_bias_analyses)
    
    # Approved models
    approved = db.query(GovernanceWorkflow).filter(
        GovernanceWorkflow.current_state == WorkflowState.APPROVED
    ).count()
    
    return {
        'total_models': total_models,
        'pending_reviews': pending_reviews,
        'bias_detected': bias_detected,
        'approved': approved
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "governance"}

@app.on_event("startup")
async def startup():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
