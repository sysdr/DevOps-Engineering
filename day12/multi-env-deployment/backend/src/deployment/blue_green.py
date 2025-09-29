import asyncio
from datetime import datetime
from typing import Dict

class BlueGreenDeployer:
    def __init__(self):
        self.environments = {
            "blue": {"status": "active", "version": "1.2.3", "traffic": 100},
            "green": {"status": "inactive", "version": None, "traffic": 0}
        }
    
    async def execute_deployment(self, deployment_id: str):
        # Determine target environment
        active_env = "blue" if self.environments["blue"]["status"] == "active" else "green"
        target_env = "green" if active_env == "blue" else "blue"
        
        print(f"Starting blue-green deployment to {target_env} environment")
        
        # Deploy to inactive environment
        await self._deploy_to_environment(target_env, "1.2.4")
        
        # Health check
        if await self._health_check(target_env):
            # Switch traffic
            await self._switch_traffic(active_env, target_env)
            print(f"Traffic switched from {active_env} to {target_env}")
        else:
            print(f"Health check failed for {target_env}, aborting deployment")
    
    async def _deploy_to_environment(self, environment: str, version: str):
        self.environments[environment]["status"] = "deploying"
        self.environments[environment]["version"] = version
        
        # Simulate deployment time
        await asyncio.sleep(3)
        
        self.environments[environment]["status"] = "deployed"
    
    async def _health_check(self, environment: str) -> bool:
        print(f"Running health checks on {environment}")
        await asyncio.sleep(1)
        return True  # 99% success rate for demo
    
    async def _switch_traffic(self, from_env: str, to_env: str):
        # Gradual traffic switch for safety
        for percentage in [10, 25, 50, 75, 100]:
            self.environments[from_env]["traffic"] = 100 - percentage
            self.environments[to_env]["traffic"] = percentage
            
            print(f"Traffic: {from_env}({100-percentage}%) -> {to_env}({percentage}%)")
            await asyncio.sleep(0.5)
        
        # Update status
        self.environments[from_env]["status"] = "inactive"
        self.environments[to_env]["status"] = "active"
    
    def get_environment_status(self) -> Dict:
        return self.environments
