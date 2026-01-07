import asyncio
import uuid
from datetime import datetime
from typing import Dict, List
import logging
import random

from backend.common.models import HealthStatus
from backend.common.metrics import (
    healing_actions_total, healing_success, healing_failures,
    recovery_time, cluster_health_score
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SelfHealingController:
    def __init__(self):
        self.resources: Dict[str, HealthStatus] = {}
        self.healing_actions = []
        self.recovery_history = []
        
    async def start(self):
        """Start reconciliation loop"""
        logger.info("Starting self-healing controller...")
        asyncio.create_task(self._reconciliation_loop())
        asyncio.create_task(self._health_monitor_loop())
    
    async def _reconciliation_loop(self):
        """Main reconciliation loop - Kubernetes operator pattern"""
        while True:
            try:
                unhealthy_resources = [
                    r for r in self.resources.values()
                    if not r.healthy
                ]
                
                if unhealthy_resources:
                    logger.info(f"Found {len(unhealthy_resources)} unhealthy resources")
                    
                    for resource in unhealthy_resources:
                        await self._heal_resource(resource)
                
                # Update cluster health score
                if self.resources:
                    healthy_count = sum(1 for r in self.resources.values() if r.healthy)
                    health_score = (healthy_count / len(self.resources)) * 100
                    cluster_health_score.set(health_score)
                
                await asyncio.sleep(10)  # Reconcile every 10 seconds
                
            except Exception as e:
                logger.error(f"Reconciliation loop error: {e}")
                await asyncio.sleep(5)
    
    async def _health_monitor_loop(self):
        """Monitor resource health"""
        while True:
            try:
                # Simulate resource monitoring
                for resource_id in list(self.resources.keys()):
                    resource = self.resources[resource_id]
                    
                    # Simulate health check
                    is_healthy = random.random() > 0.05  # 95% uptime simulation
                    
                    if is_healthy != resource.healthy:
                        resource.healthy = is_healthy
                        resource.last_check = datetime.now()
                        
                        if not is_healthy:
                            logger.warning(f"Resource {resource_id} became unhealthy")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)
    
    async def _heal_resource(self, resource: HealthStatus):
        """Execute healing actions for unhealthy resource"""
        start_time = datetime.now()
        healing_actions_total.inc()
        
        logger.info(f"Healing resource {resource.resource_id}")
        
        try:
            # Determine healing action based on resource type
            if resource.resource_type == "pod":
                action = "restart_pod"
            elif resource.resource_type == "node":
                action = "drain_and_replace"
            elif resource.resource_type == "service":
                action = "rollback_deployment"
            else:
                action = "generic_recovery"
            
            # Simulate healing action
            await asyncio.sleep(2)  # Simulate healing work
            
            # Mark as healthy
            resource.healthy = True
            resource.last_check = datetime.now()
            
            # Record success
            healing_success.inc()
            recovery_duration = (datetime.now() - start_time).total_seconds()
            recovery_time.observe(recovery_duration)
            
            self.healing_actions.append({
                'resource_id': resource.resource_id,
                'action': action,
                'timestamp': datetime.now(),
                'duration': recovery_duration,
                'success': True
            })
            
            logger.info(f"Successfully healed {resource.resource_id} in {recovery_duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to heal {resource.resource_id}: {e}")
            healing_failures.inc()
            
            self.healing_actions.append({
                'resource_id': resource.resource_id,
                'action': action,
                'timestamp': datetime.now(),
                'success': False,
                'error': str(e)
            })
    
    def register_resource(self, resource_type: str, resource_id: str):
        """Register a resource for monitoring"""
        self.resources[resource_id] = HealthStatus(
            resource_id=resource_id,
            resource_type=resource_type,
            healthy=True,
            last_check=datetime.now(),
            metrics={}
        )
        logger.info(f"Registered {resource_type} resource: {resource_id}")
    
    def get_healing_stats(self) -> dict:
        """Get healing statistics"""
        total_actions = len(self.healing_actions)
        successful = sum(1 for a in self.healing_actions if a.get('success', False))
        
        return {
            'total_actions': total_actions,
            'successful_actions': successful,
            'success_rate': (successful / total_actions * 100) if total_actions > 0 else 0,
            'recent_actions': self.healing_actions[-10:]
        }

# Global controller instance
controller = SelfHealingController()
