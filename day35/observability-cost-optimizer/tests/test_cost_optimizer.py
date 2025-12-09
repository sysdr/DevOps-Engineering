import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import CostOptimizer, MetricData, TraceData

def test_metric_cost_calculation():
    """Test metric cost calculation with various cardinalities"""
    optimizer = CostOptimizer()
    
    # Low cardinality metric
    metric = MetricData(
        service="test-service",
        metric_name="http_requests_total",
        cardinality=100,
        samples_per_second=10,
        data_size_mb=5
    )
    
    result = optimizer.calculate_metric_cost(metric)
    
    assert result["service"] == "test-service"
    assert result["time_series_count"] == 100
    assert result["cardinality_impact"] == "MEDIUM"
    assert result["total_monthly_cost"] > 0
    
    # High cardinality metric
    high_card_metric = MetricData(
        service="test-service",
        metric_name="user_requests",
        cardinality=2000,
        samples_per_second=50,
        data_size_mb=20
    )
    
    high_result = optimizer.calculate_metric_cost(high_card_metric)
    assert high_result["cardinality_impact"] == "HIGH"
    assert high_result["total_monthly_cost"] > result["total_monthly_cost"]

def test_trace_sampling_optimization():
    """Test optimal sampling rate calculation"""
    optimizer = CostOptimizer()
    
    # High error rate - should recommend higher sampling
    high_error_trace = TraceData(
        service="critical-service",
        traces_per_second=100,
        avg_spans_per_trace=10,
        error_rate=0.1  # 10% errors
    )
    
    result = optimizer.calculate_trace_cost(high_error_trace)
    
    assert result["optimal_sample_rate"] > 0.1  # At minimum error rate
    assert result["potential_monthly_savings"] > 0
    
    # Low error rate - aggressive sampling
    low_error_trace = TraceData(
        service="batch-service",
        traces_per_second=50,
        avg_spans_per_trace=5,
        error_rate=0.001  # 0.1% errors
    )
    
    low_result = optimizer.calculate_trace_cost(low_error_trace)
    assert low_result["optimal_sample_rate"] < high_error_trace.error_rate * 2

def test_retention_savings_calculation():
    """Test multi-tier retention savings"""
    optimizer = CostOptimizer()
    
    result = optimizer.calculate_retention_savings("api-gateway", 100.0)
    
    assert result["service"] == "api-gateway"
    assert result["monthly_savings"] > 0
    assert result["savings_percentage"] > 0
    assert result["optimized_monthly_cost"] < result["current_monthly_cost"]
    
    # Verify retention tiers are properly configured
    assert "hot" in result["retention_policy"]
    assert "warm" in result["retention_policy"]
    assert "cold" in result["retention_policy"]
    assert "archive" in result["retention_policy"]

def test_alert_cost_calculation():
    """Test alerting cost calculation and optimization"""
    optimizer = CostOptimizer()
    
    alert_types = {
        "sms": 10,
        "pagerduty": 5,
        "webhook": 85
    }
    
    result = optimizer.calculate_alert_cost("payment-service", 100, alert_types)
    
    assert result["service"] == "payment-service"
    assert result["total_monthly_cost"] > 0
    assert result["optimized_cost"] < result["total_monthly_cost"]
    assert result["potential_savings"] > 0
    
    # Verify cost breakdown by type
    assert "sms" in result["cost_by_type"]
    assert "pagerduty" in result["cost_by_type"]
    assert "webhook" in result["cost_by_type"]

def test_roi_calculation():
    """Test ROI calculation with various value metrics"""
    optimizer = CostOptimizer()
    
    # Set positive value metrics
    optimizer.roi_metrics["mttr_reduction_hours"] = 10
    optimizer.roi_metrics["incidents_prevented"] = 2
    optimizer.roi_metrics["optimization_savings"] = 5000
    
    result = optimizer.calculate_roi(10000)  # $10K monthly cost
    
    assert result["monthly_observability_cost"] == 10000
    assert result["value_metrics"]["total_value"] > 0
    assert "roi_percentage" in result
    assert result["roi_status"] in ["POSITIVE", "NEGATIVE"]

def test_service_cost_tracking():
    """Test service cost aggregation"""
    optimizer = CostOptimizer()
    
    optimizer.update_service_cost("api-gateway", "metrics", 500)
    optimizer.update_service_cost("api-gateway", "traces", 300)
    optimizer.update_service_cost("api-gateway", "storage", 200)
    
    assert optimizer.service_costs["api-gateway"]["metrics"] == 500
    assert optimizer.service_costs["api-gateway"]["traces"] == 300
    assert optimizer.service_costs["api-gateway"]["total"] == 1000

def test_cardinality_impact_thresholds():
    """Test cardinality impact classification"""
    optimizer = CostOptimizer()
    
    # Low cardinality
    low_metric = MetricData(
        service="test",
        metric_name="simple_counter",
        cardinality=50,
        samples_per_second=5,
        data_size_mb=1
    )
    assert optimizer.calculate_metric_cost(low_metric)["cardinality_impact"] == "LOW"
    
    # Medium cardinality
    med_metric = MetricData(
        service="test",
        metric_name="service_requests",
        cardinality=500,
        samples_per_second=20,
        data_size_mb=5
    )
    assert optimizer.calculate_metric_cost(med_metric)["cardinality_impact"] == "MEDIUM"
    
    # High cardinality
    high_metric = MetricData(
        service="test",
        metric_name="user_events",
        cardinality=5000,
        samples_per_second=100,
        data_size_mb=50
    )
    assert optimizer.calculate_metric_cost(high_metric)["cardinality_impact"] == "HIGH"

def test_sampling_preserves_errors():
    """Verify error traces are always fully sampled"""
    optimizer = CostOptimizer()
    
    for error_rate in [0.01, 0.05, 0.10, 0.20]:
        optimal_rate = optimizer.calculate_optimal_sampling(error_rate, 1000)
        # Optimal rate should always be at least the error rate
        assert optimal_rate >= error_rate

def test_cost_model_consistency():
    """Verify cost model values are consistent"""
    from main import COST_MODELS
    
    # Hot storage should be most expensive
    assert COST_MODELS["hot_storage"] > COST_MODELS["warm_storage"]
    assert COST_MODELS["warm_storage"] > COST_MODELS["cold_storage"]
    assert COST_MODELS["cold_storage"] > COST_MODELS["archive_storage"]
    
    # Alert costs should be ordered
    assert COST_MODELS["alert_pagerduty"] > COST_MODELS["alert_sms"]
    assert COST_MODELS["alert_sms"] > COST_MODELS["alert_webhook"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
