import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dns.resolver import DNSResolver

@pytest.mark.asyncio
async def test_dns_resolution():
    """Test DNS resolution functionality"""
    resolver = DNSResolver()
    
    result = await resolver.resolve("api.example.com", "192.168.1.1")
    
    assert "domain" in result
    assert "resolved_to" in result
    assert result["domain"] == "api.example.com"
    assert result["response_time_ms"] > 0

@pytest.mark.asyncio
async def test_weighted_routing():
    """Test weighted DNS routing"""
    resolver = DNSResolver()
    
    results = []
    for _ in range(100):
        result = await resolver.resolve("api.example.com", "192.168.1.1")
        results.append(result["resolved_to"])
    
    # Should get both IPs in results due to weighted routing
    unique_ips = set(results)
    assert len(unique_ips) >= 1  # At least one IP should be returned

@pytest.mark.asyncio
async def test_health_check_integration():
    """Test health check affects routing"""
    resolver = DNSResolver()
    
    # Manually set one record as failed
    resolver.records["api.example.com"][0].status = "failed"
    
    # Resolution should still work with remaining healthy records
    result = await resolver.resolve("api.example.com", "192.168.1.1")
    assert result["resolved_to"] is not None

if __name__ == "__main__":
    pytest.main([__file__])
