import time
from typing import Dict, List
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json

class MetricsCollector:
    def __init__(self):
        self.request_counts = defaultdict(int)
        self.response_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.bandwidth_usage = defaultdict(float)
        self.cache_metrics = defaultdict(dict)
        self.cost_data = defaultdict(float)
        self.time_series = deque(maxlen=1000)  # Keep last 1000 data points
        
    def record_request(self, region: str, response_time: float, 
                      cache_hit: bool, bandwidth: float, cost: float):
        """Record request metrics"""
        timestamp = datetime.now()
        
        self.request_counts[region] += 1
        self.response_times[region].append(response_time)
        self.bandwidth_usage[region] += bandwidth
        self.cost_data[region] += cost
        
        if cache_hit:
            self.cache_metrics[region]["hits"] = self.cache_metrics[region].get("hits", 0) + 1
        else:
            self.cache_metrics[region]["misses"] = self.cache_metrics[region].get("misses", 0) + 1
            
        # Time series data for dashboard
        self.time_series.append({
            "timestamp": timestamp.isoformat(),
            "region": region,
            "response_time": response_time,
            "cache_hit": cache_hit,
            "bandwidth": bandwidth,
            "cost": cost
        })
        
    def get_dashboard_data(self) -> Dict:
        """Get formatted data for dashboard"""
        total_requests = sum(self.request_counts.values())
        total_cost = sum(self.cost_data.values())
        total_bandwidth = sum(self.bandwidth_usage.values())
        
        # Calculate cache hit rate
        total_hits = sum(metrics.get("hits", 0) for metrics in self.cache_metrics.values())
        total_misses = sum(metrics.get("misses", 0) for metrics in self.cache_metrics.values())
        cache_hit_rate = (total_hits / max(total_hits + total_misses, 1)) * 100
        
        # Regional performance
        regional_data = []
        for region in self.request_counts.keys():
            avg_response_time = (sum(self.response_times[region]) / 
                               max(len(self.response_times[region]), 1))
            
            regional_data.append({
                "region": region,
                "requests": self.request_counts[region],
                "avg_response_time": round(avg_response_time, 2),
                "bandwidth_gb": round(self.bandwidth_usage[region] / 1024, 3),
                "cost_usd": round(self.cost_data[region], 4),
                "cache_hit_rate": round(
                    (self.cache_metrics[region].get("hits", 0) / 
                     max(self.cache_metrics[region].get("hits", 0) + 
                         self.cache_metrics[region].get("misses", 0), 1)) * 100, 1
                )
            })
            
        return {
            "overview": {
                "total_requests": total_requests,
                "total_cost_usd": round(total_cost, 4),
                "total_bandwidth_gb": round(total_bandwidth / 1024, 3),
                "cache_hit_rate": round(cache_hit_rate, 1),
                "avg_response_time": round(
                    sum(sum(times) for times in self.response_times.values()) / 
                    max(sum(len(times) for times in self.response_times.values()), 1), 2
                )
            },
            "regional_data": regional_data,
            "time_series": list(self.time_series)[-50:],  # Last 50 points for chart
            "cost_breakdown": {region: round(cost, 4) for region, cost in self.cost_data.items()}
        }
