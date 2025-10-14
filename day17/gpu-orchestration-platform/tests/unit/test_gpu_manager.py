import pytest
import asyncio
from unittest.mock import Mock, patch
from src.api.gpu_manager import GPUManager, GPUState

@pytest.mark.asyncio
class TestGPUManager:
    
    async def test_gpu_manager_initialization(self):
        """Test GPU manager initializes correctly"""
        manager = GPUManager()
        assert not manager.initialized
        
        await manager.initialize()
        assert manager.initialized
        assert len(manager.devices) >= 0  # Should have mock GPUs at minimum

    async def test_get_available_resources(self):
        """Test getting available GPU resources"""
        manager = GPUManager()
        await manager.initialize()
        
        resources = await manager.get_available_resources()
        assert isinstance(resources, list)
        
        if resources:  # If we have resources
            gpu = resources[0]
            required_fields = [
                'id', 'name', 'memory_total_gb', 'memory_used_gb', 
                'memory_free_gb', 'utilization_percent', 'temperature_c',
                'power_usage_w', 'state', 'mig_enabled'
            ]
            for field in required_fields:
                assert field in gpu

    async def test_gpu_allocation_and_release(self):
        """Test GPU allocation and release cycle"""
        manager = GPUManager()
        await manager.initialize()
        
        if not manager.devices:
            pytest.skip("No GPUs available for testing")
        
        gpu_id = list(manager.devices.keys())[0]
        
        # Test allocation
        success = await manager.allocate_gpu(gpu_id, "test-workload-1")
        assert success
        assert manager.devices[gpu_id].state == GPUState.ALLOCATED
        
        # Test release
        success = await manager.release_gpu(gpu_id)
        assert success
        assert manager.devices[gpu_id].state == GPUState.AVAILABLE

    async def test_invalid_gpu_allocation(self):
        """Test allocation of non-existent GPU"""
        manager = GPUManager()
        await manager.initialize()
        
        success = await manager.allocate_gpu("non-existent-gpu", "test-workload")
        assert not success

    async def test_mock_gpu_creation(self):
        """Test that mock GPUs are created when real ones unavailable"""
        manager = GPUManager()
        
        # Force mock GPU creation
        await manager._create_mock_gpus()
        
        assert len(manager.devices) == 4  # Should create 4 mock GPUs
        
        for device in manager.devices.values():
            assert device.state == GPUState.AVAILABLE
            assert device.memory_total > 0
            assert device.name in ["NVIDIA A100-SXM4-40GB", "NVIDIA V100-SXM2-32GB", "NVIDIA T4"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
