import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List

class CostCollector:
    def __init__(self):
        self.total_cost = 0.0
        self.namespace_costs = {}
        self.cost_history = []
        self.compute_cost = 0.0
        self.storage_cost = 0.0
        self.network_cost = 0.0
        
    async def collect_metrics(self):
        """Collect cost metrics from various sources"""
        # Simulate collecting metrics from Kubernetes and cloud APIs
        namespaces = ['production', 'staging', 'development', 'ml-training', 'data-pipeline']
        
        self.namespace_costs = {}
        for ns in namespaces:
            # Simulate cost calculation based on resource usage
            base_cost = random.uniform(100, 5000)
            self.namespace_costs[ns] = round(base_cost, 2)
        
        self.total_cost = sum(self.namespace_costs.values())
        
        # Breakdown by resource type
        self.compute_cost = self.total_cost * 0.6
        self.storage_cost = self.total_cost * 0.25
        self.network_cost = self.total_cost * 0.15
        
        # Store historical data
        self.cost_history.append({
            'timestamp': datetime.utcnow(),
            'total': self.total_cost,
            'namespaces': self.namespace_costs.copy()
        })
        
        # Keep only last 90 days
        cutoff = datetime.utcnow() - timedelta(days=90)
        self.cost_history = [h for h in self.cost_history if h['timestamp'] > cutoff]
        
    def get_total_cost(self) -> float:
        return round(self.total_cost, 2)
    
    def get_namespace_costs(self) -> Dict[str, float]:
        return self.namespace_costs
    
    def get_cost_trend(self, days: int) -> List[Dict]:
        """Get cost trend for specified number of days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [h for h in self.cost_history if h['timestamp'] > cutoff]
        
        # Generate hourly aggregates
        trend = []
        for i in range(days * 24):
            timestamp = datetime.utcnow() - timedelta(hours=days*24-i)
            cost = random.uniform(500, 2000)  # Simulate historical costs
            trend.append({
                'timestamp': timestamp.isoformat(),
                'cost': round(cost, 2)
            })
        return trend
    
    def get_compute_cost(self) -> float:
        return round(self.compute_cost, 2)
    
    def get_storage_cost(self) -> float:
        return round(self.storage_cost, 2)
    
    def get_network_cost(self) -> float:
        return round(self.network_cost, 2)
