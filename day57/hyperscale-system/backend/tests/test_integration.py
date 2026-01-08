import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import HyperscaleSystem

@pytest.mark.asyncio
async def test_end_to_end_request():
    """Test complete request flow through system"""
    system = HyperscaleSystem()
    
    # Simulate request for user
    user_id = "user_test_123"
    
    # Get shard for user
    shard_id = system.get_shard(user_id)
    assert 0 <= shard_id < 4, "Shard ID should be valid"
    
    # Route request geographically
    user_location = (40.7, -74.0)  # New York
    region = system.route_request(user_location)
    assert region in system.regions, "Should route to valid region"
    
    # Check cache
    cache_key = f"user:{user_id}:bucket:0"
    cached = system.check_cache(cache_key)
    assert cached is None, "First request should miss cache"
    
    # Set cache
    data = {"user_id": user_id, "data": "test"}
    system.set_cache(cache_key, data)
    
    # Verify cache hit
    cached = system.check_cache(cache_key)
    assert cached is not None, "Second request should hit cache"
    assert cached["user_id"] == user_id

@pytest.mark.asyncio
async def test_cache_tiering():
    """Test multi-tier cache behavior"""
    system = HyperscaleSystem()
    
    # Add entries at different times
    import time
    
    # L1 entry (recent)
    system.cache_data["key1"] = {"data": "value1", "timestamp": time.time()}
    
    # L2 entry (5 minutes ago)
    system.cache_data["key2"] = {"data": "value2", "timestamp": time.time() - 100}
    
    # L3 entry (20 minutes ago)
    system.cache_data["key3"] = {"data": "value3", "timestamp": time.time() - 1200}
    
    # Check each tier
    result1 = system.check_cache("key1")
    assert result1 is not None, "L1 cache should hit"
    assert system.cache_stats["l1_hits"] > 0
    
    result2 = system.check_cache("key2")
    assert result2 is not None, "L2 cache should hit"
    assert system.cache_stats["l2_hits"] > 0
    
    result3 = system.check_cache("key3")
    assert result3 is not None, "L3 cache should hit"
    assert system.cache_stats["l3_hits"] > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
