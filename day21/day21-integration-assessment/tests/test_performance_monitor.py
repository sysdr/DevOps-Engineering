import pytest
from src.monitoring.performance_monitor import PerformanceMonitor

def test_performance_monitor():
    """Test performance monitoring functionality"""
    monitor = PerformanceMonitor()
    
    # Test initialization
    assert monitor.system_metrics == []
    assert monitor.app_metrics == []
    assert "cpu_percent" in monitor.alert_thresholds
    
    # Test report generation
    report = monitor.get_performance_report()
    assert "error" in report or "system_averages" in report

def test_alert_thresholds():
    """Test alert threshold configuration"""
    monitor = PerformanceMonitor()
    thresholds = monitor.alert_thresholds
    
    assert thresholds["cpu_percent"] > 0
    assert thresholds["memory_percent"] > 0
    assert thresholds["response_time_avg"] > 0
    assert thresholds["error_rate"] > 0
