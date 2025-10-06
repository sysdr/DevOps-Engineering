import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Git Workflows Manager API"

def test_workflow_status():
    response = client.get("/api/workflow/status")
    assert response.status_code == 200
    data = response.json()
    assert "branches" in data
    assert "merge_queue_size" in data

def test_branch_protection():
    response = client.post("/api/workflow/branch-protection", json={
        "branch": "main",
        "require_reviews": 2
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_merge_queue():
    response = client.post("/api/workflow/merge-queue", json={
        "branch": "feature/test",
        "author": "test@example.com"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_analytics():
    response = client.get("/api/workflow/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "merge_queue" in data
    assert "branch_protection" in data
