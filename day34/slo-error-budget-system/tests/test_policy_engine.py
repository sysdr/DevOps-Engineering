import pytest
import httpx

BASE_URL = "http://localhost:8006"

@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_get_all_policies():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/policy/all/status")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_check_deployment():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/deployment/check/order")
        assert response.status_code == 200
        data = response.json()
        assert "allowed" in data
