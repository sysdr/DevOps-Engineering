import pytest
import asyncio
from backend.autoscaler.predictor import PredictiveScaler
from backend.utils.metrics import MetricsCollector

@pytest.mark.asyncio
async def test_metric_collection():
    """Test metric collection"""
    collector = MetricsCollector()
    scaler = PredictiveScaler(collector)
    
    await scaler.collect_metrics()
    
    assert len(scaler.history) > 0
    assert 'load' in scaler.history[-1]
    assert 'replicas' in scaler.history[-1]

def test_forecast_generation():
    """Test load forecasting"""
    collector = MetricsCollector()
    scaler = PredictiveScaler(collector)
    
    # Add mock history
    for i in range(50):
        scaler.history.append({
            'timestamp': i,
            'load': 1000 + i * 10,
            'replicas': 3,
            'utilization': 0.5
        })
    
    forecast = scaler.forecast_load(horizon=6)
    
    assert 'predictions' in forecast
    assert len(forecast['predictions']) == 6
    assert forecast['predictions'][0] > 0

def test_scaling_decisions():
    """Test scaling decision logic"""
    collector = MetricsCollector()
    scaler = PredictiveScaler(collector)
    
    initial_replicas = scaler.current_replicas
    status = scaler.get_scaling_status()
    
    assert 'current_replicas' in status
    assert 'utilization' in status
    assert status['current_replicas'] == initial_replicas
