import asyncio
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class TPUMonitor:
    def __init__(self, orchestrator=None):
        self.metrics_cache: Dict[str, dict] = {}
        self.cluster_metrics = {
            "total_utilization": 0.0,
            "average_mxu": 0.0,
            "total_flops": 0.0
        }
        self.orchestrator = orchestrator
        
        logger.info("TPU Monitor initialized")
    
    def set_orchestrator(self, orchestrator):
        """Set orchestrator reference for metrics calculation"""
        self.orchestrator = orchestrator
    
    async def collection_loop(self):
        """Background metrics collection"""
        logger.info("Starting metrics collection loop...")
        
        while True:
            try:
                await self._collect_metrics()
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
    
    async def _collect_metrics(self):
        """Collect metrics from all active jobs"""
        if not self.orchestrator:
            return
        
        active_jobs = list(self.orchestrator.active_jobs.values())
        
        if not active_jobs:
            self.cluster_metrics = {
                "total_utilization": 0.0,
                "average_mxu": 0.0,
                "total_flops": 0.0
            }
            return
        
        # Calculate aggregate metrics from active jobs
        total_mxu = 0.0
        total_flops = 0.0
        job_count = 0
        
        for job in active_jobs:
            job_metrics = job.metrics if job.metrics else {}
            mxu = job_metrics.get("mxu_utilization", 0.0)
            flops = job_metrics.get("flops", 0.0)
            
            total_mxu += mxu
            total_flops += flops
            job_count += 1
            
            # Cache job metrics
            self.metrics_cache[job.job_id] = job_metrics
        
        # Calculate averages
        avg_mxu = total_mxu / job_count if job_count > 0 else 0.0
        
        # Calculate utilization (based on active jobs vs total capacity)
        total_capacity = self.orchestrator.tpu_resources.total_capacity()
        utilization = (len(active_jobs) / total_capacity * 100) if total_capacity > 0 else 0.0
        
        self.cluster_metrics = {
            "total_utilization": min(utilization, 100.0),
            "average_mxu": avg_mxu,
            "total_flops": total_flops
        }
    
    def get_job_metrics(self, job_id: str) -> dict:
        """Get metrics for specific job"""
        return self.metrics_cache.get(job_id, {
            "mxu_utilization": 0.0,
            "memory_bandwidth_gbps": 0.0,
            "step_time_ms": 0.0,
            "flops": 0.0
        })
    
    def get_cluster_utilization(self) -> float:
        return self.cluster_metrics["total_utilization"]
    
    async def get_cluster_metrics(self) -> dict:
        return {
            **self.cluster_metrics,
            "timestamp": datetime.now().isoformat()
        }
