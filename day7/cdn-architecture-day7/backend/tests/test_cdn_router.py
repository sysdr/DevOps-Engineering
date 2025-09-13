import pytest
import asyncio
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import CDNRouter, EdgeNode

@pytest.mark.asyncio
async def test_cdn_router_initialization():
    """Test CDN router initializes correctly"""
    router = CDNRouter()
    
    assert len(router.edge_nodes) == 5
    assert "us-east" in router.edge_nodes
    assert "eu-west" in router.edge_nodes
    
    # Check edge nodes have proper structure
    us_east = router.edge_nodes["us-east"]
    assert us_east.region == "US East"
    assert us_east.capacity == 1000
    assert us_east.status == "healthy"

@pytest.mark.asyncio
async def test_optimal_edge_selection():
    """Test geographic routing selects optimal edge"""
    router = CDNRouter()
    
    # Test US East coast request
    edge = router.find_optimal_edge(40.7128, -74.0060)  # NYC coordinates
    assert edge.id == "us-east"
    
    # Test London request
    edge = router.find_optimal_edge(51.5074, -0.1278)  # London coordinates
    assert edge.id == "eu-west"

@pytest.mark.asyncio
async def test_cache_hit_miss():
    """Test cache hit and miss behavior"""
    router = CDNRouter()
    
    # First request should populate cache
    result1 = await router.handle_request("test.html", 40.7128, -74.0060, "192.168.1.1")
    
    # Second request to same resource should hit cache
    result2 = await router.handle_request("test.html", 40.7128, -74.0060, "192.168.1.1")
    
    assert result1["status"] == "success"
    assert result2["status"] == "success"
    assert result2["cache_hit"] == True

@pytest.mark.asyncio
async def test_failover_mechanism():
    """Test automatic failover when nodes fail"""
    router = CDNRouter()
    
    # Simulate node failure
    router.edge_nodes["us-east"].status = "failed"
    
    # Request from NYC should now go to next best option
    edge = router.find_optimal_edge(40.7128, -74.0060)
    assert edge.id != "us-east"
    assert edge.status == "healthy"

def test_distance_calculation():
    """Test geographic distance calculation"""
    router = CDNRouter()
    
    # Distance between NYC and London
    distance = router.calculate_distance(40.7128, -74.0060, 51.5074, -0.1278)
    
    # Should be approximately 5500km
    assert 5000 < distance < 6000

if __name__ == "__main__":
    pytest.main([__file__])
