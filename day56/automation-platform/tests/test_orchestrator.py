import pytest
import asyncio
from backend.orchestrator.engine import OrchestrationEngine
from backend.common.models import Workflow, Task, WorkflowStatus

@pytest.mark.asyncio
async def test_workflow_execution():
    engine = OrchestrationEngine()
    
    tasks = [
        Task(id="task1", name="Build", command="echo build", dependencies=[]),
        Task(id="task2", name="Test", command="echo test", dependencies=["task1"]),
        Task(id="task3", name="Deploy", command="echo deploy", dependencies=["task2"])
    ]
    
    workflow = Workflow(id="", name="Test Workflow", tasks=tasks)
    workflow_id = await engine.submit_workflow(workflow)
    
    # Wait for completion
    await asyncio.sleep(5)
    
    status = engine.get_workflow_status(workflow_id)
    assert status['status'] == WorkflowStatus.COMPLETED

@pytest.mark.asyncio
async def test_parallel_task_execution():
    engine = OrchestrationEngine()
    
    tasks = [
        Task(id="task1", name="Task1", command="echo 1", dependencies=[]),
        Task(id="task2", name="Task2", command="echo 2", dependencies=[]),
        Task(id="task3", name="Task3", command="echo 3", dependencies=["task1", "task2"])
    ]
    
    workflow = Workflow(id="", name="Parallel Test", tasks=tasks)
    workflow_id = await engine.submit_workflow(workflow)
    
    await asyncio.sleep(5)
    
    status = engine.get_workflow_status(workflow_id)
    assert status['status'] == WorkflowStatus.COMPLETED

def test_dependency_graph():
    engine = OrchestrationEngine()
    
    tasks = [
        Task(id="A", name="A", command="echo A", dependencies=[]),
        Task(id="B", name="B", command="echo B", dependencies=["A"]),
        Task(id="C", name="C", command="echo C", dependencies=["A", "B"])
    ]
    
    graph = engine._build_dependency_graph(tasks)
    assert graph["A"] == []
    assert graph["B"] == ["A"]
    assert "A" in graph["C"] and "B" in graph["C"]
