import asyncio
import asyncpg
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpotInstanceManager:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.spot_pool = []
        self.availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
    
    async def initialize_spot_pool(self, instance_type: str, count: int):
        """Initialize pool of spot instances"""
        for i in range(count):
            spot = {
                "instance_id": f"i-spot-{random.randint(10000, 99999)}",
                "instance_type": instance_type,
                "availability_zone": random.choice(self.availability_zones),
                "state": "available",
                "assigned_job": None,
                "created_at": datetime.now()
            }
            self.spot_pool.append(spot)
        
        logger.info(f"Initialized {count} spot instances of type {instance_type}")
    
    async def allocate_spot(self, job_id: str, instance_type: str) -> Optional[Dict]:
        """Allocate spot instance to job"""
        for spot in self.spot_pool:
            if (spot["state"] == "available" and 
                spot["instance_type"] == instance_type):
                spot["state"] = "allocated"
                spot["assigned_job"] = job_id
                logger.info(f"Allocated {spot['instance_id']} to job {job_id}")
                return spot
        
        return None
    
    async def simulate_spot_interruption(self, instance_id: str) -> Dict:
        """Simulate AWS spot interruption signal"""
        for spot in self.spot_pool:
            if spot["instance_id"] == instance_id:
                spot["state"] = "interrupted"
                spot["interruption_time"] = datetime.now()
                logger.warning(f"Spot instance {instance_id} interrupted!")
                
                # Trigger checkpoint and reschedule
                job_id = spot["assigned_job"]
                recovery_info = {
                    "instance_id": instance_id,
                    "had_job": job_id is not None,
                    "job_id": job_id,
                    "recovery_successful": False,
                    "new_instance_id": None
                }
                
                if job_id:
                    recovery_result = await self.handle_spot_interruption(job_id, spot)
                    recovery_info["recovery_successful"] = recovery_result["success"]
                    recovery_info["new_instance_id"] = recovery_result.get("new_instance_id")
                else:
                    recovery_info["message"] = "No job was running on this instance"
                
                return recovery_info
        
        return {
            "error": f"Instance {instance_id} not found",
            "instance_id": instance_id
        }
    
    async def handle_spot_interruption(self, job_id: str, old_spot: Dict) -> Dict:
        """Handle spot interruption by checkpointing and rescheduling"""
        logger.info(f"Handling interruption for job {job_id}")
        
        # Simulate checkpoint
        await self.checkpoint_job(job_id)
        
        # Find replacement spot instance
        new_spot = await self.find_replacement_spot(old_spot["instance_type"])
        
        if new_spot:
            # Reschedule job
            await self.reschedule_job(job_id, new_spot)
            logger.info(f"Job {job_id} rescheduled to {new_spot['instance_id']}")
            return {
                "success": True,
                "new_instance_id": new_spot["instance_id"],
                "message": f"Job {job_id} successfully recovered on {new_spot['instance_id']}"
            }
        else:
            logger.error(f"No replacement spot available for job {job_id}")
            return {
                "success": False,
                "message": f"No replacement spot available for job {job_id}"
            }
    
    async def checkpoint_job(self, job_id: str):
        """Checkpoint job state"""
        checkpoint = {
            "job_id": job_id,
            "timestamp": datetime.now(),
            "state": "checkpointed"
        }
        logger.info(f"Checkpointed job {job_id}")
        await asyncio.sleep(1)  # Simulate checkpoint time
    
    async def find_replacement_spot(self, instance_type: str) -> Optional[Dict]:
        """Find replacement spot in different AZ"""
        for spot in self.spot_pool:
            if (spot["state"] == "available" and 
                spot["instance_type"] == instance_type):
                return spot
        return None
    
    async def reschedule_job(self, job_id: str, new_spot: Dict):
        """Reschedule job on new spot instance"""
        new_spot["state"] = "allocated"
        new_spot["assigned_job"] = job_id
        logger.info(f"Job {job_id} running on {new_spot['instance_id']}")
    
    async def get_spot_statistics(self) -> Dict:
        """Get spot instance statistics"""
        total = len(self.spot_pool)
        available = sum(1 for s in self.spot_pool if s["state"] == "available")
        allocated = sum(1 for s in self.spot_pool if s["state"] == "allocated")
        interrupted = sum(1 for s in self.spot_pool if s["state"] == "interrupted")
        
        return {
            "total": total,
            "available": available,
            "allocated": allocated,
            "interrupted": interrupted,
            "utilization": (allocated / total * 100) if total > 0 else 0
        }
    
    async def get_spot_instances(self) -> List[Dict]:
        """Get list of all spot instances"""
        return [
            {
                "instance_id": spot["instance_id"],
                "instance_type": spot["instance_type"],
                "state": spot["state"],
                "assigned_job": spot.get("assigned_job"),
                "availability_zone": spot.get("availability_zone")
            }
            for spot in self.spot_pool
        ]
