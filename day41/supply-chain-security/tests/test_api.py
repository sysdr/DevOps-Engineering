"""Test suite for Supply Chain Security API"""
import pytest
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_artifact():
    """Test artifact creation"""
    artifact = {
        "id": "test-artifact-1",
        "name": "test-app",
        "version": "1.0.0",
        "type": "container",
        "created_at": "2024-01-01T00:00:00Z"
    }
    response = client.post("/api/artifacts", json=artifact)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_list_artifacts():
    """Test listing artifacts"""
    response = client.get("/api/artifacts")
    assert response.status_code == 200
    assert "artifacts" in response.json()

def test_generate_sbom():
    """Test SBOM generation"""
    # First create artifact
    artifact = {
        "id": "test-artifact-2",
        "name": "test-app",
        "version": "1.0.0",
        "type": "container",
        "created_at": "2024-01-01T00:00:00Z"
    }
    client.post("/api/artifacts", json=artifact)
    
    # Generate SBOM
    sbom_request = {
        "artifact_id": "test-artifact-2",
        "image_name": "test-app:latest",
        "format": "cyclonedx"
    }
    response = client.post("/api/sbom/generate", json=sbom_request)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "component_count" in response.json()

def test_sign_artifact():
    """Test artifact signing"""
    # Create artifact
    artifact = {
        "id": "test-artifact-3",
        "name": "test-app",
        "version": "1.0.0",
        "type": "container",
        "created_at": "2024-01-01T00:00:00Z"
    }
    client.post("/api/artifacts", json=artifact)
    
    # Sign artifact
    sign_request = {
        "artifact_id": "test-artifact-3",
        "signer": "test@example.com"
    }
    response = client.post("/api/sign", json=sign_request)
    assert response.status_code == 200
    assert "signature" in response.json()

def test_verify_signature():
    """Test signature verification"""
    # Create and sign artifact
    artifact = {
        "id": "test-artifact-4",
        "name": "test-app",
        "version": "1.0.0",
        "type": "container",
        "created_at": "2024-01-01T00:00:00Z"
    }
    client.post("/api/artifacts", json=artifact)
    
    sign_request = {
        "artifact_id": "test-artifact-4",
        "signer": "test@example.com"
    }
    client.post("/api/sign", json=sign_request)
    
    # Verify signature
    verify_request = {
        "artifact_id": "test-artifact-4"
    }
    response = client.post("/api/verify", json=verify_request)
    assert response.status_code == 200
    assert response.json()["verified"] == True

def test_scan_vulnerabilities():
    """Test vulnerability scanning"""
    # Create artifact
    artifact = {
        "id": "test-artifact-5",
        "name": "test-app",
        "version": "1.0.0",
        "type": "container",
        "created_at": "2024-01-01T00:00:00Z"
    }
    client.post("/api/artifacts", json=artifact)
    
    # Scan vulnerabilities
    scan_request = {
        "artifact_id": "test-artifact-5"
    }
    response = client.post("/api/scan/vulnerabilities", json=scan_request)
    assert response.status_code == 200
    assert "vulnerabilities" in response.json()
    assert "summary" in response.json()

def test_dashboard_stats():
    """Test dashboard statistics"""
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    assert "artifacts" in response.json()
    assert "vulnerabilities" in response.json()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
