import asyncio
import asyncpg
from typing import Optional, List, Dict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobScheduler:
    def __init__(self, db_pool: asyncpg.Pool, spot_manager):
        self.db_pool = db_pool
        self.spot_manager = spot_manager
        self.job_queue = []
        self.team_budgets = {
            "recommendations": {"budget": 10000, "spend": 0},
            "search": {"budget": 5000, "spend": 0},
            "fraud-detection": {"budget": 8000, "spend": 0}
        }
    
    async def submit_job(self, job: Dict) -> Dict:
        """Submit ML job for scheduling"""
        logger.info(f"Received job {job['job_id']} (priority: {job['priority']})")
        
        # Check budget
        team = job["team"]
        estimated_cost = self.estimate_job_cost(job)
        
        if not self.check_budget(team, estimated_cost):
            return {
                "status": "rejected",
                "reason": "budget_exceeded",
                "team": team,
                "budget": self.team_budgets[team]["budget"],
                "current_spend": self.team_budgets[team]["spend"]
            }
        
        # Schedule based on priority
        if job["priority"] == "P0":
            # Critical: allocate immediately on-demand
            result = await self.allocate_on_demand(job)
        elif job["priority"] == "P1":
            # Normal: prefer spot, fallback to on-demand
            result = await self.allocate_spot(job)
            if not result:
                result = await self.allocate_on_demand(job)
        else:  # P2
            # Low: spot only, can queue
            result = await self.allocate_spot(job)
            if not result:
                self.job_queue.append(job)
                return {"status": "queued", "position": len(self.job_queue)}
        
        # Update budget
        self.team_budgets[team]["spend"] += estimated_cost
        
        return result
    
    def estimate_job_cost(self, job: Dict) -> float:
        """Estimate job cost based on resources and duration"""
        # Simplified cost estimation
        instance_costs = {
            "p3.8xlarge": 12.24,
            "g4dn.2xlarge": 0.752,
            "c5.4xlarge": 0.68
        }
        
        instance_type = job.get("instance_type", "g4dn.2xlarge")
        hourly_cost = instance_costs.get(instance_type, 1.0)
        duration_hours = job.get("estimated_duration", 2)
        
        return hourly_cost * duration_hours
    
    def check_budget(self, team: str, estimated_cost: float) -> bool:
        """Check if team has budget for job"""
        if team not in self.team_budgets:
            return True  # Unknown team, allow
        
        budget = self.team_budgets[team]
        return (budget["spend"] + estimated_cost) <= budget["budget"]
    
    async def allocate_spot(self, job: Dict) -> Optional[Dict]:
        """Allocate spot instance for job"""
        instance_type = job.get("instance_type", "g4dn.2xlarge")
        spot = await self.spot_manager.allocate_spot(job["job_id"], instance_type)
        
        if spot:
            return {
                "status": "scheduled",
                "instance_id": spot["instance_id"],
                "instance_type": spot["instance_type"],
                "type": "spot"
            }
        return None
    
    async def allocate_on_demand(self, job: Dict) -> Dict:
        """Allocate on-demand instance (always succeeds)"""
        return {
            "status": "scheduled",
            "instance_id": f"i-ondemand-{job['job_id']}",
            "instance_type": job.get("instance_type", "g4dn.2xlarge"),
            "type": "on-demand"
        }
    
    async def get_queue_stats(self) -> Dict:
        """Get job queue statistics"""
        return {
            "queued_jobs": len(self.job_queue),
            "p0_jobs": sum(1 for j in self.job_queue if j["priority"] == "P0"),
            "p1_jobs": sum(1 for j in self.job_queue if j["priority"] == "P1"),
            "p2_jobs": sum(1 for j in self.job_queue if j["priority"] == "P2")
        }
