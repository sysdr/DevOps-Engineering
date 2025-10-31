import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "GitOps Demo API"

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_applications():
    response = client.get("/applications")
    assert response.status_code == 200
    apps = response.json()
    assert len(apps) > 0
    assert all("name" in app for app in apps)

def test_sync_application():
    response = client.post("/sync/web-app/dev")
    assert response.status_code == 200
    assert "Sync initiated" in response.json()["message"]

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert "applications_total" in metrics
    assert "sync_success_rate" in metrics
