import pytest
import httpx
import asyncio
from fastapi.testclient import TestClient
from src.api.main import app

# Test client for integration tests
client = TestClient(app)

class TestAPIEndpoints:
    
    def test_dashboard_endpoint(self):
        """Test main dashboard endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "GPU Orchestration Platform" in response.text

    def test_gpu_resources_endpoint(self):
        """Test GPU resources API endpoint"""
        response = client.get("/api/gpu/resources")
        assert response.status_code == 200
        
        data = response.json()
        assert "resources" in data
        assert "timestamp" in data
        assert isinstance(data["resources"], list)

    def test_metrics_endpoint(self):
        """Test monitoring metrics endpoint"""
        response = client.get("/api/monitoring/metrics")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["timestamp", "cluster_stats", "individual_gpus", "historical_data"]
        for field in required_fields:
            assert field in data

    def test_cost_analysis_endpoint(self):
        """Test cost analysis endpoint"""
        response = client.get("/api/costs/analysis")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "current_hourly_cost", "projected_daily_cost", "projected_monthly_cost",
            "utilization_analysis", "underutilized_gpus", "optimization_recommendations"
        ]
        for field in required_fields:
            assert field in data

    def test_workload_submission(self):
        """Test workload submission endpoint"""
        workload_data = {
            "name": "Integration Test Workload",
            "workload_type": "training",
            "gpu_memory_required": 16 * (1024**3),
            "gpu_count": 1,
            "max_duration_hours": 2,
            "priority": 2,
            "framework": "pytorch"
        }
        
        response = client.post("/api/workloads/submit", json=workload_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "workload_id" in data
        assert "status" in data
        assert data["status"] == "submitted"

    def test_workload_status_retrieval(self):
        """Test workload status endpoint after submission"""
        # First submit a workload
        workload_data = {
            "name": "Status Test Workload",
            "workload_type": "inference",
            "gpu_memory_required": 8 * (1024**3),
            "gpu_count": 1
        }
        
        submit_response = client.post("/api/workloads/submit", json=workload_data)
        workload_id = submit_response.json()["workload_id"]
        
        # Then check its status
        status_response = client.get(f"/api/workloads/{workload_id}/status")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["id"] == workload_id
        assert status_data["name"] == "Status Test Workload"

    def test_invalid_workload_submission(self):
        """Test submission with invalid data"""
        invalid_workload = {
            "name": "Invalid Workload",
            # Missing required fields
        }
        
        response = client.post("/api/workloads/submit", json=invalid_workload)
        assert response.status_code == 422  # Validation error

    def test_nonexistent_workload_status(self):
        """Test status request for non-existent workload"""
        response = client.get("/api/workloads/non-existent-id/status")
        assert response.status_code == 404

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
