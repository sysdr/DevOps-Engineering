import pytest
import time
import requests
import subprocess
import signal
import os

class TestIntegration:
    @classmethod
    def setup_class(cls):
        # Start the application
        cls.backend_process = subprocess.Popen(
            ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)  # Wait for server to start

    @classmethod
    def teardown_class(cls):
        cls.backend_process.terminate()
        cls.backend_process.wait()

    def test_full_build_lifecycle(self):
        base_url = "http://localhost:8000"
        
        # Start a build
        start_response = requests.post(f"{base_url}/api/builds/start", json={
            "build_id": "integration-test-1",
            "pipeline_name": "integration-pipeline"
        })
        assert start_response.status_code == 200
        
        # Check active builds
        active_response = requests.get(f"{base_url}/api/builds/active")
        assert active_response.status_code == 200
        active_data = active_response.json()
        assert "integration-test-1" in active_data["active_builds"]
        
        # Simulate some time passing
        time.sleep(2)
        
        # Finish the build
        finish_response = requests.post(f"{base_url}/api/builds/integration-test-1/finish", json={
            "success": True
        })
        assert finish_response.status_code == 200
        
        # Check metrics summary
        summary_response = requests.get(f"{base_url}/api/metrics/summary")
        assert summary_response.status_code == 200
        
        # Check trends
        trends_response = requests.get(f"{base_url}/api/metrics/trends")
        assert trends_response.status_code == 200

    def test_api_health(self):
        response = requests.get("http://localhost:8000/")
        assert response.status_code == 200
        assert response.json()["status"] == "running"
