"""
Comprehensive tests for WASM Edge Computing Platform
"""
import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

class TestEdgeComputing:
    """Test edge computing functionality"""
    
    def test_platform_status(self):
        """Test platform status endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "platform" in data
        assert data["platform"] == "WASM Edge Computing"
        assert "version" in data
        assert "edge_locations" in data
    
    def test_edge_status(self):
        """Test edge status endpoint"""
        response = client.get("/edge/status")
        assert response.status_code == 200
        data = response.json()
        assert "edge_locations" in data
        assert "pending_syncs" in data
        assert "total_computations" in data
        assert "wasm_runtime_active" in data
    
    def test_compute_addition(self):
        """Test edge computation - addition"""
        payload = {
            "operation": "add",
            "values": [1, 2, 3, 4, 5],
            "edge_location": "test-edge"
        }
        response = client.post("/compute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 15
        assert "execution_time_ms" in data
        assert data["edge_location"] == "test-edge"
    
    def test_compute_multiplication(self):
        """Test edge computation - multiplication"""
        payload = {
            "operation": "multiply",
            "values": [2, 3, 4],
            "edge_location": "test-edge"
        }
        response = client.post("/compute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 24
    
    def test_compute_average(self):
        """Test edge computation - average"""
        payload = {
            "operation": "average",
            "values": [10, 20, 30],
            "edge_location": "test-edge"
        }
        response = client.post("/compute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 20
    
    def test_invalid_operation(self):
        """Test invalid operation handling"""
        payload = {
            "operation": "invalid",
            "values": [1, 2, 3],
            "edge_location": "test-edge"
        }
        response = client.post("/compute", json=payload)
        assert response.status_code == 500
    
    def test_edge_sync(self):
        """Test edge data synchronization"""
        payload = {
            "edge_id": "test-edge-001",
            "data": {"sensor_reading": 42.5, "timestamp": time.time()},
            "timestamp": time.time()
        }
        response = client.post("/sync", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["edge_id"] == "test-edge-001"
    
    def test_performance_benchmark(self):
        """Test performance benchmark"""
        response = client.get("/performance/benchmark")
        assert response.status_code == 200
        data = response.json()
        assert "benchmark_results" in data
        
        results = data["benchmark_results"]
        assert "add" in results
        assert "multiply" in results
        assert "average" in results
        
        for op_name, metrics in results.items():
            assert "wasm_time_ms" in metrics
            assert "python_time_ms" in metrics
            assert "speedup" in metrics
            assert "result_match" in metrics
            assert metrics["result_match"] is True
    
    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "wasm_requests_total" in response.text

class TestPerformance:
    """Test performance characteristics"""
    
    def test_compute_latency(self):
        """Test that compute operations are fast"""
        payload = {
            "operation": "add",
            "values": list(range(100)),
            "edge_location": "perf-test"
        }
        
        start_time = time.time()
        response = client.post("/compute", json=payload)
        end_time = time.time()
        
        assert response.status_code == 200
        latency = (end_time - start_time) * 1000  # Convert to ms
        
        # Should complete in under 100ms for edge computing
        assert latency < 100, f"Latency {latency}ms exceeds 100ms threshold"
    
    def test_concurrent_requests(self):
        """Test handling multiple concurrent requests"""
        import concurrent.futures
        import threading
        
        def make_request():
            payload = {
                "operation": "multiply",
                "values": [1, 2, 3],
                "edge_location": f"concurrent-{threading.current_thread().ident}"
            }
            response = client.post("/compute", json=payload)
            return response.status_code == 200
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(results), "Some concurrent requests failed"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
