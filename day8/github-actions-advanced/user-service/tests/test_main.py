import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "user-service"
    assert data["status"] == "healthy"

def test_get_users():
    response = client.get("/users")
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 3
    assert all("id" in user for user in users)

def test_get_user():
    response = client.get("/users/1")
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == 1
    assert "name" in user

def test_create_user():
    new_user = {
        "name": "Test User",
        "email": "test@example.com",
        "role": "user"
    }
    response = client.post("/users", json=new_user)
    assert response.status_code == 200
    created_user = response.json()
    assert created_user["name"] == "Test User"
    assert created_user["active"] == True

def test_get_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    stats = response.json()
    assert "total_users" in stats
    assert "active_users" in stats
