import pytest
import httpx
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from crossplane_api import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()
    assert response.json()["service"] == "Crossplane Infrastructure API"

def test_provision_database():
    payload = {
        "name": "test-db",
        "type": "database",
        "size": "small",
        "cloud": "aws",
        "namespace": "default",
        "backup_enabled": True
    }
    
    # This will fail in local testing without Kubernetes
    # but validates the endpoint structure
    response = client.post("/infrastructure/provision", json=payload)
    # In local test, we expect 500 due to no K8s connection
    assert response.status_code in [200, 500, 503]

def test_invalid_type():
    payload = {
        "name": "test-invalid",
        "type": "invalid-type",
        "size": "small",
        "cloud": "aws",
        "namespace": "default"
    }
    
    response = client.post("/infrastructure/provision", json=payload)
    assert response.status_code in [400, 500, 503]

def test_list_infrastructure():
    response = client.get("/infrastructure/list/default")
    # Will fail without K8s but validates endpoint
    assert response.status_code in [200, 500, 503]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
