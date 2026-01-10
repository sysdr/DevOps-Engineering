import pytest
import asyncio
from app.services.cost_collector import CostCollector

@pytest.mark.asyncio
async def test_cost_collection():
    collector = CostCollector()
    await collector.collect_metrics()
    
    assert collector.get_total_cost() > 0
    assert len(collector.get_namespace_costs()) > 0
    assert collector.get_compute_cost() > 0

@pytest.mark.asyncio
async def test_cost_trend():
    collector = CostCollector()
    await collector.collect_metrics()
    
    trend = collector.get_cost_trend(7)
    assert len(trend) > 0
    assert 'timestamp' in trend[0]
    assert 'cost' in trend[0]

def test_cost_breakdown():
    collector = CostCollector()
    collector.total_cost = 1000.0
    collector.compute_cost = 600.0
    collector.storage_cost = 250.0
    collector.network_cost = 150.0
    
    assert collector.get_compute_cost() == 600.0
    assert collector.get_storage_cost() == 250.0
    assert collector.get_network_cost() == 150.0
