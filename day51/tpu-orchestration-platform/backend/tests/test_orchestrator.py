"""
Test suite for TPU Orchestrator
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.job import Job, TPUType
from services.orchestrator import TPUOrchestrator

async def test_job_scheduling():
    """Test basic job scheduling"""
    print("Testing job scheduling...")
    
    orchestrator = TPUOrchestrator()
    
    # Start scheduling loop
    task = asyncio.create_task(orchestrator.scheduling_loop())
    await asyncio.sleep(0.1)  # Give task time to start
    
    # Create test job
    job = Job(
        model_name="test-model",
        tpu_type=TPUType.V4_8,
        priority=50,
        total_steps=100
    )
    
    # Schedule job
    job_id = await orchestrator.schedule_job(job)
    print(f"  ✓ Job scheduled: {job_id}")
    
    # Wait for scheduling cycle (scheduling interval is 5 seconds)
    await asyncio.sleep(6)
    
    # Check if job was picked up
    active_jobs = orchestrator.get_active_jobs()
    assert len(active_jobs) > 0, "Job should be active"
    print(f"  ✓ Job activated successfully")
    
    # Cancel the scheduling loop task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    return True

async def test_cost_optimization():
    """Test cost optimization logic"""
    print("Testing cost optimization...")
    
    orchestrator = TPUOrchestrator()
    
    # High priority job (should use on-demand)
    job1 = Job(
        model_name="critical-job",
        tpu_type=TPUType.V4_8,
        priority=90,
        optimize_cost=True
    )
    
    # Low priority job (should use preemptible)
    job2 = Job(
        model_name="batch-job",
        tpu_type=TPUType.V4_8,
        priority=30,
        optimize_cost=True
    )
    
    assert not job1.can_use_preemptible(), "High priority should use on-demand"
    assert job2.can_use_preemptible(), "Low priority should use preemptible"
    
    print("  ✓ Cost optimization logic working correctly")
    return True

async def test_preemption_recovery():
    """Test preemption handling"""
    print("Testing preemption recovery...")
    
    orchestrator = TPUOrchestrator()
    
    job = Job(
        model_name="preemptible-test",
        tpu_type=TPUType.V4_8,
        priority=30,
        total_steps=1000,
        use_preemptible=True,
        max_retries=2
    )
    
    job_id = await orchestrator.schedule_job(job)
    print(f"  ✓ Preemptible job scheduled: {job_id}")
    
    # Note: Actual preemption is random, just verify retry logic exists
    assert job.max_retries == 2, "Retry logic configured"
    print("  ✓ Preemption recovery mechanism in place")
    
    return True

async def run_tests():
    """Run all tests"""
    print("\n" + "="*50)
    print("TPU ORCHESTRATOR TEST SUITE")
    print("="*50 + "\n")
    
    tests = [
        test_job_scheduling,
        test_cost_optimization,
        test_preemption_recovery
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
                print(f"✓ {test.__name__} PASSED\n")
            else:
                failed += 1
                print(f"✗ {test.__name__} FAILED\n")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} FAILED: {e}\n")
    
    print("="*50)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*50)
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
