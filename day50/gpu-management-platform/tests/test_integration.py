import pytest
import httpx
import asyncio
import time

BASE_URL = "http://localhost"
MIG_URL = f"{BASE_URL}:8001"
SCHEDULER_URL = f"{BASE_URL}:8002"
COST_URL = f"{BASE_URL}:8003"

@pytest.mark.asyncio
async def test_mig_controller_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MIG_URL}/health", timeout=5.0)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_list_gpus():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MIG_URL}/gpus", timeout=5.0)
        assert response.status_code == 200
        gpus = response.json()
        assert len(gpus) == 4

@pytest.mark.asyncio
async def test_enable_mig():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MIG_URL}/gpu/0/mig/enable", timeout=5.0)
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_configure_mig():
    async with httpx.AsyncClient() as client:
        # First enable MIG
        await client.post(f"{MIG_URL}/gpu/0/mig/enable", timeout=5.0)
        
        # Configure MIG instances
        config = {
            "gpu_id": 0,
            "profiles": [
                {"profile": "1g.5gb", "instances": 3},
                {"profile": "2g.10gb", "instances": 2}
            ]
        }
        response = await client.post(f"{MIG_URL}/gpu/0/mig/configure", json=config, timeout=5.0)
        assert response.status_code == 200
        result = response.json()
        assert len(result["instances"]) == 5

@pytest.mark.asyncio
async def test_scheduler_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SCHEDULER_URL}/health", timeout=5.0)
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_schedule_job():
    async with httpx.AsyncClient() as client:
        # Setup: Enable MIG on GPU 0
        await client.post(f"{MIG_URL}/gpu/0/mig/enable", timeout=5.0)
        config = {
            "gpu_id": 0,
            "profiles": [{"profile": "1g.5gb", "instances": 4}]
        }
        await client.post(f"{MIG_URL}/gpu/0/mig/configure", json=config, timeout=5.0)
        
        # Schedule a small job
        job = {
            "job_id": "test-job-1",
            "memory_required": 4096,
            "can_use_spot": False
        }
        response = await client.post(f"{SCHEDULER_URL}/schedule", json=job, timeout=5.0)
        assert response.status_code == 200
        decision = response.json()
        assert decision["node_type"] == "mig"

@pytest.mark.asyncio
async def test_cost_analytics():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{COST_URL}/analytics", timeout=5.0)
        assert response.status_code == 200
        analytics = response.json()
        assert "total_cost_current" in analytics
        assert "recommendations" in analytics

@pytest.mark.asyncio
async def test_cluster_state():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SCHEDULER_URL}/cluster/state", timeout=5.0)
        assert response.status_code == 200
        state = response.json()
        assert state["total_gpus"] > 0

def test_all_services_running():
    """Verify all services are reachable"""
    services = [
        ("MIG Controller", f"{MIG_URL}/health"),
        ("GPU Scheduler", f"{SCHEDULER_URL}/health"),
        ("Cost Optimizer", f"{COST_URL}/health")
    ]
    
    for name, url in services:
        try:
            response = httpx.get(url, timeout=5.0)
            assert response.status_code == 200, f"{name} not healthy"
            print(f"✓ {name} is running")
        except Exception as e:
            pytest.fail(f"{name} not reachable: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
