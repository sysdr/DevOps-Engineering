"""In-memory database for metrics and state management"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import random
import uuid

class Database:
    def __init__(self):
        self.metrics: List[Dict] = []
        self.deployments: List[Dict] = []
        self.incidents: List[Dict] = []
        self.slo_configs: List[Dict] = self._default_slos()
        self.error_budgets: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._initialize_sample_data()
    
    def _default_slos(self) -> List[Dict]:
        return [
            {
                "id": "deployment-success-rate",
                "name": "Deployment Success Rate",
                "target": 99.5,
                "window": "1h",
                "indicator": "success_rate"
            },
            {
                "id": "sync-latency-p99",
                "name": "Sync Latency P99",
                "target": 95.0,
                "window": "1h",
                "indicator": "sync_latency_p99",
                "threshold_ms": 30000
            },
            {
                "id": "reconciliation-success",
                "name": "Reconciliation Success Rate",
                "target": 99.9,
                "window": "1h",
                "indicator": "reconciliation_success"
            }
        ]
    
    def _initialize_sample_data(self):
        now = datetime.utcnow()
        apps = ["frontend", "backend-api", "payment-service", "auth-service", "notification-service"]
        
        for i in range(60):
            ts = now - timedelta(minutes=60-i)
            for app in apps:
                success = random.random() > 0.02
                self.deployments.append({
                    "id": str(uuid.uuid4()),
                    "app": app,
                    "timestamp": ts.isoformat(),
                    "status": "success" if success else "failed",
                    "duration_ms": random.randint(5000, 45000),
                    "sync_attempts": 1 if success else random.randint(2, 5),
                    "environment": random.choice(["production", "staging"])
                })
                
                self.metrics.append({
                    "timestamp": ts.isoformat(),
                    "app": app,
                    "cpu_usage": random.uniform(20, 80),
                    "memory_usage": random.uniform(30, 70),
                    "sync_duration_ms": random.randint(1000, 30000),
                    "reconciliation_count": random.randint(1, 10),
                    "error_count": 0 if success else random.randint(1, 3)
                })
    
    async def add_metric(self, metric: Dict):
        async with self._lock:
            metric["timestamp"] = datetime.utcnow().isoformat()
            self.metrics.append(metric)
            if len(self.metrics) > 10000:
                self.metrics = self.metrics[-5000:]
    
    async def add_deployment(self, deployment: Dict):
        async with self._lock:
            deployment["id"] = str(uuid.uuid4())
            deployment["timestamp"] = datetime.utcnow().isoformat()
            self.deployments.append(deployment)
            if len(self.deployments) > 5000:
                self.deployments = self.deployments[-2500:]
    
    async def get_metrics_in_window(self, window_minutes: int) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        return [m for m in self.metrics if datetime.fromisoformat(m["timestamp"]) > cutoff]
    
    async def get_deployments_in_window(self, window_minutes: int) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        return [d for d in self.deployments if datetime.fromisoformat(d["timestamp"]) > cutoff]
    
    async def get_latest_metrics(self) -> Dict:
        if not self.metrics:
            return {}
        
        recent = self.metrics[-50:]
        apps = set(m["app"] for m in recent)
        
        result = {}
        for app in apps:
            app_metrics = [m for m in recent if m["app"] == app]
            if app_metrics:
                latest = app_metrics[-1]
                result[app] = {
                    "cpu": latest["cpu_usage"],
                    "memory": latest["memory_usage"],
                    "sync_duration": latest["sync_duration_ms"],
                    "errors": latest["error_count"]
                }
        return result
    
    async def get_recent_deployments(self, limit: int = 20) -> List[Dict]:
        return sorted(self.deployments, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    async def add_incident(self, incident: Dict):
        async with self._lock:
            incident["id"] = str(uuid.uuid4())
            incident["created_at"] = datetime.utcnow().isoformat()
            incident["status"] = "active"
            self.incidents.append(incident)
    
    async def get_active_incidents(self) -> List[Dict]:
        return [i for i in self.incidents if i["status"] == "active"]
    
    async def resolve_incident(self, incident_id: str):
        for incident in self.incidents:
            if incident["id"] == incident_id:
                incident["status"] = "resolved"
                incident["resolved_at"] = datetime.utcnow().isoformat()
    
    def get_slo_configs(self) -> List[Dict]:
        return self.slo_configs
    
    async def update_error_budget(self, slo_id: str, remaining: float):
        self.error_budgets[slo_id] = remaining
    
    async def get_error_budgets(self) -> Dict[str, float]:
        return self.error_budgets.copy()
