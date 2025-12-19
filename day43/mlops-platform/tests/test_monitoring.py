import pytest
import httpx

BASE_URL = "http://localhost:8002"

@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_set_baseline():
    async with httpx.AsyncClient() as client:
        features = [[float(x) for x in range(20)] for _ in range(100)]
        response = await client.post(
            f"{BASE_URL}/baseline/test_model",
            json=features
        )
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_drift_check():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/drift/test_model")
        assert response.status_code == 200
        data = response.json()
        assert "drift_score" in data
        assert "drift_detected" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
