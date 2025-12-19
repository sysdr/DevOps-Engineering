import pytest
import httpx
import numpy as np

BASE_URL = "http://localhost:8001"

@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_list_models():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/models")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
