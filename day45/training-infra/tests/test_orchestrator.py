import pytest
import asyncio
from src.orchestrator import TrainingOrchestrator, JobStatus

@pytest.mark.asyncio
async def test_job_submission():
    """Test job submission and queuing"""
    orchestrator = TrainingOrchestrator()
    
    config = {
        'model_type': 'resnet18',
        'epochs': 5,
        'num_gpus': 1
    }
    
    job = orchestrator.submit_job(config)
    
    assert job.job_id is not None
    assert job.status == JobStatus.QUEUED
    assert job.epochs == 5
    assert len(orchestrator.queue) == 1

@pytest.mark.asyncio
async def test_resource_allocation():
    """Test GPU allocation"""
    orchestrator = TrainingOrchestrator()
    
    # Should allocate successfully
    assert orchestrator.can_allocate(2) is True
    assert orchestrator.allocate_gpus('job1', 2) is True
    
    # Should fail - not enough GPUs
    assert orchestrator.can_allocate(3) is False
    
    # Release and reallocate
    orchestrator.release_gpus('job1')
    assert orchestrator.can_allocate(4) is True

@pytest.mark.asyncio
async def test_job_lifecycle():
    """Test complete job lifecycle"""
    orchestrator = TrainingOrchestrator()
    
    config = {'model_type': 'simple', 'epochs': 3, 'num_gpus': 1}
    job = orchestrator.submit_job(config)
    
    # Start scheduler
    scheduler_task = asyncio.create_task(orchestrator.schedule_jobs())
    
    # Wait for job to complete
    await asyncio.sleep(5)
    
    job = orchestrator.jobs[job.job_id]
    assert job.status in [JobStatus.TRAINING, JobStatus.SUCCESS]
    
    scheduler_task.cancel()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
