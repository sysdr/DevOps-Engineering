import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Testing Automation System API" in response.json()["message"]

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_run_unit_tests():
    response = client.post("/tests/run/unit")
    assert response.status_code == 200
    assert response.json()["test_type"] == "unit"
    assert response.json()["status"] == "started"

def test_run_invalid_test_type():
    response = client.post("/tests/run/invalid")
    assert response.status_code == 400

def test_get_quality_gates():
    response = client.get("/quality/gates")
    assert response.status_code == 200
    assert "gates" in response.json()

def test_inject_chaos():
    response = client.post("/chaos/inject/latency?duration=10")
    assert response.status_code == 200
    assert response.json()["fault_type"] == "latency"

@pytest.mark.asyncio
async def test_dashboard_metrics():
    response = client.get("/metrics/dashboard")
    assert response.status_code == 200
    assert "metrics" in response.json()
    assert "recent_results" in response.json()
    assert "quality_gates" in response.json()
