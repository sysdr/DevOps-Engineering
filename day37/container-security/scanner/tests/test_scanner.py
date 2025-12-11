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

def test_scan_image():
    response = client.post("/scan", json={"image": "nginx:latest", "policy": "default"})
    assert response.status_code == 200
    data = response.json()
    assert "scan_id" in data
    assert data["status"] in ["pending", "scanning", "completed"]

def test_list_scans():
    response = client.get("/scans")
    assert response.status_code == 200
    assert "scans" in response.json()
