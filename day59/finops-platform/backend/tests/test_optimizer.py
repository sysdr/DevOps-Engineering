import pytest
from app.services.optimizer import CostOptimizer

@pytest.mark.asyncio
async def test_generate_recommendations():
    optimizer = CostOptimizer()
    recommendations = await optimizer.generate_recommendations()
    
    assert len(recommendations) > 0
    assert 'savings_monthly' in recommendations[0]
    assert 'confidence' in recommendations[0]

@pytest.mark.asyncio
async def test_rightsizing_recommendations():
    optimizer = CostOptimizer()
    recommendations = await optimizer.get_rightsizing_recommendations()
    
    assert len(recommendations) > 0
    assert 'current_requests' in recommendations[0]
    assert 'recommended' in recommendations[0]

@pytest.mark.asyncio
async def test_waste_calculation():
    optimizer = CostOptimizer()
    waste = await optimizer.calculate_total_waste()
    
    assert waste > 0
