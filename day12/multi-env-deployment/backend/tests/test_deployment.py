import pytest
import asyncio
from src.deployment.pipeline import DeploymentPipeline
from src.deployment.blue_green import BlueGreenDeployer
from src.deployment.canary import CanaryDeployer

@pytest.mark.asyncio
async def test_deployment_pipeline():
    pipeline = DeploymentPipeline()
    
    deployment_id = await pipeline.start_deployment(
        environment="staging",
        version="1.2.4",
        strategy="blue-green"
    )
    
    assert deployment_id is not None
    
    # Wait for pipeline to complete
    await asyncio.sleep(3)
    
    deployment = await pipeline.get_deployment_status(deployment_id)
    assert deployment["status"] in ["success", "running"]

@pytest.mark.asyncio
async def test_blue_green_deployment():
    deployer = BlueGreenDeployer()
    initial_status = deployer.get_environment_status()
    
    await deployer.execute_deployment("test-deployment-123")
    
    final_status = deployer.get_environment_status()
    
    # Verify traffic switched
    active_envs = [env for env, status in final_status.items() if status["status"] == "active"]
    assert len(active_envs) == 1

@pytest.mark.asyncio
async def test_canary_deployment():
    deployer = CanaryDeployer()
    
    # Start canary deployment in background
    task = asyncio.create_task(deployer.execute_canary_deployment("canary-test-123"))
    
    # Let it run for a few stages
    await asyncio.sleep(5)
    
    status = deployer.get_canary_status()
    assert status["status"] in ["in_progress", "completed"]
    
    # Cancel the task to avoid waiting for full completion
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
