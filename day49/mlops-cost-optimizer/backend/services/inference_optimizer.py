import asyncio
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InferenceOptimizer:
    def __init__(self):
        self.benchmark_configs = [
            {
                "instance_type": "c5.2xlarge",
                "replicas": 4,
                "vcpu": 8,
                "memory": 16,
                "hourly_cost": 0.34
            },
            {
                "instance_type": "c5.4xlarge",
                "replicas": 2,
                "vcpu": 16,
                "memory": 32,
                "hourly_cost": 0.68
            },
            {
                "instance_type": "g4dn.xlarge",
                "replicas": 1,
                "vcpu": 4,
                "memory": 16,
                "hourly_cost": 0.526
            }
        ]
    
    async def benchmark_config(self, model_id: str, config: Dict) -> Dict:
        """Benchmark model on specific config"""
        # Simulate benchmarking
        await asyncio.sleep(0.5)
        
        # Calculate estimated metrics
        base_qps = config["vcpu"] * 50  # Rough estimate
        qps = base_qps * config["replicas"]
        p99_latency = 800 / config["vcpu"]  # Lower with more CPU
        
        monthly_cost = config["hourly_cost"] * config["replicas"] * 730
        
        return {
            "model_id": model_id,
            "instance_type": config["instance_type"],
            "replicas": config["replicas"],
            "qps": qps,
            "p99_latency_ms": p99_latency,
            "monthly_cost": monthly_cost
        }
    
    async def optimize_model(self, model_id: str, latency_sla: float = 100.0) -> Dict:
        """Find optimal config for model within latency SLA"""
        logger.info(f"Optimizing deployment for model {model_id}")
        
        results = []
        for config in self.benchmark_configs:
            metrics = await self.benchmark_config(model_id, config)
            if metrics["p99_latency_ms"] <= latency_sla:
                results.append(metrics)
        
        if not results:
            logger.warning(f"No config meets SLA of {latency_sla}ms")
            return None
        
        # Choose cheapest config that meets SLA
        optimal = min(results, key=lambda x: x["monthly_cost"])
        
        logger.info(f"Optimal config: {optimal['instance_type']} x{optimal['replicas']} "
                   f"({optimal['qps']} QPS, ${optimal['monthly_cost']:.2f}/month)")
        
        return optimal
    
    async def calculate_savings(self, baseline: Dict, optimized: Dict) -> Dict:
        """Calculate cost savings from optimization"""
        monthly_savings = baseline["monthly_cost"] - optimized["monthly_cost"]
        savings_percent = (monthly_savings / baseline["monthly_cost"]) * 100
        
        return {
            "baseline_cost": baseline["monthly_cost"],
            "optimized_cost": optimized["monthly_cost"],
            "monthly_savings": monthly_savings,
            "savings_percent": savings_percent,
            "annual_savings": monthly_savings * 12
        }
