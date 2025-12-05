import pytest
import asyncio
import httpx

BASE_URL = "http://localhost:8005"

@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_get_slo_metrics():
    async with httpx.AsyncClient() as client:
        # Wait a bit for metrics to be calculated
        await asyncio.sleep(5)
        response = await client.get(f"{BASE_URL}/api/slo/order")
        assert response.status_code == 200
        data = response.json()
        assert "1h" in data or "slo_config" in data

@pytest.mark.asyncio
async def test_get_all_summary():
    async with httpx.AsyncClient() as client:
        await asyncio.sleep(5)
        response = await client.get(f"{BASE_URL}/api/slo/all/summary")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
