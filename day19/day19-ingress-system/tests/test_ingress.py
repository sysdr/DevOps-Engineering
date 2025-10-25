import pytest
import httpx
import asyncio
import time

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_health_check():
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_ssl_info():
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/api/ssl-info")
        assert response.status_code == 200
        assert "protocol" in response.json()

@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting functionality"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Make multiple requests quickly
        tasks = []
        for i in range(10):
            tasks.append(client.get(f"{BASE_URL}/api/load-test"))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should have some successful responses
        success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
        assert success_count > 0

@pytest.mark.asyncio
async def test_services_endpoint():
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/api/services")
        assert response.status_code == 200
        services = response.json()["services"]
        assert len(services) > 0
        assert all("name" in service for service in services)

@pytest.mark.asyncio
async def test_load_performance():
    """Test system performance under load"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        start_time = time.time()
        
        # Run concurrent requests
        tasks = [client.get(f"{BASE_URL}/api/load-test") for _ in range(20)]
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)
        
        # Should complete within reasonable time
        assert duration < 15.0  # 15 seconds max for 20 requests with random delays
