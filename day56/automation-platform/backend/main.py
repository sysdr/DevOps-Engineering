from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest
from fastapi.responses import Response
import asyncio
import json
import logging
from datetime import datetime, timedelta
import random
import uuid

from backend.orchestrator.engine import engine
from backend.self_healing.controller import controller
from backend.scheduler.ai_scheduler import scheduler
from backend.chaos.framework import chaos_framework
from backend.incidents.detector import incident_detector
from backend.common.models import Workflow, Task, WorkflowStatus, TaskStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Automation Orchestration Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
active_connections = []

@app.on_event("startup")
async def startup():
    """Initialize all subsystems"""
    logger.info("Starting automation platform...")
    
    # Start all background services
    await controller.start()
    await scheduler.start()
    await chaos_framework.start()
    await incident_detector.start()
    
    # Register some initial resources
    for i in range(10):
        controller.register_resource("pod", f"pod-{i}")
    for i in range(3):
        controller.register_resource("node", f"node-{i}")
    
    # Create sample workflows to populate dashboard
    logger.info("Creating sample workflows...")
    sample_workflows = [
        {
            "name": "Data Pipeline Processing",
            "tasks": [
                {"name": "Extract Data", "command": "echo 'Extracting data'", "dependencies": []},
                {"name": "Transform Data", "command": "echo 'Transforming data'", "dependencies": [0]},
                {"name": "Load Data", "command": "echo 'Loading data'", "dependencies": [1]}
            ]
        },
        {
            "name": "CI/CD Deployment",
            "tasks": [
                {"name": "Build", "command": "echo 'Building'", "dependencies": []},
                {"name": "Test", "command": "echo 'Testing'", "dependencies": [0]},
                {"name": "Deploy", "command": "echo 'Deploying'", "dependencies": [1]}
            ]
        },
        {
            "name": "Backup Automation",
            "tasks": [
                {"name": "Create Snapshot", "command": "echo 'Creating snapshot'", "dependencies": []},
                {"name": "Verify Backup", "command": "echo 'Verifying backup'", "dependencies": [0]}
            ]
        },
        {
            "name": "Monitoring Setup",
            "tasks": [
                {"name": "Configure Metrics", "command": "echo 'Configuring metrics'", "dependencies": []},
                {"name": "Setup Alerts", "command": "echo 'Setting up alerts'", "dependencies": [0]}
            ]
        },
        {
            "name": "Security Scan",
            "tasks": [
                {"name": "Vulnerability Scan", "command": "echo 'Scanning vulnerabilities'", "dependencies": []},
                {"name": "Generate Report", "command": "echo 'Generating report'", "dependencies": [0]}
            ]
        }
    ]
    
    # Submit sample workflows
    for workflow_data in sample_workflows:
        try:
            tasks = []
            for i, task_data in enumerate(workflow_data.get('tasks', [])):
                # Convert dependency indices to task IDs
                task_deps = [f"task-{dep}" for dep in task_data.get('dependencies', [])]
                task = Task(
                    id=f"task-{i}",
                    name=task_data['name'],
                    dependencies=task_deps,
                    command=task_data.get('command', 'echo "task"')
                )
                tasks.append(task)
            
            workflow = Workflow(
                id="",
                name=workflow_data.get('name', 'unnamed'),
                tasks=tasks
            )
            
            # Determine workflow status before submission
            rand_val = random.random()
            should_complete = rand_val < 0.5  # 50% completed
            should_fail = 0.5 <= rand_val < 0.7  # 20% failed
            should_run = rand_val >= 0.7  # 30% running
            
            if should_complete or should_fail:
                # Add workflow directly without starting execution
                workflow.id = str(uuid.uuid4())
                engine.workflows[workflow.id] = workflow
                
                if should_complete:
                    workflow.status = WorkflowStatus.COMPLETED
                    workflow.completed_at = datetime.now()
                    workflow.started_at = datetime.now() - timedelta(seconds=60)
                    for task in workflow.tasks:
                        task.status = TaskStatus.COMPLETED
                else:  # should_fail
                    workflow.status = WorkflowStatus.FAILED
                    workflow.completed_at = datetime.now()
                    workflow.started_at = datetime.now() - timedelta(seconds=60)
                    if workflow.tasks:
                        workflow.tasks[0].status = TaskStatus.FAILED
                        for task in workflow.tasks[1:]:
                            task.status = TaskStatus.SKIPPED
                
                workflow_id = workflow.id
            else:
                # Submit workflow normally (will run)
                workflow_id = await engine.submit_workflow(workflow)
            
            # Add some workflows to scheduler
            if random.random() < 0.4:  # 40% scheduled
                scheduler.scheduled_workflows.append({
                    'workflow_id': workflow_id,
                    'workflow_name': workflow.name,
                    'scheduled_at': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error creating sample workflow: {e}")
    
    logger.info(f"Created {len(sample_workflows)} sample workflows")
    
    # Create sample healing actions
    logger.info("Creating sample healing actions...")
    sample_healing_actions = [
        {'resource_id': 'pod-0', 'action': 'restart_pod', 'success': True, 'duration': 2.3, 'timestamp': datetime.now() - timedelta(minutes=15)},
        {'resource_id': 'pod-2', 'action': 'restart_pod', 'success': True, 'duration': 1.8, 'timestamp': datetime.now() - timedelta(minutes=30)},
        {'resource_id': 'node-1', 'action': 'drain_and_replace', 'success': True, 'duration': 45.2, 'timestamp': datetime.now() - timedelta(hours=1)},
        {'resource_id': 'pod-5', 'action': 'restart_pod', 'success': True, 'duration': 2.1, 'timestamp': datetime.now() - timedelta(minutes=45)},
        {'resource_id': 'pod-7', 'action': 'restart_pod', 'success': False, 'duration': 5.0, 'timestamp': datetime.now() - timedelta(minutes=20), 'error': 'Timeout'},
        {'resource_id': 'pod-9', 'action': 'restart_pod', 'success': True, 'duration': 1.9, 'timestamp': datetime.now() - timedelta(minutes=10)},
    ]
    controller.healing_actions.extend(sample_healing_actions)
    logger.info(f"Created {len(sample_healing_actions)} sample healing actions")
    
    # Create sample incidents
    logger.info("Creating sample incidents...")
    from backend.common.models import Incident, IncidentSeverity
    sample_incidents = [
        Incident(
            id=str(uuid.uuid4()),
            severity=IncidentSeverity.HIGH,
            description="Detected high_error_rate",
            detected_at=datetime.now() - timedelta(hours=2),
            resolved_at=datetime.now() - timedelta(hours=1, minutes=45),
            auto_resolved=True,
            remediation_actions=['rollback_deployment', 'scale_up']
        ),
        Incident(
            id=str(uuid.uuid4()),
            severity=IncidentSeverity.MEDIUM,
            description="Detected high_latency",
            detected_at=datetime.now() - timedelta(hours=1),
            resolved_at=datetime.now() - timedelta(minutes=45),
            auto_resolved=True,
            remediation_actions=['scale_up', 'check_dependencies']
        ),
        Incident(
            id=str(uuid.uuid4()),
            severity=IncidentSeverity.CRITICAL,
            description="Detected service_down",
            detected_at=datetime.now() - timedelta(minutes=30),
            resolved_at=datetime.now() - timedelta(minutes=20),
            auto_resolved=True,
            remediation_actions=['restart_service', 'failover']
        ),
        Incident(
            id=str(uuid.uuid4()),
            severity=IncidentSeverity.HIGH,
            description="Detected resource_exhaustion",
            detected_at=datetime.now() - timedelta(minutes=5),
            resolved_at=None,
            auto_resolved=False,
            remediation_actions=['scale_up']
        ),
        Incident(
            id=str(uuid.uuid4()),
            severity=IncidentSeverity.MEDIUM,
            description="Detected high_latency",
            detected_at=datetime.now() - timedelta(minutes=2),
            resolved_at=None,
            auto_resolved=False,
            remediation_actions=['scale_up', 'check_dependencies']
        ),
    ]
    for incident in sample_incidents:
        incident_detector.incidents[incident.id] = incident
        if not incident.resolved_at:
            incident_detector.active_incidents.append(incident.id)
    logger.info(f"Created {len(sample_incidents)} sample incidents")
    
    logger.info("Platform initialized successfully")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

@app.post("/api/workflows/submit")
async def submit_workflow(workflow_data: dict):
    """Submit new workflow for execution"""
    tasks = [
        Task(
            id=f"task-{i}",
            name=task['name'],
            dependencies=task.get('dependencies', []),
            command=task.get('command', 'echo "task"')
        )
        for i, task in enumerate(workflow_data.get('tasks', []))
    ]
    
    workflow = Workflow(
        id="",
        name=workflow_data.get('name', 'unnamed'),
        tasks=tasks
    )
    
    workflow_id = await engine.submit_workflow(workflow)
    
    # Notify WebSocket clients
    await broadcast_update({
        'type': 'workflow_submitted',
        'workflow_id': workflow_id
    })
    
    return {"workflow_id": workflow_id, "status": "submitted"}

@app.get("/api/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get workflow execution status"""
    return engine.get_workflow_status(workflow_id)

@app.get("/api/workflows/stats")
async def get_workflow_stats():
    """Get workflow statistics"""
    return {
        'total_workflows': len(engine.workflows),
        'active_workflows': sum(1 for w in engine.workflows.values() if w.status == 'running'),
        'scheduler_stats': scheduler.get_scheduler_stats()
    }

@app.get("/api/healing/stats")
async def get_healing_stats():
    """Get self-healing statistics"""
    return controller.get_healing_stats()

@app.get("/api/chaos/stats")
async def get_chaos_stats():
    """Get chaos experiment statistics"""
    return chaos_framework.get_experiment_stats()

@app.post("/api/chaos/inject/{experiment_type}")
async def inject_chaos(experiment_type: str):
    """Manually trigger chaos experiment"""
    result = await chaos_framework.inject_failure(experiment_type)
    
    await broadcast_update({
        'type': 'chaos_experiment',
        'experiment': result
    })
    
    return result

@app.get("/api/incidents/stats")
async def get_incident_stats():
    """Get incident response statistics"""
    return incident_detector.get_incident_stats()

@app.get("/api/dashboard/overview")
async def get_dashboard_overview():
    """Get comprehensive dashboard data"""
    return {
        'workflows': {
            'total': len(engine.workflows),
            'active': sum(1 for w in engine.workflows.values() if w.status == 'running'),
            'completed': sum(1 for w in engine.workflows.values() if w.status == 'completed'),
            'failed': sum(1 for w in engine.workflows.values() if w.status == 'failed')
        },
        'healing': controller.get_healing_stats(),
        'chaos': chaos_framework.get_experiment_stats(),
        'incidents': incident_detector.get_incident_stats(),
        'scheduler': scheduler.get_scheduler_stats()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    try:
        await websocket.accept()
        active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(active_connections)}")
    except Exception as e:
        logger.error(f"Error accepting WebSocket connection: {e}")
        return
    
    try:
        while True:
            # Send periodic updates
            try:
                overview = await get_dashboard_overview()
                await websocket.send_json(overview)
            except Exception as e:
                # Check if it's a connection error
                error_str = str(e).lower()
                if any(term in error_str for term in ['closed', 'disconnect', 'broken', 'reset']):
                    logger.info(f"WebSocket connection closed by client: {e}")
                else:
                    logger.error(f"Error sending WebSocket update: {e}")
                break
                
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        logger.info("WebSocket task cancelled")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            if websocket in active_connections:
                active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total connections: {len(active_connections)}")
        except Exception as e:
            logger.error(f"Error cleaning up WebSocket: {e}")

async def broadcast_update(message: dict):
    """Broadcast update to all WebSocket clients"""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
