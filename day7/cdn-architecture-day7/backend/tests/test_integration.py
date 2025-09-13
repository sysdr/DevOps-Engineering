import pytest
import asyncio
import aiohttp
import json
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.mark.asyncio
async def test_api_endpoints():
    """Test API endpoints are working"""
    # This would require the server to be running
    # For demo purposes, we'll test the logic directly
    from main import init_app
    
    app = await init_app()
    
    # Test that app initializes
    assert app is not None

@pytest.mark.asyncio
async def test_performance_under_load():
    """Test system performance under simulated load"""
    from main import CDNRouter
    
    router = CDNRouter()
    
    start_time = time.time()
    
    # Simulate 100 concurrent requests
    tasks = []
    for i in range(100):
        task = router.handle_request(
            f"resource_{i % 10}.html", 
            40.7128 + (i % 10) * 0.1, 
            -74.0060 + (i % 10) * 0.1, 
            f"192.168.1.{i % 255}"
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    
    # All requests should succeed
    assert len(results) == 100
    assert all(result["status"] == "success" for result in results)
    
    # Should complete within reasonable time
    assert end_time - start_time < 5.0  # 5 seconds max

@pytest.mark.asyncio
async def test_cost_optimization():
    """Test cost optimization features"""
    from main import CDNRouter
    
    router = CDNRouter()
    
    # Make requests and check cost metrics
    await router.handle_request("test.html", 40.7128, -74.0060, "192.168.1.1")
    await router.handle_request("test.html", 40.7128, -74.0060, "192.168.1.1")  # Should hit cache
    
    # Cache hit should reduce cost
    assert router.cost_metrics["cache_hits"] > 0
    assert router.cost_metrics["requests"] >= 2

if __name__ == "__main__":
    pytest.main([__file__])
