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

def test_get_latest_benchmark():
    response = client.get("/benchmark/latest")
    assert response.status_code == 200
    data = response.json()
    assert "score" in data

def test_run_benchmark():
    response = client.post("/benchmark/run")
    assert response.status_code == 200
    assert "benchmark_id" in response.json()
