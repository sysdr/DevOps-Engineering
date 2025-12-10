import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_login_success():
    response = client.post("/auth/login", json={
        "username": "alice@company.com",
        "password": "alice123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert data["user_info"]["username"] == "alice@company.com"

def test_login_failure():
    response = client.post("/auth/login", json={
        "username": "alice@company.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_token_validation():
    # First login
    login_response = client.post("/auth/login", json={
        "username": "bob@company.com",
        "password": "bob123"
    })
    token = login_response.json()["access_token"]
    
    # Validate token
    response = client.post(
        "/auth/validate",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] == True
    assert data["claims"]["sub"] == "bob@company.com"

def test_list_users():
    response = client.get("/auth/users")
    assert response.status_code == 200
    users = response.json()["users"]
    assert len(users) == 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
