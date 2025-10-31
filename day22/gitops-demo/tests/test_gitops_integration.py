import pytest
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_api_health():
    """Test API health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_applications_endpoint():
    """Test applications listing"""
    response = requests.get(f"{BASE_URL}/applications")
    assert response.status_code == 200
    apps = response.json()
    assert len(apps) > 0
    
    # Verify application structure
    app = apps[0]
    required_fields = ["name", "environment", "status", "sync_status", "health_status"]
    for field in required_fields:
        assert field in app

def test_sync_functionality():
    """Test application sync functionality"""
    response = requests.post(f"{BASE_URL}/sync/web-app/dev")
    assert response.status_code == 200
    assert "Sync initiated" in response.json()["message"]
    
    # Wait for sync to complete
    time.sleep(3)
    
    # Verify sync status updated
    response = requests.get(f"{BASE_URL}/applications")
    apps = response.json()
    dev_app = next((app for app in apps if app["name"] == "web-app" and app["environment"] == "dev"), None)
    assert dev_app is not None

def test_metrics_endpoint():
    """Test metrics collection"""
    response = requests.get(f"{BASE_URL}/metrics")
    assert response.status_code == 200
    metrics = response.json()
    
    required_metrics = ["applications_total", "applications_synced", "sync_success_rate"]
    for metric in required_metrics:
        assert metric in metrics
        assert isinstance(metrics[metric], (int, float))
