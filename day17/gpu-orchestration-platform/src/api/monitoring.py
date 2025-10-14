import asyncio
import time
from typing import Dict, List
from datetime import datetime, timedelta
import logging
from prometheus_client import Counter, Histogram, Gauge, generate_latest

logger = logging.getLogger(__name__)

# Prometheus metrics
gpu_utilization = Gauge('gpu_utilization_percent', 'GPU utilization percentage', ['gpu_id', 'gpu_name'])
gpu_memory_used = Gauge('gpu_memory_used_bytes', 'GPU memory used in bytes', ['gpu_id', 'gpu_name'])
gpu_temperature = Gauge('gpu_temperature_celsius', 'GPU temperature in Celsius', ['gpu_id', 'gpu_name'])
gpu_power_usage = Gauge('gpu_power_usage_watts', 'GPU power usage in watts', ['gpu_id', 'gpu_name'])

workload_duration = Histogram('workload_duration_seconds', 'Workload execution duration', ['workload_type'])
workload_counter = Counter('workloads_total', 'Total workloads processed', ['status', 'workload_type'])

class GPUMonitor:
    def __init__(self):
        self.monitoring = False
        self.metrics_history = []
        self.cost_data = {
            "total_spend": 0.0,
            "hourly_rates": {
                "A100": 3.20,
                "V100": 2.48, 
                "T4": 0.95
            }
        }
        # Initialize base metrics for dynamic changes
        self.base_metrics = {
            "gpu-0": {"util": 75.5, "memory": 32*1024**3, "temp": 65, "power": 380},
            "gpu-1": {"util": 45.2, "memory": 28*1024**3, "temp": 58, "power": 320},
            "gpu-2": {"util": 90.1, "memory": 24*1024**3, "temp": 78, "power": 290},
            "gpu-3": {"util": 35.8, "memory": 8*1024**3, "temp": 42, "power": 60}
        }
        self.time_offset = 0

    async def start_monitoring(self):
        """Start background monitoring loop"""
        self.monitoring = True
        asyncio.create_task(self._monitoring_loop())
        logger.info("GPU monitoring started")

    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.monitoring:
            try:
                await self._collect_gpu_metrics()
                await asyncio.sleep(3)  # Collect every 3 seconds for better chart updates
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")

    async def _collect_gpu_metrics(self):
        """Collect GPU metrics and update Prometheus counters"""
        import random
        import math
        
        current_time = datetime.utcnow()
        self.time_offset += 1
        
        # Generate dynamic metrics with realistic patterns
        gpu_data = []
        gpu_names = ["A100", "A100", "V100", "T4"]
        
        for i, gpu_id in enumerate(["gpu-0", "gpu-1", "gpu-2", "gpu-3"]):
            base = self.base_metrics[gpu_id]
            
            # Create realistic utilization patterns
            # Add sine wave for natural variation + random noise
            time_factor = self.time_offset * 0.1
            sine_variation = math.sin(time_factor + i) * 15  # ±15% variation
            random_noise = random.uniform(-5, 5)  # ±5% random noise
            
            # Calculate new utilization
            new_util = base["util"] + sine_variation + random_noise
            new_util = max(0, min(100, new_util))  # Clamp between 0-100
            
            # Correlate other metrics with utilization
            memory_factor = new_util / 100
            temp_factor = new_util / 100
            power_factor = new_util / 100
            
            # Calculate correlated metrics
            memory_used = int(base["memory"] * (0.3 + 0.7 * memory_factor))  # 30-100% of memory
            temperature = int(base["temp"] * (0.7 + 0.3 * temp_factor) + random.uniform(-2, 2))
            power_usage = int(base["power"] * (0.5 + 0.5 * power_factor) + random.uniform(-10, 10))
            
            # Ensure realistic bounds
            temperature = max(30, min(85, temperature))
            power_usage = max(50, min(400, power_usage))
            
            gpu_data.append({
                "id": gpu_id,
                "name": gpu_names[i],
                "util": round(new_util, 1),
                "memory": memory_used,
                "temp": round(temperature),
                "power": round(power_usage)
            })
        
        metrics_snapshot = {
            "timestamp": current_time.isoformat(),
            "gpus": []
        }
        
        for gpu in gpu_data:
            # Update Prometheus metrics
            gpu_utilization.labels(gpu_id=gpu["id"], gpu_name=gpu["name"]).set(gpu["util"])
            gpu_memory_used.labels(gpu_id=gpu["id"], gpu_name=gpu["name"]).set(gpu["memory"])
            gpu_temperature.labels(gpu_id=gpu["id"], gpu_name=gpu["name"]).set(gpu["temp"])
            gpu_power_usage.labels(gpu_id=gpu["id"], gpu_name=gpu["name"]).set(gpu["power"])
            
            metrics_snapshot["gpus"].append({
                "id": gpu["id"],
                "name": gpu["name"],
                "utilization": gpu["util"],
                "memory_used_gb": gpu["memory"] // (1024**3),
                "temperature": gpu["temp"],
                "power_usage": gpu["power"]
            })
        
        self.metrics_history.append(metrics_snapshot)
        
        # Keep only last 100 snapshots
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)

    async def collect_metrics(self) -> Dict:
        """Get current GPU metrics for API"""
        if not self.metrics_history:
            await self._collect_gpu_metrics()
        
        latest = self.metrics_history[-1] if self.metrics_history else {"timestamp": datetime.utcnow().isoformat(), "gpus": []}
        
        # Calculate cluster-wide statistics
        total_gpus = len(latest["gpus"])
        avg_utilization = sum(gpu["utilization"] for gpu in latest["gpus"]) / max(1, total_gpus)
        total_memory = sum(gpu["memory_used_gb"] for gpu in latest["gpus"])
        avg_temperature = sum(gpu["temperature"] for gpu in latest["gpus"]) / max(1, total_gpus)
        total_power = sum(gpu["power_usage"] for gpu in latest["gpus"])
        
        return {
            "timestamp": latest["timestamp"],
            "cluster_stats": {
                "total_gpus": total_gpus,
                "average_utilization": round(avg_utilization, 2),
                "total_memory_used_gb": total_memory,
                "average_temperature": round(avg_temperature, 1),
                "total_power_usage": total_power
            },
            "individual_gpus": latest["gpus"],
            "historical_data": self.metrics_history[-20:]  # Last 20 snapshots
        }

    async def analyze_costs(self) -> Dict:
        """Analyze GPU usage costs and provide optimization recommendations"""
        current_hour_cost = 0.0
        utilization_scores = {}
        
        if self.metrics_history:
            latest = self.metrics_history[-1]
            for gpu in latest["gpus"]:
                gpu_type = gpu["name"]
                hourly_rate = self.cost_data["hourly_rates"].get(gpu_type, 2.0)
                current_hour_cost += hourly_rate
                utilization_scores[gpu["id"]] = gpu["utilization"]
        
        # Calculate daily and monthly projections
        daily_cost = current_hour_cost * 24
        monthly_cost = daily_cost * 30
        
        # Identify underutilized GPUs
        underutilized = [gpu_id for gpu_id, util in utilization_scores.items() if util < 30]
        
        # Generate optimization recommendations
        recommendations = []
        
        if len(underutilized) > 0:
            potential_savings = len(underutilized) * 2.0 * 24 * 30  # Conservative estimate
            recommendations.append({
                "type": "underutilization",
                "message": f"Consider deallocating {len(underutilized)} underutilized GPUs",
                "potential_monthly_savings": potential_savings
            })
        
        if current_hour_cost > 50:
            recommendations.append({
                "type": "high_cost",
                "message": "Consider using spot instances for non-critical workloads",
                "potential_monthly_savings": monthly_cost * 0.7  # 70% savings with spots
            })
        
        return {
            "current_hourly_cost": round(current_hour_cost, 2),
            "projected_daily_cost": round(daily_cost, 2),
            "projected_monthly_cost": round(monthly_cost, 2),
            "utilization_analysis": utilization_scores,
            "underutilized_gpus": underutilized,
            "optimization_recommendations": recommendations,
            "cost_breakdown_by_gpu_type": {
                gpu_type: {"hourly_rate": rate, "count": sum(1 for gpu in latest["gpus"] if gpu["name"] == gpu_type)} 
                for gpu_type, rate in self.cost_data["hourly_rates"].items()
                if self.metrics_history and any(gpu["name"] == gpu_type for gpu in self.metrics_history[-1]["gpus"])
            }
        }

    def get_prometheus_metrics(self) -> str:
        """Return Prometheus metrics in text format"""
        return generate_latest()
