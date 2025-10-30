import pytest
import asyncio
from src.load_testing.load_generator import LoadTestGenerator, LoadTestConfig

@pytest.mark.asyncio
async def test_load_test_generator():
    """Test load test generator functionality"""
    config = LoadTestConfig(
        target_url="http://httpbin.org",
        concurrent_users=5,
        ramp_up_time=5,
        test_duration=10,
        request_patterns=[]
    )
    
    generator = LoadTestGenerator(config)
    
    # Test scenario generation
    scenarios = generator._generate_user_scenarios()
    assert len(scenarios) > 0
    
    # Test request data generation
    cart_data = generator._generate_request_data("/cart/add")
    assert "product_id" in cart_data
    assert "quantity" in cart_data

def test_load_test_config():
    """Test load test configuration"""
    config = LoadTestConfig(
        target_url="http://example.com",
        concurrent_users=10,
        ramp_up_time=30,
        test_duration=60,
        request_patterns=[]
    )
    
    assert config.target_url == "http://example.com"
    assert config.concurrent_users == 10
    assert config.ramp_up_time == 30
    assert config.test_duration == 60
