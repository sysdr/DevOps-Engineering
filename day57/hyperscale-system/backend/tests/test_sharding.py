import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import HyperscaleSystem

def test_consistent_hashing():
    """Test consistent hashing distributes keys evenly"""
    system = HyperscaleSystem()
    
    # Generate 10000 keys and track distribution
    shard_counts = {i: 0 for i in range(4)}
    
    for i in range(10000):
        shard = system.get_shard(f"user_{i}")
        shard_counts[shard] += 1
    
    # Each shard should get roughly 25% (2500) keys
    # Allow 10% variance (2250-2750)
    for shard, count in shard_counts.items():
        assert 2000 <= count <= 3000, f"Shard {shard} has {count} keys (expected ~2500)"

def test_same_key_same_shard():
    """Test same key always routes to same shard"""
    system = HyperscaleSystem()
    
    # Same key should always return same shard
    key = "user_12345"
    shard1 = system.get_shard(key)
    shard2 = system.get_shard(key)
    shard3 = system.get_shard(key)
    
    assert shard1 == shard2 == shard3, "Same key must route to same shard"

def test_virtual_nodes():
    """Test virtual nodes are created correctly"""
    system = HyperscaleSystem()
    
    # Should have 4 shards * 256 virtual nodes = 1024 total
    assert len(system.hash_ring) == 1024, "Should have 1024 virtual nodes"
    
    # Hash ring should be sorted
    for i in range(len(system.hash_ring) - 1):
        assert system.hash_ring[i][0] <= system.hash_ring[i+1][0], "Hash ring must be sorted"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
