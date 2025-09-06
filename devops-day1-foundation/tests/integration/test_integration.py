import pytest
import requests
import time
from concurrent.futures import ThreadPoolExecutor
import asyncio

BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="module")
def backend_url():
    """Backend URL fixture"""
    return BASE_URL

def test_backend_startup(backend_url):
    """Test that backend starts up correctly"""
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{backend_url}/health")
            if response.status_code == 200:
                return
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    
    pytest.fail("Backend failed to start within 30 seconds")

def test_api_endpoints_response_time(backend_url):
    """Test that all API endpoints respond within acceptable time"""
    endpoints = [
        "/api/system/metrics",
        "/api/aws/costs",
        "/api/infrastructure/status",
        "/api/performance/tuning"
    ]
    
    for endpoint in endpoints:
        start_time = time.time()
        response = requests.get(f"{backend_url}{endpoint}")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Should respond within 2 seconds

def test_concurrent_requests(backend_url):
    """Test handling of concurrent requests"""
    def make_request():
        response = requests.get(f"{backend_url}/api/system/metrics")
        return response.status_code == 200
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        results = [future.result() for future in futures]
    
    assert all(results), "Some requests failed under concurrent load"

def test_data_consistency(backend_url):
    """Test that data returned is consistent and valid"""
    # Make multiple requests to ensure data consistency
    responses = []
    for _ in range(5):
        response = requests.get(f"{backend_url}/api/system/metrics")
        responses.append(response.json())
        time.sleep(1)
    
    # Check that CPU count remains consistent
    cpu_counts = [r["cpu"]["count"] for r in responses]
    assert len(set(cpu_counts)) == 1, "CPU count should be consistent"
    
    # Check that memory total remains consistent
    memory_totals = [r["memory"]["total"] for r in responses]
    assert len(set(memory_totals)) == 1, "Memory total should be consistent"

if __name__ == "__main__":
    pytest.main([__file__])
