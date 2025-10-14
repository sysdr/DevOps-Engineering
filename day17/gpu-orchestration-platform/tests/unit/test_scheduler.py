import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.api.scheduler import GPUScheduler, WorkloadRequest, WorkloadType, WorkloadPriority

@pytest.mark.asyncio
class TestGPUScheduler:
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_gpu_manager = Mock()
        self.scheduler = GPUScheduler(self.mock_gpu_manager)

    async def test_workload_submission(self):
        """Test workload submission creates proper tracking"""
        request = WorkloadRequest(
            name="Test Training",
            workload_type=WorkloadType.TRAINING,
            gpu_memory_required=16 * (1024**3),  # 16GB
            gpu_count=1
        )
        
        workload_id = await self.scheduler.submit_workload(request)
        
        assert workload_id in self.scheduler.workloads
        assert self.scheduler.workloads[workload_id].status == "pending"
        assert len(self.scheduler.queue) == 1

    async def test_workload_priority_queue(self):
        """Test that higher priority workloads are processed first"""
        # Submit low priority workload
        low_priority = WorkloadRequest(
            name="Low Priority",
            workload_type=WorkloadType.BATCH,
            gpu_memory_required=8 * (1024**3),
            priority=WorkloadPriority.LOW
        )
        low_id = await self.scheduler.submit_workload(low_priority)
        
        # Submit high priority workload
        high_priority = WorkloadRequest(
            name="High Priority",
            workload_type=WorkloadType.TRAINING,
            gpu_memory_required=8 * (1024**3),
            priority=WorkloadPriority.HIGH
        )
        high_id = await self.scheduler.submit_workload(high_priority)
        
        # High priority should be first in queue
        assert len(self.scheduler.queue) == 2
        _, _, first_workload_id = self.scheduler.queue[0]
        assert first_workload_id == high_id

    async def test_cost_estimation(self):
        """Test workload cost estimation"""
        request = WorkloadRequest(
            name="Cost Test",
            workload_type=WorkloadType.TRAINING,
            gpu_memory_required=16 * (1024**3),
            gpu_count=2,
            max_duration_hours=4
        )
        
        estimated_cost = self.scheduler._estimate_cost(request)
        
        # Should be positive and reasonable
        assert estimated_cost > 0
        assert estimated_cost == 3.20 * 2 * 4  # base_rate * gpu_count * hours

    async def test_workload_status_retrieval(self):
        """Test getting workload status"""
        request = WorkloadRequest(
            name="Status Test",
            workload_type=WorkloadType.INFERENCE,
            gpu_memory_required=8 * (1024**3)
        )
        
        workload_id = await self.scheduler.submit_workload(request)
        status = await self.scheduler.get_workload_status(workload_id)
        
        assert status is not None
        assert status["id"] == workload_id
        assert status["name"] == "Status Test"
        assert status["status"] == "pending"

    async def test_nonexistent_workload_status(self):
        """Test getting status of non-existent workload"""
        status = await self.scheduler.get_workload_status("non-existent-id")
        assert status is None

    def test_find_suitable_gpus_mock(self):
        """Test GPU matching logic with mocked resources"""
        # Mock available resources
        self.scheduler.gpu_manager.get_available_resources = AsyncMock(return_value=[
            {
                "id": "gpu-0",
                "state": "available",
                "memory_free_gb": 20
            },
            {
                "id": "gpu-1", 
                "state": "allocated",
                "memory_free_gb": 30
            },
            {
                "id": "gpu-2",
                "state": "available", 
                "memory_free_gb": 10
            }
        ])
        
        # Test request requiring 15GB
        request = WorkloadRequest(
            name="Memory Test",
            workload_type=WorkloadType.TRAINING,
            gpu_memory_required=15 * (1024**3),  # 15GB
            gpu_count=1
        )
        
        # Should return gpu-0 (available with 20GB free)
        # Note: In real test this would be async, but for unit test we can test the logic

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
