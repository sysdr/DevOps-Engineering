import pytest
import requests
import time
import subprocess
import os

BASE_URL = "http://localhost:8000"

def test_api_health():
    """Test API health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "OpenTofu Infrastructure Manager" in data["message"]
        print("✅ API health check passed")
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        raise

def test_infrastructure_status():
    """Test infrastructure status endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/infrastructure/status")
        assert response.status_code == 200
        data = response.json()
        assert "environments" in data
        assert "total_environments" in data
        print("✅ Infrastructure status endpoint working")
    except Exception as e:
        print(f"❌ Infrastructure status test failed: {e}")
        raise

def test_environment_state():
    """Test environment state endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/infrastructure/dev/state")
        assert response.status_code == 200
        data = response.json()
        assert "environment" in data
        assert data["environment"] == "dev"
        print("✅ Environment state endpoint working")
    except Exception as e:
        print(f"❌ Environment state test failed: {e}")
        raise

def test_drift_detection():
    """Test drift detection endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/drift-detection/dev")
        assert response.status_code == 200
        data = response.json()
        assert "environment" in data
        assert "drift_detected" in data
        print("✅ Drift detection endpoint working")
    except Exception as e:
        print(f"❌ Drift detection test failed: {e}")
        raise

def test_deployment_endpoint():
    """Test deployment endpoint"""
    try:
        payload = {
            "environment": "dev",
            "action": "plan",
            "auto_approve": False
        }
        response = requests.post(f"{BASE_URL}/api/infrastructure/deploy", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print("✅ Deployment endpoint working")
    except Exception as e:
        print(f"❌ Deployment endpoint test failed: {e}")
        raise

def test_modules_endpoint():
    """Test modules listing endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/modules")
        assert response.status_code == 200
        data = response.json()
        assert "modules" in data
        assert len(data["modules"]) > 0
        print("✅ Modules endpoint working")
    except Exception as e:
        print(f"❌ Modules endpoint test failed: {e}")
        raise

if __name__ == "__main__":
    print("🧪 Running API tests...")
    test_api_health()
    test_infrastructure_status()
    test_environment_state()
    test_drift_detection()
    test_deployment_endpoint()
    test_modules_endpoint()
    print("🎉 All API tests passed!")
