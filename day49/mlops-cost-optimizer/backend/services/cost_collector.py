import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CostCollector:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.pricing = self._load_pricing()
    
    def _load_pricing(self) -> Dict:
        """Load current cloud pricing (simplified for demo)"""
        return {
            "c5.2xlarge": {"cpu": 8, "memory": 16, "cost": 0.34},
            "c5.4xlarge": {"cpu": 16, "memory": 32, "cost": 0.68},
            "g4dn.xlarge": {"cpu": 4, "memory": 16, "gpu": 1, "cost": 0.526},
            "g4dn.2xlarge": {"cpu": 8, "memory": 32, "gpu": 1, "cost": 0.752},
            "p3.2xlarge": {"cpu": 8, "memory": 61, "gpu": 1, "cost": 3.06},
            "p3.8xlarge": {"cpu": 32, "memory": 244, "gpu": 4, "cost": 12.24},
        }
    
    async def collect_pod_costs(self) -> List[Dict]:
        """Simulate collecting pod costs from Kubernetes"""
        pods = [
            {
                "name": "training-job-1",
                "team": "recommendations",
                "project": "user-ranking",
                "instance_type": "p3.8xlarge",
                "runtime_hours": 2.5,
                "priority": "P1"
            },
            {
                "name": "inference-server-1",
                "team": "search",
                "project": "query-understanding",
                "instance_type": "c5.4xlarge",
                "runtime_hours": 24.0,
                "priority": "P0"
            },
            {
                "name": "training-job-2",
                "team": "recommendations",
                "project": "content-ranking",
                "instance_type": "g4dn.2xlarge",
                "runtime_hours": 1.2,
                "priority": "P2"
            }
        ]
        
        costs = []
        for pod in pods:
            instance_type = pod["instance_type"]
            pricing = self.pricing[instance_type]
            cost = pricing["cost"] * pod["runtime_hours"]
            
            costs.append({
                "timestamp": datetime.now(),
                "team": pod["team"],
                "project": pod["project"],
                "instance_type": instance_type,
                "runtime_hours": pod["runtime_hours"],
                "cost": cost
            })
        
        return costs
    
    async def store_costs(self, costs: List[Dict]):
        """Store collected costs in database"""
        async with self.db_pool.acquire() as conn:
            for cost in costs:
                await conn.execute('''
                    INSERT INTO cost_records 
                    (timestamp, team, project, instance_type, runtime_hours, cost)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', cost["timestamp"], cost["team"], cost["project"],
                     cost["instance_type"], cost["runtime_hours"], cost["cost"])
        
        logger.info(f"Stored {len(costs)} cost records")
    
    async def run_collection_loop(self):
        """Main collection loop - runs every minute"""
        while True:
            try:
                costs = await self.collect_pod_costs()
                await self.store_costs(costs)
                await asyncio.sleep(60)  # Collect every minute
            except Exception as e:
                logger.error(f"Collection error: {e}")
                await asyncio.sleep(10)
