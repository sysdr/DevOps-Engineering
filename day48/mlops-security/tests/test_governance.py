import sys
sys.path.append('..')

from backend.governance_engine import GovernanceEngine

def test_workflow_creation():
    engine = GovernanceEngine()
    
    workflow = engine.create_workflow("test_model_v1", {
        "version": "1.0.0",
        "algorithm": "XGBoost"
    })
    
    assert workflow["state"] == "draft"
    print("✓ Workflow creation passed")

def test_approval_flow():
    engine = GovernanceEngine()
    
    workflow = engine.create_workflow("test_model_v2", {})
    wf_id = workflow["workflow_id"]
    
    # Approve data validation
    result = engine.approve_stage(wf_id, "data_validated", "data-team-lead", "approved")
    assert result["state"] == "data_validated"
    print("✓ Data validation approval passed")
    
    # Approve performance
    result = engine.approve_stage(wf_id, "performance_approved", "ml-team-lead", "approved")
    assert result["state"] == "performance_approved"
    print("✓ Performance approval passed")

def test_rejection():
    engine = GovernanceEngine()
    
    workflow = engine.create_workflow("test_model_v3", {})
    wf_id = workflow["workflow_id"]
    
    result = engine.approve_stage(wf_id, "data_validated", "data-team-lead", "rejected")
    assert result["state"] == "rejected"
    print("✓ Rejection handling passed")

if __name__ == "__main__":
    test_workflow_creation()
    test_approval_flow()
    test_rejection()
    print("\n✅ All governance tests passed!")
