import pytest
import asyncio
from backend.optimizer.query_optimizer import QueryOptimizer

@pytest.mark.asyncio
async def test_query_analysis():
    """Test slow query analysis"""
    optimizer = QueryOptimizer()
    
    await optimizer.analyze_queries()
    
    # Should detect simulated slow queries
    assert len(optimizer.slow_queries) > 0

def test_pattern_extraction():
    """Test query pattern extraction"""
    optimizer = QueryOptimizer()
    
    query = "SELECT * FROM users WHERE email = 'test@example.com'"
    pattern = optimizer.extract_pattern(query)
    
    assert '?' in pattern
    assert 'test@example.com' not in pattern

@pytest.mark.asyncio
async def test_recommendation_generation():
    """Test index recommendation generation"""
    optimizer = QueryOptimizer()
    
    await optimizer.analyze_queries()
    await optimizer.generate_recommendations()
    
    recommendations = optimizer.get_recommendations()
    
    assert 'recommendations' in recommendations
    assert 'slow_query_count' in recommendations
    if recommendations['recommendations']:
        rec = recommendations['recommendations'][0]
        assert 'table' in rec
        assert 'column' in rec
        assert 'statement' in rec
