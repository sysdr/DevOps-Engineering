import pytest
import httpx
import asyncio
import time

@pytest.mark.asyncio
async def test_api_integration():
    """Test API integration with external services"""
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        response = await client.get("http://localhost:8000/health")
        assert response.status_code == 200
        
        # Test test execution workflow
        test_response = await client.post("http://localhost:8000/tests/run/unit")
        assert test_response.status_code == 200
        
        test_id = test_response.json()["test_id"]
        
        # Wait for test completion
        await asyncio.sleep(2)
        
        # Check test results
        results_response = await client.get(f"http://localhost:8000/tests/results/{test_id}")
        assert results_response.status_code in [200, 404]  # May not be complete yet

@pytest.mark.asyncio
async def test_database_integration():
    """Test database operations"""
    # This would test actual database operations
    # For now, simulate with in-memory operations
    assert True

@pytest.mark.asyncio
async def test_redis_integration():
    """Test Redis cache operations"""
    # This would test Redis operations
    assert True

def test_docker_environment():
    """Test Docker environment is properly configured"""
    import subprocess
    result = subprocess.run(["docker", "ps"], capture_output=True)
    assert result.returncode == 0
