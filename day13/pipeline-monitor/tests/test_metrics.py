import pytest
import asyncio
from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Pipeline Performance Monitor API"

def test_start_build():
    response = client.post("/api/builds/start", json={
        "build_id": "test-build-123",
        "pipeline_name": "test-pipeline"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["build_id"] == "test-build-123"
    assert data["status"] == "started"

def test_finish_build():
    # Start build first
    start_response = client.post("/api/builds/start", json={
        "build_id": "test-build-456",
        "pipeline_name": "test-pipeline"
    })
    
    # Finish build
    finish_response = client.post("/api/builds/test-build-456/finish", json={
        "success": True
    })
    assert finish_response.status_code == 200
    data = finish_response.json()
    assert data["build_id"] == "test-build-456"
    assert data["status"] == "finished"

def test_get_metrics_summary():
    response = client.get("/api/metrics/summary")
    assert response.status_code == 200
    # Should return either summary data or no builds message

def test_get_active_builds():
    response = client.get("/api/builds/active")
    assert response.status_code == 200
    data = response.json()
    assert "active_builds" in data
    assert "count" in data
