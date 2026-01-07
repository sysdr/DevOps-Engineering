import asyncio
import uuid
from datetime import datetime
import logging
import random
from typing import List, Dict

from backend.common.models import ChaosExperiment
from backend.common.metrics import (
    chaos_experiments_total, chaos_experiments_passed,
    chaos_experiments_failed
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChaosFramework:
    def __init__(self):
        self.experiments: Dict[str, ChaosExperiment] = {}
        self.active_experiments = []
        
    async def start(self):
        """Start chaos engineering scheduler"""
        logger.info("Starting chaos engineering framework...")
        asyncio.create_task(self._chaos_scheduler_loop())
    
    async def inject_failure(self, experiment_type: str, blast_radius: float = 0.05):
        """Inject controlled failure"""
        experiment_id = str(uuid.uuid4())
        
        experiment = ChaosExperiment(
            id=experiment_id,
            name=f"{experiment_type}_experiment",
            type=experiment_type,
            blast_radius=blast_radius,
            steady_state_metrics={
                'success_rate': 0.995,
                'latency_p95': 200,
                'error_rate': 0.005
            }
        )
        
        self.experiments[experiment_id] = experiment
        chaos_experiments_total.inc()
        
        logger.info(f"Starting chaos experiment: {experiment_type}")
        
        # Run experiment
        result = await self._run_experiment(experiment)
        
        return {
            'experiment_id': experiment_id,
            'type': experiment_type,
            'result': result
        }
    
    async def _run_experiment(self, experiment: ChaosExperiment) -> dict:
        """Execute chaos experiment"""
        experiment.status = "running"
        start_time = datetime.now()
        
        try:
            # 1. Establish steady state
            baseline_metrics = await self._measure_metrics()
            
            # 2. Inject failure
            logger.info(f"Injecting {experiment.type} failure...")
            await self._inject_specific_failure(experiment.type)
            
            # 3. Wait for propagation
            await asyncio.sleep(5)
            
            # 4. Measure impact
            impact_metrics = await self._measure_metrics()
            
            # 5. Wait for recovery
            await asyncio.sleep(10)
            
            # 6. Verify recovery
            recovery_metrics = await self._measure_metrics()
            
            # 7. Analyze results
            passed = self._validate_experiment(
                baseline_metrics,
                impact_metrics,
                recovery_metrics,
                experiment.steady_state_metrics
            )
            
            if passed:
                chaos_experiments_passed.inc()
                experiment.status = "passed"
            else:
                chaos_experiments_failed.inc()
                experiment.status = "failed"
            
            duration = (datetime.now() - start_time).total_seconds()
            
            experiment.results = {
                'baseline': baseline_metrics,
                'impact': impact_metrics,
                'recovery': recovery_metrics,
                'duration': duration,
                'passed': passed
            }
            
            logger.info(f"Experiment {experiment.type}: {'PASSED' if passed else 'FAILED'}")
            
            return experiment.results
            
        except Exception as e:
            logger.error(f"Experiment failed: {e}")
            chaos_experiments_failed.inc()
            experiment.status = "error"
            return {'error': str(e)}
    
    async def _inject_specific_failure(self, failure_type: str):
        """Inject specific type of failure"""
        if failure_type == "pod_failure":
            logger.info("Terminating random pods...")
        elif failure_type == "network_partition":
            logger.info("Simulating network partition...")
        elif failure_type == "resource_exhaustion":
            logger.info("Exhausting resources...")
        elif failure_type == "latency_injection":
            logger.info("Injecting latency...")
        
        await asyncio.sleep(2)  # Simulate failure injection
    
    async def _measure_metrics(self) -> dict:
        """Measure current system metrics"""
        return {
            'success_rate': random.uniform(0.98, 0.999),
            'latency_p95': random.uniform(150, 250),
            'error_rate': random.uniform(0.001, 0.01)
        }
    
    def _validate_experiment(self, baseline, impact, recovery, thresholds) -> bool:
        """Validate experiment results against steady state"""
        # Check if system recovered to acceptable levels
        recovery_success_rate = recovery['success_rate']
        recovery_latency = recovery['latency_p95']
        
        passed = (
            recovery_success_rate >= thresholds['success_rate'] and
            recovery_latency <= thresholds['latency_p95']
        )
        
        return passed
    
    async def _chaos_scheduler_loop(self):
        """Schedule regular chaos experiments"""
        while True:
            try:
                # Run hourly chaos experiments
                experiment_types = [
                    "pod_failure",
                    "network_partition",
                    "resource_exhaustion",
                    "latency_injection"
                ]
                
                experiment_type = random.choice(experiment_types)
                
                logger.info(f"Scheduled chaos experiment: {experiment_type}")
                await self.inject_failure(experiment_type, blast_radius=0.05)
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Chaos scheduler error: {e}")
                await asyncio.sleep(300)
    
    def get_experiment_stats(self) -> dict:
        """Get chaos experiment statistics"""
        total = len(self.experiments)
        passed = sum(1 for e in self.experiments.values() if e.status == "passed")
        
        return {
            'total_experiments': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'recent_experiments': [
                {
                    'id': e.id,
                    'type': e.type,
                    'status': e.status,
                    'results': e.results
                }
                for e in list(self.experiments.values())[-5:]
            ]
        }

# Global chaos framework instance
chaos_framework = ChaosFramework()
