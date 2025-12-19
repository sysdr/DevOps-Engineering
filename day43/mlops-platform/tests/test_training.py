import pytest
import httpx
import asyncio
import time

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_submit_training_job():
    async with httpx.AsyncClient(timeout=60.0) as client:
        request = {
            "experiment_name": "test_experiment",
            "model_type": "random_forest",
            "hyperparameters": {
                "n_estimators": 10,
                "max_depth": 5,
                "random_state": 42
            },
            "dataset_config": {
                "n_samples": 100,
                "n_features": 10
            },
            "tags": {"test": "true"}
        }
        
        response = await client.post(f"{BASE_URL}/train", json=request)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "submitted"
        
        # Wait for job completion
        job_id = data["job_id"]
        for _ in range(30):
            response = await client.get(f"{BASE_URL}/jobs/{job_id}")
            job_data = response.json()
            if job_data["status"] == "completed":
                assert "metrics" in job_data
                assert "accuracy" in job_data["metrics"]
                break
            await asyncio.sleep(2)

@pytest.mark.asyncio
async def test_list_jobs():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/jobs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
