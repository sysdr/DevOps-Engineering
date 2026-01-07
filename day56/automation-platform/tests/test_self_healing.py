import pytest
import asyncio
from backend.self_healing.controller import SelfHealingController

@pytest.mark.asyncio
async def test_resource_registration():
    controller = SelfHealingController()
    
    controller.register_resource("pod", "test-pod-1")
    assert "test-pod-1" in controller.resources
    assert controller.resources["test-pod-1"].healthy == True

@pytest.mark.asyncio
async def test_healing_action():
    controller = SelfHealingController()
    controller.register_resource("pod", "test-pod-1")
    
    # Simulate unhealthy state
    controller.resources["test-pod-1"].healthy = False
    
    # Trigger healing
    await controller._heal_resource(controller.resources["test-pod-1"])
    
    # Should be healthy again
    assert controller.resources["test-pod-1"].healthy == True
    assert len(controller.healing_actions) > 0
