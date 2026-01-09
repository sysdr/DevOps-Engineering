import pytest
import asyncio
from backend.profiler.profiler import PerformanceProfiler
from backend.utils.metrics import MetricsCollector

@pytest.mark.asyncio
async def test_profiler_sampling():
    """Test profiler samples performance metrics"""
    collector = MetricsCollector()
    profiler = PerformanceProfiler(collector)
    
    await profiler.sample_performance()
    
    assert len(profiler.samples) > 0
    sample = profiler.samples[-1]
    assert 'cpu_percent' in sample
    assert 'memory_percent' in sample
    assert sample['cpu_percent'] >= 0

@pytest.mark.asyncio
async def test_hotspot_detection():
    """Test CPU hotspot detection"""
    collector = MetricsCollector()
    profiler = PerformanceProfiler(collector)
    
    await profiler.identify_hotspots()
    
    # Should identify processes using CPU
    assert isinstance(profiler.hotspots, dict)

def test_flame_graph_data():
    """Test flame graph data generation"""
    collector = MetricsCollector()
    profiler = PerformanceProfiler(collector)
    
    data = profiler.get_flame_graph_data()
    
    assert 'hotspots' in data
    assert 'samples' in data
    assert 'timestamp' in data
