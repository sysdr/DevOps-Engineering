import pytest
import asyncio
from datetime import datetime, timedelta
from backend.capacity.planner import CapacityPlanner
from backend.utils.metrics import MetricsCollector

@pytest.mark.asyncio
async def test_resource_collection():
    """Test resource metric collection"""
    collector = MetricsCollector()
    planner = CapacityPlanner(collector)
    
    await planner.collect_resource_metrics()
    
    assert len(planner.resource_history['cpu']) > 0
    assert len(planner.resource_history['memory']) > 0

def test_growth_forecasting():
    """Test growth forecast calculation"""
    collector = MetricsCollector()
    planner = CapacityPlanner(collector)
    
    # Add mock history
    for i in range(30):
        timestamp = datetime.utcnow() - timedelta(days=30-i)
        planner.resource_history['cpu'].append({
            'timestamp': timestamp,
            'value': 50 + i * 0.5  # Gradual growth
        })
    
    forecast = planner.forecast_growth(planner.resource_history['cpu'])
    
    assert 'current' in forecast
    assert 'growth_rate_weekly' in forecast
    assert forecast['growth_rate_weekly'] > 0

def test_runway_calculation():
    """Test capacity runway calculation"""
    collector = MetricsCollector()
    planner = CapacityPlanner(collector)
    
    forecast = {
        'current': 70.0,
        'growth_rate_weekly': 2.0
    }
    
    runway = planner.calculate_runway(forecast, 'cpu')
    
    assert runway > 0
    assert runway < 999  # Should have finite runway
