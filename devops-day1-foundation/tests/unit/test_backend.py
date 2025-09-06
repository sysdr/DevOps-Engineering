import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"

def test_system_metrics():
    """Test system metrics endpoint"""
    response = client.get("/api/system/metrics")
    assert response.status_code == 200
    
    data = response.json()
    assert "timestamp" in data
    assert "cpu" in data
    assert "memory" in data
    assert "disk" in data
    assert "network" in data
    
    # Validate CPU data
    assert "usage_percent" in data["cpu"]
    assert "count" in data["cpu"]
    assert isinstance(data["cpu"]["usage_percent"], (int, float))
    assert isinstance(data["cpu"]["count"], int)

def test_aws_costs():
    """Test AWS costs endpoint"""
    response = client.get("/api/aws/costs")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_cost" in data
    assert "services" in data
    assert "cost_by_team" in data
    assert isinstance(data["total_cost"], (int, float))

def test_infrastructure_status():
    """Test infrastructure status endpoint"""
    response = client.get("/api/infrastructure/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "vpc" in data
    assert "ec2_instances" in data
    assert "load_balancers" in data
    assert "security_compliance" in data

def test_performance_tuning():
    """Test performance tuning endpoint"""
    response = client.get("/api/performance/tuning")
    assert response.status_code == 200
    
    data = response.json()
    assert "kernel_parameters" in data
    assert "processes" in data
    assert "optimization_score" in data
    assert isinstance(data["optimization_score"], (int, float))

if __name__ == "__main__":
    pytest.main([__file__])
