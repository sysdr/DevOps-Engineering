import pytest
from src.features.flags import FeatureFlagService

@pytest.mark.asyncio
async def test_feature_flag_creation():
    service = FeatureFlagService()
    
    result = await service.create_flag("test_feature", {
        "enabled": True,
        "rollout_percentage": 50,
        "environments": ["dev", "staging"]
    })
    
    assert result["status"] == "created"
    assert result["flag"]["enabled"] is True

@pytest.mark.asyncio
async def test_feature_flag_evaluation():
    service = FeatureFlagService()
    
    # Test existing flag
    result = await service.evaluate_flag("new_checkout_flow", "user123", "dev")
    assert isinstance(result, bool)

@pytest.mark.asyncio
async def test_feature_flag_update():
    service = FeatureFlagService()
    
    result = await service.update_flag("dark_mode", {
        "enabled": True,
        "rollout_percentage": 75
    })
    
    assert result["status"] == "updated"
    assert result["flag"]["enabled"] is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
