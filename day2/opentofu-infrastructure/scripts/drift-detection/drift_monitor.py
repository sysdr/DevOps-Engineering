#!/usr/bin/env python3

import asyncio
import aiohttp
import schedule
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DriftMonitor:
    def __init__(self, api_base_url="http://localhost:8000"):
        self.api_base_url = api_base_url
        self.environments = ["dev", "staging", "prod"]
    
    async def check_environment_drift(self, session, environment):
        """Check drift for a specific environment"""
        try:
            url = f"{self.api_base_url}/api/drift-detection/{environment}"
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("drift_detected"):
                        logger.warning(f"🚨 DRIFT DETECTED in {environment}!")
                        logger.warning(f"Changes: {result.get('changes', [])}")
                        await self.notify_drift_detected(environment, result)
                    else:
                        logger.info(f"✅ No drift detected in {environment}")
                    return result
                else:
                    logger.error(f"Failed to check drift for {environment}: {response.status}")
        except Exception as e:
            logger.error(f"Error checking drift for {environment}: {e}")
    
    async def notify_drift_detected(self, environment, drift_result):
        """Send notification when drift is detected"""
        logger.info(f"📧 Sending drift notification for {environment}")
        # In a real implementation, you would:
        # - Send email notifications
        # - Post to Slack/Teams
        # - Create JIRA tickets
        # - Send webhook notifications
    
    async def remediate_drift_if_safe(self, session, environment):
        """Automatically remediate drift if it's safe to do so"""
        try:
            url = f"{self.api_base_url}/api/drift-detection/remediate/{environment}"
            async with session.post(url) as response:
                if response.status == 200:
                    logger.info(f"🔧 Auto-remediation started for {environment}")
                else:
                    logger.error(f"Failed to start remediation for {environment}")
        except Exception as e:
            logger.error(f"Error starting remediation for {environment}: {e}")
    
    async def run_drift_check_cycle(self):
        """Run a complete drift check cycle for all environments"""
        logger.info("🔍 Starting drift detection cycle...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for env in self.environments:
                task = self.check_environment_drift(session, env)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for env, result in zip(self.environments, results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing {env}: {result}")
                elif isinstance(result, dict) and result.get("drift_detected"):
                    # Check if auto-remediation is enabled for this environment
                    if env == "dev":  # Only auto-remediate dev environment
                        await self.remediate_drift_if_safe(session, env)
        
        logger.info("✅ Drift detection cycle completed")

def run_scheduled_drift_check():
    """Wrapper function for scheduled execution"""
    monitor = DriftMonitor()
    asyncio.run(monitor.run_drift_check_cycle())

def main():
    logger.info("🚀 Starting OpenTofu Drift Monitor")
    
    # Schedule drift checks every 15 minutes
    schedule.every(15).minutes.do(run_scheduled_drift_check)
    
    # Run initial check
    run_scheduled_drift_check()
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute for scheduled tasks

if __name__ == "__main__":
    main()
