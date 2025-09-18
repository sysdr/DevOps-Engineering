import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_images():
    response = client.get("/api/images")
    assert response.status_code == 200
    assert "images" in response.json()

def test_sign_image():
    response = client.post("/api/sign", 
                          json={"image": "nginx", "tag": "latest"})
    assert response.status_code == 200
    assert "signature" in response.json()

def test_security_metrics():
    response = client.get("/api/security-metrics")
    assert response.status_code == 200
    assert "compliance_score" in response.json()
