import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import HyperscaleSystem

def test_geographic_routing():
    """Test geographic routing to nearest region"""
    system = HyperscaleSystem()
    
    # New York location should route to US-EAST
    ny_location = (40.7, -74.0)
    region = system.route_request(ny_location)
    assert region == "us-east", "New York should route to US-EAST"
    
    # San Francisco should route to US-WEST
    sf_location = (37.7, -122.4)
    region = system.route_request(sf_location)
    assert region == "us-west", "San Francisco should route to US-WEST"
    
    # London should route to EU-WEST
    london_location = (51.5, -0.1)
    region = system.route_request(london_location)
    assert region == "eu-west", "London should route to EU-WEST"

def test_health_based_routing():
    """Test routing avoids unhealthy regions"""
    system = HyperscaleSystem()
    
    # Mark US-EAST as unhealthy
    system.regions["us-east"]["health"] = 30
    
    # NY request should fail over to US-WEST
    ny_location = (40.7, -74.0)
    region = system.route_request(ny_location)
    assert region != "us-east", "Should not route to unhealthy region"

def test_region_failover():
    """Test automatic failover when region fails"""
    system = HyperscaleSystem()
    
    # Fail US-EAST
    system.failed_regions.add("us-east")
    
    # Should route to alternative regions
    ny_location = (40.7, -74.0)
    region = system.route_request(ny_location)
    assert region in ["us-west", "eu-west"], "Should failover to healthy region"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
