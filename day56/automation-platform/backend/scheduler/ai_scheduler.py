import asyncio
from datetime import datetime, timedelta
import logging
import random
from typing import List, Dict
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIWorkflowScheduler:
    def __init__(self):
        self.scheduled_workflows = []
        self.execution_history = []
        self.resource_predictions = {}
        
    async def start(self):
        """Start scheduler optimization loop"""
        logger.info("Starting AI-powered workflow scheduler...")
        asyncio.create_task(self._optimization_loop())
        asyncio.create_task(self._prediction_loop())
    
    def predict_optimal_time(self, workflow_name: str, workflow_data: dict) -> dict:
        """Predict optimal execution time using ML-like logic"""
        
        # Get historical execution data
        historical_durations = [
            h['duration'] for h in self.execution_history
            if h.get('workflow_name') == workflow_name
        ]
        
        if historical_durations:
            predicted_duration = np.mean(historical_durations)
            confidence = min(len(historical_durations) / 10.0, 1.0)
        else:
            predicted_duration = 300  # Default 5 minutes
            confidence = 0.1
        
        # Predict resource availability
        current_load = self._get_current_cluster_load()
        
        # Calculate optimal start time
        if current_load > 0.8:
            # High load - schedule for later
            optimal_start = datetime.now() + timedelta(minutes=15)
        else:
            # Low load - schedule immediately
            optimal_start = datetime.now()
        
        return {
            'predicted_duration': predicted_duration,
            'confidence': confidence,
            'optimal_start_time': optimal_start.isoformat(),
            'current_load': current_load,
            'recommendation': 'immediate' if current_load < 0.8 else 'delayed'
        }
    
    def _get_current_cluster_load(self) -> float:
        """Get current cluster resource utilization"""
        # Simulate cluster load (0.0 to 1.0)
        base_load = 0.4
        variation = random.uniform(-0.2, 0.3)
        return max(0.0, min(1.0, base_load + variation))
    
    async def _optimization_loop(self):
        """Continuously optimize workflow scheduling"""
        while True:
            try:
                # Optimize pending workflows
                if self.scheduled_workflows:
                    logger.info(f"Optimizing {len(self.scheduled_workflows)} scheduled workflows")
                    
                    # Sort by priority and resource requirements
                    self.scheduled_workflows.sort(
                        key=lambda w: (w.get('priority', 0), w.get('resources', 0)),
                        reverse=True
                    )
                
                await asyncio.sleep(30)  # Optimize every 30 seconds
                
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                await asyncio.sleep(10)
    
    async def _prediction_loop(self):
        """Update resource predictions"""
        while True:
            try:
                # Generate predictions for next hour
                for minutes_ahead in range(0, 60, 15):
                    timestamp = datetime.now() + timedelta(minutes=minutes_ahead)
                    
                    # Simple sinusoidal prediction pattern
                    hour = timestamp.hour
                    base_load = 0.5
                    hourly_pattern = 0.3 * np.sin((hour - 6) * np.pi / 12)
                    predicted_load = base_load + hourly_pattern
                    
                    self.resource_predictions[timestamp.isoformat()] = {
                        'cpu_load': max(0.1, min(0.9, predicted_load)),
                        'memory_available': random.uniform(0.3, 0.8),
                        'confidence': 0.85
                    }
                
                await asyncio.sleep(300)  # Update predictions every 5 minutes
                
            except Exception as e:
                logger.error(f"Prediction loop error: {e}")
                await asyncio.sleep(60)
    
    def get_scheduler_stats(self) -> dict:
        """Get scheduler statistics"""
        return {
            'scheduled_workflows': len(self.scheduled_workflows),
            'current_load': self._get_current_cluster_load(),
            'predictions_available': len(self.resource_predictions),
            'optimization_efficiency': random.uniform(0.88, 0.95)  # Simulated metric
        }

# Global scheduler instance
scheduler = AIWorkflowScheduler()
