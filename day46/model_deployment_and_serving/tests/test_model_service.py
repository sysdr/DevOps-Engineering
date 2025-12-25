import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi.testclient import TestClient
from model_service import app, load_models

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup():
    load_models()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["models_loaded"] > 0

def test_list_models():
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert len(data["models"]) >= 2
    assert any(m["version"] == "v1" for m in data["models"])

def test_prediction():
    response = client.post(
        "/v1/models/predict",
        json={"instances": [[5.1, 3.5, 1.4, 0.2]]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert "model_version" in data
    assert "latency_ms" in data
    assert len(data["predictions"]) == 1
    assert data["predictions"][0] in [0, 1, 2]

def test_prediction_with_version():
    response = client.post(
        "/v1/models/predict",
        json={"instances": [[6.5, 3.0, 5.2, 2.0]], "version": "v2"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model_version"] == "v2"

def test_traffic_split():
    response = client.get("/v1/traffic-split")
    assert response.status_code == 200
    data = response.json()
    assert "v1" in data
    assert "v2" in data

def test_update_traffic_split():
    response = client.post(
        "/v1/traffic-split",
        json={"v1": 50, "v2": 50}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"
    assert data["traffic_split"]["v1"] == 50
    assert data["traffic_split"]["v2"] == 50

def test_model_metadata():
    response = client.get("/v1/models/v1/metadata")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "v1"
    assert "accuracy" in data
    assert "size_mb" in data

def test_compare_models():
    # Make some predictions first
    client.post("/v1/models/predict", json={"instances": [[5.1, 3.5, 1.4, 0.2]], "version": "v1"})
    client.post("/v1/models/predict", json={"instances": [[6.5, 3.0, 5.2, 2.0]], "version": "v2"})
    
    response = client.get("/v1/compare-models")
    assert response.status_code == 200
    data = response.json()
    assert "comparison" in data

def test_quantized_model():
    response = client.post(
        "/v1/models/predict",
        json={"instances": [[5.9, 3.0, 4.2, 1.5]], "version": "v2-quantized"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model_version"] == "v2-quantized"

def test_batch_prediction():
    response = client.post(
        "/v1/models/predict",
        json={
            "instances": [
                [5.1, 3.5, 1.4, 0.2],
                [6.5, 3.0, 5.2, 2.0],
                [5.9, 3.0, 4.2, 1.5]
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["predictions"]) == 3

def test_latency_tracking():
    # Make multiple predictions
    for _ in range(10):
        client.post("/v1/models/predict", json={"instances": [[5.1, 3.5, 1.4, 0.2]]})
    
    response = client.get("/v1/metrics/v1")
    assert response.status_code == 200 or response.status_code == 404  # 404 if Redis not available
