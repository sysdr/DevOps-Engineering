"""Tests for SLI Calculator"""
import pytest
import asyncio
from calculators.sli_calculator import SLICalculator
from models.database import Database

@pytest.fixture
def db():
    return Database()

@pytest.fixture
def calculator(db):
    return SLICalculator(db)

@pytest.mark.asyncio
async def test_calculate_returns_all_slis(calculator):
    slis = await calculator.calculate()
    
    assert "success_rate" in slis
    assert "sync_latency" in slis
    assert "reconciliation_success" in slis
    assert "error_rate" in slis
    assert "throughput" in slis
    assert "calculated_at" in slis

@pytest.mark.asyncio
async def test_success_rate_calculation(calculator, db):
    await db.add_deployment({"app": "test", "status": "success", "duration_ms": 1000, "sync_attempts": 1, "environment": "prod"})
    await db.add_deployment({"app": "test", "status": "success", "duration_ms": 1000, "sync_attempts": 1, "environment": "prod"})
    await db.add_deployment({"app": "test", "status": "failed", "duration_ms": 1000, "sync_attempts": 2, "environment": "prod"})
    
    slis = await calculator.calculate()
    assert slis["success_rate"]["value"] > 0
    assert slis["success_rate"]["total"] > 0

@pytest.mark.asyncio
async def test_latency_percentile(calculator):
    deployments = await calculator.db.get_deployments_in_window(60)
    p99 = await calculator._calculate_latency_percentile(deployments, 99)
    p95 = await calculator._calculate_latency_percentile(deployments, 95)
    
    assert p99 >= p95

@pytest.mark.asyncio
async def test_empty_data_handling(calculator):
    calculator.db.deployments = []
    calculator.db.metrics = []
    
    slis = await calculator.calculate()
    assert slis["success_rate"]["value"] == 100.0
    assert slis["success_rate"]["total"] == 0
