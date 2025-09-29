import asyncio
from datetime import datetime
from typing import Dict, List

class CanaryDeployer:
    def __init__(self):
        self.canary_config = {
            "stages": [1, 5, 10, 25, 50, 100],
            "stage_duration": 300,  # 5 minutes per stage
            "success_criteria": {
                "error_rate_threshold": 0.01,
                "latency_p99_threshold": 500,
                "success_rate_threshold": 99.9
            }
        }
        self.current_deployment = None
    
    async def execute_canary_deployment(self, deployment_id: str):
        print(f"Starting canary deployment {deployment_id}")
        
        self.current_deployment = {
            "id": deployment_id,
            "status": "in_progress",
            "current_stage": 0,
            "traffic_percentage": 0,
            "started_at": datetime.now().isoformat()
        }
        
        for stage_index, traffic_percentage in enumerate(self.canary_config["stages"]):
            print(f"Canary Stage {stage_index + 1}: {traffic_percentage}% traffic")
            
            self.current_deployment["current_stage"] = stage_index
            self.current_deployment["traffic_percentage"] = traffic_percentage
            
            # Route traffic to canary
            await self._update_traffic_routing(traffic_percentage)
            
            # Monitor metrics during stage
            metrics_healthy = await self._monitor_canary_metrics(traffic_percentage)
            
            if not metrics_healthy:
                await self._abort_canary_deployment()
                return
            
            # Wait for stage duration (shortened for demo)
            await asyncio.sleep(2)  # Shortened from 300 seconds
        
        # Deployment successful
        await self._complete_canary_deployment()
    
    async def _update_traffic_routing(self, percentage: int):
        print(f"Routing {percentage}% traffic to canary version")
        # Simulate load balancer update
        await asyncio.sleep(0.5)
    
    async def _monitor_canary_metrics(self, traffic_percentage: int) -> bool:
        print(f"Monitoring canary metrics at {traffic_percentage}% traffic...")
        
        # Simulate metric collection
        await asyncio.sleep(1)
        
        # Simulate metrics (normally from monitoring system)
        metrics = {
            "error_rate": 0.005,  # 0.5%
            "latency_p99": 450,   # 450ms
            "success_rate": 99.95  # 99.95%
        }
        
        # Evaluate against success criteria
        criteria = self.canary_config["success_criteria"]
        
        if metrics["error_rate"] > criteria["error_rate_threshold"]:
            print(f"❌ Error rate too high: {metrics['error_rate']}")
            return False
        
        if metrics["latency_p99"] > criteria["latency_p99_threshold"]:
            print(f"❌ Latency too high: {metrics['latency_p99']}ms")
            return False
        
        if metrics["success_rate"] < criteria["success_rate_threshold"]:
            print(f"❌ Success rate too low: {metrics['success_rate']}%")
            return False
        
        print(f"✅ Metrics healthy - Error: {metrics['error_rate']}%, Latency: {metrics['latency_p99']}ms")
        return True
    
    async def _abort_canary_deployment(self):
        print("🚨 Aborting canary deployment due to metric failures")
        self.current_deployment["status"] = "aborted"
        
        # Route all traffic back to stable version
        await self._update_traffic_routing(0)
        print("Rolled back to stable version")
    
    async def _complete_canary_deployment(self):
        print("✅ Canary deployment completed successfully")
        self.current_deployment["status"] = "completed"
        self.current_deployment["completed_at"] = datetime.now().isoformat()
    
    def get_canary_status(self) -> Dict:
        return self.current_deployment or {"status": "no_active_deployment"}
