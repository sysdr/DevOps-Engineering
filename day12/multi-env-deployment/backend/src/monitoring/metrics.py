import time
import random
from datetime import datetime, timedelta
from typing import Dict, List

class MetricsCollector:
    def __init__(self):
        self.deployment_metrics = []
        self.environment_metrics = {}
        self._generate_sample_data()
    
    def _generate_sample_data(self):
        # Generate last 24 hours of metrics
        now = datetime.now()
        for i in range(24):
            timestamp = now - timedelta(hours=i)
            
            self.deployment_metrics.append({
                "timestamp": timestamp.isoformat(),
                "deployments_count": random.randint(5, 15),
                "success_rate": random.uniform(95, 99.5),
                "avg_deployment_time": random.uniform(300, 900),
                "rollback_count": random.randint(0, 2)
            })
        
        # Environment health metrics
        for env in ["dev", "staging", "prod"]:
            self.environment_metrics[env] = {
                "cpu_usage": random.uniform(20, 80),
                "memory_usage": random.uniform(30, 70),
                "request_rate": random.randint(100, 1000),
                "error_rate": random.uniform(0.1, 2.0),
                "response_time": random.uniform(50, 200)
            }
    
    async def get_deployment_metrics(self) -> Dict:
        # Get latest metrics
        latest = self.deployment_metrics[0] if self.deployment_metrics else {}
        
        return {
            "deployment_frequency": latest.get("deployments_count", 0),
            "success_rate": latest.get("success_rate", 0),
            "avg_deployment_time": latest.get("avg_deployment_time", 0),
            "mttr": random.uniform(5, 15),  # Mean Time To Recovery in minutes
            "environment_health": self.environment_metrics,
            "trend_data": self.deployment_metrics[:12]  # Last 12 hours
        }
    
    async def record_deployment_event(self, event_type: str, metadata: Dict):
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "metadata": metadata
        }
        
        # In production, this would go to a metrics system like Prometheus
        print(f"Metrics Event: {event}")
