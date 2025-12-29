import pytest
import asyncio
import asyncpg
from datetime import datetime

@pytest.mark.asyncio
async def test_cost_collection():
    """Test cost collection functionality"""
    print("\n=== Testing Cost Collection ===")
    
    # Create test database connection
    conn = await asyncpg.connect(
        host="localhost",
        port=5433,
        user="postgres",
        password="postgres",
        database="mlops_costs"
    )
    
    # Insert test cost record
    await conn.execute('''
        INSERT INTO cost_records 
        (timestamp, team, project, instance_type, runtime_hours, cost)
        VALUES ($1, $2, $3, $4, $5, $6)
    ''', datetime.now(), 'test-team', 'test-project', 'g4dn.2xlarge', 1.0, 0.752)
    
    # Verify record
    record = await conn.fetchrow('''
        SELECT * FROM cost_records 
        WHERE team = 'test-team' 
        ORDER BY timestamp DESC LIMIT 1
    ''')
    
    assert record is not None
    assert record['team'] == 'test-team'
    assert record['cost'] == 0.752
    
    print("✓ Cost collection test passed")
    await conn.close()

@pytest.mark.asyncio
async def test_spot_manager():
    """Test spot instance management"""
    print("\n=== Testing Spot Instance Manager ===")
    
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from backend.services.spot_manager import SpotInstanceManager
    
    # Create mock db pool
    class MockPool:
        async def acquire(self):
            return self
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
    
    manager = SpotInstanceManager(MockPool())
    
    # Test spot pool initialization
    await manager.initialize_spot_pool("g4dn.2xlarge", 3)
    assert len(manager.spot_pool) == 3
    
    # Test allocation
    spot = await manager.allocate_spot("job-1", "g4dn.2xlarge")
    assert spot is not None
    assert spot['assigned_job'] == "job-1"
    
    # Test statistics
    stats = await manager.get_spot_statistics()
    assert stats['total'] == 3
    assert stats['allocated'] == 1
    assert stats['available'] == 2
    
    print("✓ Spot manager test passed")

@pytest.mark.asyncio
async def test_inference_optimizer():
    """Test inference optimization"""
    print("\n=== Testing Inference Optimizer ===")
    
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from backend.services.inference_optimizer import InferenceOptimizer
    
    optimizer = InferenceOptimizer()
    
    # Test optimization
    optimal = await optimizer.optimize_model("test-model", latency_sla=100.0)
    
    assert optimal is not None
    assert optimal['p99_latency_ms'] <= 100.0
    assert 'monthly_cost' in optimal
    assert optimal['monthly_cost'] > 0
    
    print(f"✓ Optimal config: {optimal['instance_type']} x{optimal['replicas']}")
    print(f"  QPS: {optimal['qps']}, Latency: {optimal['p99_latency_ms']}ms")
    print(f"  Cost: ${optimal['monthly_cost']:.2f}/month")

def run_tests():
    """Run all tests"""
    print("\n" + "="*50)
    print("Running MLOps Cost Optimizer Tests")
    print("="*50)
    
    asyncio.run(test_cost_collection())
    asyncio.run(test_spot_manager())
    asyncio.run(test_inference_optimizer())
    
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)

if __name__ == "__main__":
    run_tests()
