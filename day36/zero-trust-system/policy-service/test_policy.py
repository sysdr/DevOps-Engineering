import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_policy_evaluation_allow():
    response = client.post("/policy/evaluate", json={
        "user": {
            "sub": "alice@company.com",
            "groups": ["developers"]
        },
        "resource": "api/data/dev",
        "action": "GET",
        "namespace": "dev"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] == True

def test_policy_evaluation_deny():
    response = client.post("/policy/evaluate", json={
        "user": {
            "sub": "alice@company.com",
            "groups": ["developers"]
        },
        "resource": "api/data/sensitive",
        "action": "DELETE",
        "namespace": "prod"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] == False

def test_network_policy_check():
    response = client.post("/policy/network/check", json={
        "from_service": "frontend",
        "to_service": "api-gateway",
        "port": 8080
    })
    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] == True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
