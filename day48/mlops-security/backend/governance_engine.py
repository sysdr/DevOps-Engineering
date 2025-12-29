from typing import Dict, Any, List
from datetime import datetime
import uuid

class GovernanceEngine:
    def __init__(self):
        self.workflows = {}
        self.state_transitions = {
            "draft": ["data_validated", "rejected"],
            "data_validated": ["performance_approved", "rejected"],
            "performance_approved": ["security_cleared", "rejected"],
            "security_cleared": ["compliance_verified", "rejected"],
            "compliance_verified": ["approved", "rejected"],
            "approved": ["deployed"],
            "rejected": [],
            "deployed": []
        }
        self.required_approvers = {
            "data_validated": ["data-team-lead"],
            "performance_approved": ["ml-team-lead"],
            "security_cleared": ["security-team"],
            "compliance_verified": ["compliance-officer"],
            "approved": ["engineering-director"]
        }
    
    def create_workflow(self, model_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create new governance workflow"""
        workflow_id = f"wf-{uuid.uuid4().hex[:8]}"
        
        workflow = {
            "workflow_id": workflow_id,
            "model_id": model_id,
            "metadata": metadata,
            "state": "draft",
            "approvals": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self.workflows[workflow_id] = workflow
        
        return {
            "workflow_id": workflow_id,
            "state": "draft",
            "next_stage": "data_validation"
        }
    
    def approve_stage(self, workflow_id: str, stage: str, approver: str, decision: str) -> Dict[str, Any]:
        """Approve or reject a workflow stage"""
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        
        # Record approval
        if stage not in workflow["approvals"]:
            workflow["approvals"][stage] = []
        
        workflow["approvals"][stage].append({
            "approver": approver,
            "decision": decision,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        if decision == "rejected":
            workflow["state"] = "rejected"
            workflow["rejection_reason"] = f"Rejected at {stage} by {approver}"
            return {
                "state": "rejected",
                "reason": workflow["rejection_reason"]
            }
        
        # Check if can transition
        current_state = workflow["state"]
        target_state = stage
        
        # Run automated checks
        checks_passed = self._run_automated_checks(workflow_id, stage)
        
        if not checks_passed:
            return {
                "state": current_state,
                "message": "Automated checks failed",
                "next_stage": stage
            }
        
        # Update state
        workflow["state"] = target_state
        workflow["updated_at"] = datetime.utcnow().isoformat()
        
        # Determine next stage
        next_stage = self._get_next_stage(target_state)
        
        return {
            "state": target_state,
            "next_stage": next_stage
        }
    
    def _run_automated_checks(self, workflow_id: str, stage: str) -> bool:
        """Run automated checks for stage"""
        # In production, this would run actual validation
        # For demo, we pass all checks
        return True
    
    def _get_next_stage(self, current_state: str) -> str:
        """Get next stage in workflow"""
        transitions = self.state_transitions.get(current_state, [])
        if transitions and transitions[0] != "rejected":
            return transitions[0]
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get governance statistics"""
        states = {}
        for wf in self.workflows.values():
            state = wf["state"]
            states[state] = states.get(state, 0) + 1
        
        return {
            "total_workflows": len(self.workflows),
            "by_state": states
        }
