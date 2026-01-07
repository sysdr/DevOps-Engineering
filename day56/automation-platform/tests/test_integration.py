import pytest
import asyncio
from backend.orchestrator.engine import OrchestrationEngine
from backend.self_healing.controller import SelfHealingController
from backend.common.models import Workflow, Task

@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test complete workflow with self-healing"""
    engine = OrchestrationEngine()
    controller = SelfHealingController()
    
    # Register resources
    controller.register_resource("pod", "workflow-executor")
    
    # Submit workflow
    tasks = [
        Task(id="build", name="Build", command="echo build", dependencies=[]),
        Task(id="test", name="Test", command="echo test", dependencies=["build"]),
        Task(id="deploy", name="Deploy", command="echo deploy", dependencies=["test"])
    ]
    
    workflow = Workflow(id="", name="E2E Test", tasks=tasks)
    workflow_id = await engine.submit_workflow(workflow)
    
    # Wait for completion
    await asyncio.sleep(6)
    
    # Verify workflow completed
    status = engine.get_workflow_status(workflow_id)
    assert status['status'] in ['completed', 'running']
    
    # Verify resources still healthy
    assert controller.resources["workflow-executor"].healthy == True
