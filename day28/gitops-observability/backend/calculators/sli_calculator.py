"""Calculates Service Level Indicators from raw metrics"""
import statistics
from typing import Dict, List, Any
from datetime import datetime, timedelta

class SLICalculator:
    def __init__(self, db):
        self.db = db
        self.status = "healthy"
    
    async def calculate(self) -> Dict[str, Any]:
        """Calculate all SLIs for current window"""
        try:
            deployments = await self.db.get_deployments_in_window(60)
            metrics = await self.db.get_metrics_in_window(60)
            
            slis = {
                "success_rate": await self._calculate_success_rate(deployments),
                "sync_latency": await self._calculate_sync_latency(deployments),
                "sync_latency_p99": await self._calculate_latency_percentile(deployments, 99),
                "sync_latency_p95": await self._calculate_latency_percentile(deployments, 95),
                "reconciliation_success": await self._calculate_reconciliation_rate(metrics),
                "error_rate": await self._calculate_error_rate(metrics),
                "throughput": await self._calculate_throughput(deployments),
                "resource_saturation": await self._calculate_saturation(metrics),
                "calculated_at": datetime.utcnow().isoformat()
            }
            
            self.status = "healthy"
            return slis
        except Exception as e:
            self.status = f"error: {e}"
            return {}
    
    async def _calculate_success_rate(self, deployments: List[Dict]) -> Dict:
        if not deployments:
            return {"value": 100.0, "total": 0, "successful": 0}
        
        successful = sum(1 for d in deployments if d["status"] == "success")
        total = len(deployments)
        rate = (successful / total) * 100
        
        return {
            "value": round(rate, 2),
            "total": total,
            "successful": successful,
            "failed": total - successful
        }
    
    async def _calculate_sync_latency(self, deployments: List[Dict]) -> Dict:
        if not deployments:
            return {"avg_ms": 0, "min_ms": 0, "max_ms": 0}
        
        durations = [d["duration_ms"] for d in deployments]
        
        return {
            "avg_ms": round(statistics.mean(durations), 2),
            "min_ms": min(durations),
            "max_ms": max(durations),
            "median_ms": round(statistics.median(durations), 2)
        }
    
    async def _calculate_latency_percentile(self, deployments: List[Dict], percentile: int) -> float:
        if not deployments:
            return 0.0
        
        durations = sorted([d["duration_ms"] for d in deployments])
        index = int(len(durations) * percentile / 100)
        index = min(index, len(durations) - 1)
        
        return durations[index]
    
    async def _calculate_reconciliation_rate(self, metrics: List[Dict]) -> Dict:
        if not metrics:
            return {"value": 100.0, "total": 0}
        
        total_reconciliations = sum(m["reconciliation_count"] for m in metrics)
        total_errors = sum(m["error_count"] for m in metrics)
        
        if total_reconciliations == 0:
            return {"value": 100.0, "total": 0}
        
        success_rate = ((total_reconciliations - total_errors) / total_reconciliations) * 100
        
        return {
            "value": round(max(0, success_rate), 2),
            "total": total_reconciliations,
            "errors": total_errors
        }
    
    async def _calculate_error_rate(self, metrics: List[Dict]) -> float:
        if not metrics:
            return 0.0
        
        total_errors = sum(m["error_count"] for m in metrics)
        return round(total_errors / len(metrics), 2)
    
    async def _calculate_throughput(self, deployments: List[Dict]) -> Dict:
        if not deployments:
            return {"per_hour": 0, "per_minute": 0}
        
        return {
            "per_hour": len(deployments),
            "per_minute": round(len(deployments) / 60, 2)
        }
    
    async def _calculate_saturation(self, metrics: List[Dict]) -> Dict:
        if not metrics:
            return {"cpu": 0, "memory": 0}
        
        cpu_values = [m["cpu_usage"] for m in metrics]
        memory_values = [m["memory_usage"] for m in metrics]
        
        return {
            "cpu": round(statistics.mean(cpu_values), 2),
            "memory": round(statistics.mean(memory_values), 2),
            "cpu_max": round(max(cpu_values), 2),
            "memory_max": round(max(memory_values), 2)
        }
