import asyncio
import uuid
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import logging

from backend.common.models import Workflow, Task, WorkflowStatus, TaskStatus
from backend.common.metrics import (
    workflows_total, workflows_completed, workflows_failed,
    workflow_duration, active_workflows
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchestrationEngine:
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.task_graph: Dict[str, List[str]] = {}
        self.execution_history = defaultdict(list)
        
    async def submit_workflow(self, workflow: Workflow) -> str:
        """Submit a new workflow for execution"""
        workflow.id = str(uuid.uuid4())
        self.workflows[workflow.id] = workflow
        workflows_total.inc()
        active_workflows.inc()
        
        logger.info(f"Submitted workflow {workflow.id}: {workflow.name}")
        
        # Start execution in background
        asyncio.create_task(self.execute_workflow(workflow.id))
        
        return workflow.id
    
    async def execute_workflow(self, workflow_id: str):
        """Execute workflow tasks respecting dependencies"""
        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        start_time = datetime.now()
        
        try:
            # Build dependency graph
            dep_graph = self._build_dependency_graph(workflow.tasks)
            
            # Execute tasks in topological order
            completed_tasks = set()
            
            while len(completed_tasks) < len(workflow.tasks):
                # Find tasks ready to execute
                ready_tasks = [
                    task for task in workflow.tasks
                    if task.status == TaskStatus.WAITING
                    and all(dep in completed_tasks for dep in task.dependencies)
                ]
                
                if not ready_tasks:
                    if len(completed_tasks) < len(workflow.tasks):
                        # Deadlock or failure
                        workflow.status = WorkflowStatus.FAILED
                        break
                    break
                
                # Execute ready tasks in parallel
                await asyncio.gather(*[
                    self._execute_task(task, workflow_id)
                    for task in ready_tasks
                ])
                
                # Update completed tasks
                for task in ready_tasks:
                    if task.status == TaskStatus.COMPLETED:
                        completed_tasks.add(task.id)
                    elif task.status == TaskStatus.FAILED:
                        workflow.status = WorkflowStatus.FAILED
                        break
                
                await asyncio.sleep(0.1)  # Small delay between batches
            
            if workflow.status != WorkflowStatus.FAILED:
                workflow.status = WorkflowStatus.COMPLETED
                workflows_completed.inc()
            else:
                workflows_failed.inc()
                
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            workflow.status = WorkflowStatus.FAILED
            workflows_failed.inc()
        
        finally:
            workflow.completed_at = datetime.now()
            duration = (workflow.completed_at - start_time).total_seconds()
            workflow_duration.observe(duration)
            active_workflows.dec()
            
            # Store execution history
            self.execution_history[workflow.name].append({
                'duration': duration,
                'status': workflow.status,
                'timestamp': workflow.completed_at
            })
    
    async def _execute_task(self, task: Task, workflow_id: str):
        """Execute a single task with retry logic"""
        task.status = TaskStatus.RUNNING
        
        for attempt in range(task.retry_count):
            try:
                # Simulate task execution
                logger.info(f"Executing task {task.name} (attempt {attempt + 1})")
                await asyncio.sleep(0.5)  # Simulate work
                
                task.status = TaskStatus.COMPLETED
                logger.info(f"Task {task.name} completed successfully")
                return
                
            except Exception as e:
                if attempt < task.retry_count - 1:
                    logger.warning(f"Task {task.name} failed, retrying...")
                    await asyncio.sleep(1)
                else:
                    logger.error(f"Task {task.name} failed after {task.retry_count} attempts")
                    task.status = TaskStatus.FAILED
    
    def _build_dependency_graph(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """Build task dependency graph"""
        graph = {task.id: task.dependencies for task in tasks}
        return graph
    
    def get_workflow_status(self, workflow_id: str) -> dict:
        """Get current workflow status"""
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        return {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status,
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "status": task.status
                }
                for task in workflow.tasks
            ],
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
        }

# Global engine instance
engine = OrchestrationEngine()
