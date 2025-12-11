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

def test_get_alerts():
    response = client.get("/alerts")
    assert response.status_code == 200
    assert "alerts" in response.json()

def test_get_rules():
    response = client.get("/rules")
    assert response.status_code == 200
    assert "rules" in response.json()
