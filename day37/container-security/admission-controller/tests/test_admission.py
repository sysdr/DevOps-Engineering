import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_validate_admission():
    admission_request = {
        "request": {
            "uid": "test-uid-123",
            "object": {
                "metadata": {"name": "test-pod", "namespace": "default"},
                "spec": {
                    "containers": [{
                        "name": "test",
                        "image": "docker.io/nginx:latest",
                        "securityContext": {"runAsNonRoot": True},
                        "resources": {"limits": {"cpu": "100m", "memory": "128Mi"}}
                    }]
                }
            },
            "namespace": "default"
        }
    }
    
    response = client.post("/validate", json=admission_request)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
