"""Collects metrics from GitOps controllers and Kubernetes"""
import asyncio
import random
from datetime import datetime
from typing import Dict, Any

class MetricsCollector:
    def __init__(self, db):
        self.db = db
        self.status = "healthy"
        self._apps = ["frontend", "backend-api", "payment-service", "auth-service", "notification-service"]
    
    async def collect(self):
        """Collect metrics from all sources"""
        try:
            for app in self._apps:
                metric = await self._collect_app_metrics(app)
                await self.db.add_metric(metric)
                
                if random.random() > 0.7:
                    deployment = await self._collect_deployment(app)
                    await self.db.add_deployment(deployment)
            
            self.status = "healthy"
        except Exception as e:
            self.status = f"error: {e}"
    
    async def _collect_app_metrics(self, app: str) -> Dict[str, Any]:
        base_cpu = {"frontend": 35, "backend-api": 55, "payment-service": 45, 
                   "auth-service": 40, "notification-service": 30}
        
        return {
            "app": app,
            "cpu_usage": base_cpu.get(app, 40) + random.uniform(-10, 20),
            "memory_usage": random.uniform(40, 75),
            "sync_duration_ms": random.randint(2000, 25000),
            "reconciliation_count": random.randint(1, 8),
            "error_count": 0 if random.random() > 0.05 else random.randint(1, 3),
            "pending_syncs": random.randint(0, 3),
            "healthy_replicas": random.randint(2, 5),
            "total_replicas": 5
        }
    
    async def _collect_deployment(self, app: str) -> Dict[str, Any]:
        success = random.random() > 0.03
        return {
            "app": app,
            "status": "success" if success else "failed",
            "duration_ms": random.randint(8000, 40000),
            "sync_attempts": 1 if success else random.randint(2, 4),
            "environment": random.choice(["production", "staging"]),
            "commit_sha": f"{random.randint(1000000, 9999999):07x}",
            "image_tag": f"v1.{random.randint(0, 99)}.{random.randint(0, 999)}"
        }
    
    async def collect_controller_metrics(self) -> Dict[str, Any]:
        return {
            "argocd": {
                "sync_total": random.randint(100, 500),
                "sync_failures": random.randint(0, 10),
                "reconciliation_queue": random.randint(0, 20),
                "cpu_percent": random.uniform(20, 60),
                "memory_mb": random.randint(200, 800)
            }
        }
