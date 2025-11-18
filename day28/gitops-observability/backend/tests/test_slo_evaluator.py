"""Tests for SLO Evaluator"""
import pytest
from evaluators.slo_evaluator import SLOEvaluator
from models.database import Database

@pytest.fixture
def db():
    return Database()

@pytest.fixture
def evaluator(db):
    return SLOEvaluator(db)

@pytest.mark.asyncio
async def test_evaluate_all_slos(evaluator):
    slis = {
        "success_rate": {"value": 99.8},
        "sync_latency_p99": 25000,
        "reconciliation_success": {"value": 99.95}
    }
    
    evaluations = await evaluator.evaluate(slis)
    
    assert len(evaluations) == 3
    for eval in evaluations:
        assert "slo_id" in eval
        assert "is_meeting" in eval
        assert "error_budget_remaining" in eval

@pytest.mark.asyncio
async def test_error_budget_calculation(evaluator):
    slis = {"success_rate": {"value": 99.0}}
    evaluations = await evaluator.evaluate(slis)
    
    success_eval = next(e for e in evaluations if e["slo_id"] == "deployment-success-rate")
    assert success_eval["error_budget_consumed"] > 0
    assert success_eval["error_budget_remaining"] >= 0

@pytest.mark.asyncio
async def test_status_assignment(evaluator):
    slis = {"success_rate": {"value": 98.0}}
    evaluations = await evaluator.evaluate(slis)
    
    success_eval = next(e for e in evaluations if e["slo_id"] == "deployment-success-rate")
    assert success_eval["status"] in ["healthy", "warning", "critical"]

@pytest.mark.asyncio
async def test_meeting_slo(evaluator):
    slis = {
        "success_rate": {"value": 100.0},
        "sync_latency_p99": 10000,
        "reconciliation_success": {"value": 100.0}
    }
    
    evaluations = await evaluator.evaluate(slis)
    for eval in evaluations:
        assert eval["is_meeting"] == True
