import logging
from models.job import Job, TPUType

logger = logging.getLogger(__name__)

class CostOptimizer:
    def __init__(self, orchestrator=None):
        # Hourly costs (simulated)
        self.tpu_costs = {
            TPUType.V3_8: {"on_demand": 8.00, "preemptible": 2.40},
            TPUType.V3_32: {"on_demand": 32.00, "preemptible": 9.60},
            TPUType.V4_8: {"on_demand": 12.00, "preemptible": 3.60},
            TPUType.V4_32: {"on_demand": 48.00, "preemptible": 14.40},
            TPUType.V4_128: {"on_demand": 192.00, "preemptible": 57.60},
        }
        
        self.current_cost_rate = 0.0
        self.historical_preemption_rate = 0.05  # 5% chance per hour
        self.orchestrator = orchestrator
        
        logger.info("Cost Optimizer initialized")
    
    def set_orchestrator(self, orchestrator):
        """Set orchestrator reference for cost calculation"""
        self.orchestrator = orchestrator
    
    def estimate_cost(self, job: Job) -> float:
        """Estimate hourly cost for job"""
        base_cost = self.tpu_costs[job.tpu_type]
        
        if job.can_use_preemptible():
            cost = base_cost["preemptible"]
            # Factor in preemption overhead
            overhead_factor = 1 + (self.historical_preemption_rate * 0.15)
            return cost * overhead_factor
        else:
            return base_cost["on_demand"]
    
    def get_current_cost_rate(self) -> float:
        """Calculate current cost rate based on active jobs"""
        if not self.orchestrator:
            return self.current_cost_rate
        
        total_cost = 0.0
        for job in self.orchestrator.active_jobs.values():
            total_cost += self.estimate_cost(job)
        
        self.current_cost_rate = total_cost
        return self.current_cost_rate
    
    def get_preemption_rate(self) -> float:
        return self.historical_preemption_rate
    
    def get_current_metrics(self) -> dict:
        current_rate = self.get_current_cost_rate()
        return {
            "cost_per_hour": current_rate,
            "estimated_daily_cost": current_rate * 24,
            "preemptible_savings": 0.70,  # 70% savings
            "preemption_overhead": 0.05
        }
