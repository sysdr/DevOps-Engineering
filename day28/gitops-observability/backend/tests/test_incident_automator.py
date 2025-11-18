"""Tests for Incident Automator"""
import pytest
from automators.incident_automator import IncidentAutomator
from models.database import Database

@pytest.fixture
def db():
    return Database()

@pytest.fixture
def automator(db):
    return IncidentAutomator(db)

@pytest.mark.asyncio
async def test_critical_incident_creation(automator):
    evaluations = [{
        "slo_id": "test-slo",
        "slo_name": "Test SLO",
        "status": "critical",
        "current": 95.0,
        "target": 99.5,
        "error_budget_percent": 5.0
    }]
    
    await automator.process(evaluations)
    incidents = await automator.db.get_active_incidents()
    
    critical_incidents = [i for i in incidents if i.get("severity") == "critical"]
    assert len(critical_incidents) > 0

@pytest.mark.asyncio
async def test_cooldown_prevents_duplicate_incidents(automator):
    evaluations = [{
        "slo_id": "cooldown-test",
        "slo_name": "Cooldown Test",
        "status": "critical",
        "current": 95.0,
        "target": 99.5,
        "error_budget_percent": 5.0
    }]
    
    await automator.process(evaluations)
    initial_count = len(await automator.db.get_active_incidents())
    
    await automator.process(evaluations)
    final_count = len(await automator.db.get_active_incidents())
    
    assert final_count == initial_count

@pytest.mark.asyncio
async def test_runbook_actions(automator):
    evaluation = {
        "slo_id": "deployment-success-rate",
        "error_budget_percent": 5.0
    }
    
    actions = await automator._execute_runbook(evaluation)
    assert "deployments_paused" in actions
    assert "oncall_paged" in actions
