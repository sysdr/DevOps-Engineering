import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_get_data():
    response = client.get("/api/data")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Data retrieved successfully"
    assert "data" in data
    assert data["data"]["total"] == 3

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_data_structure():
    response = client.get("/api/data")
    data = response.json()["data"]
    assert len(data["items"]) == 3
    assert all("id" in item for item in data["items"])
    assert all("name" in item for item in data["items"])
    assert all("status" in item for item in data["items"])
