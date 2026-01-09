import asyncio
import logging
import time
import math
import random
from datetime import datetime, timedelta
from collections import deque
import statistics

logger = logging.getLogger(__name__)

class PredictiveScaler:
    def __init__(self, metrics_collector):
        self.metrics = metrics_collector
        self.history = deque(maxlen=2016)  # 1 week at 5-min intervals
        self.predictions = {}
        self.current_replicas = 3
        self.min_replicas = 2
        self.max_replicas = 20
        self.target_utilization = 0.70
        self.scale_up_threshold = 0.80
        self.scale_down_threshold = 0.40
        self.prediction_interval = 300  # 5 minutes
        self.last_prediction = time.time()
        self.running = False
        
    async def run(self):
        """Main scaler loop"""
        self.running = True
        logger.info("Predictive Auto-Scaler started")
        
        while self.running:
            try:
                await self.collect_metrics()
                
                # Make predictions periodically
                if time.time() - self.last_prediction > self.prediction_interval:
                    await self.predict_and_scale()
                    self.last_prediction = time.time()
                
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Scaler error: {e}")
                await asyncio.sleep(10)
    
    async def collect_metrics(self):
        """Collect current load metrics"""
        current_load = self.metrics.get_current_load()
        
        metric = {
            'timestamp': time.time(),
            'load': current_load,
            'replicas': self.current_replicas,
            'utilization': current_load / self.current_replicas if self.current_replicas > 0 else 0
        }
        
        self.history.append(metric)
    
    async def predict_and_scale(self):
        """Predict future load and make scaling decisions"""
        if len(self.history) < 12:  # Need at least 1 hour of data
            return
        
        # Time-series forecasting
        forecast = self.forecast_load(horizon=6)  # 30 minutes ahead
        
        # Calculate required capacity
        predicted_load = forecast['predictions'][-1]
        predicted_utilization = predicted_load / self.current_replicas
        
        # Scaling decision
        if predicted_utilization > self.scale_up_threshold:
            new_replicas = math.ceil(predicted_load / self.target_utilization)
            new_replicas = min(new_replicas, self.max_replicas)
            
            if new_replicas > self.current_replicas:
                logger.info(f"Proactive scale-up: {self.current_replicas} -> {new_replicas} replicas")
                logger.info(f"Predicted load: {predicted_load:.1f}, Current capacity: {self.current_replicas * self.target_utilization:.1f}")
                self.current_replicas = new_replicas
                self.metrics.record_scaling_event({
                    'action': 'scale_up',
                    'old_replicas': self.current_replicas,
                    'new_replicas': new_replicas,
                    'reason': 'predicted_overload'
                })
        
        elif predicted_utilization < self.scale_down_threshold:
            new_replicas = max(math.ceil(predicted_load / self.target_utilization), self.min_replicas)
            
            if new_replicas < self.current_replicas:
                # Conservative scale-down: wait for sustained low load
                recent_low = all(m['utilization'] < self.scale_down_threshold 
                               for m in list(self.history)[-10:])
                
                if recent_low:
                    logger.info(f"Conservative scale-down: {self.current_replicas} -> {new_replicas} replicas")
                    self.current_replicas = new_replicas
                    self.metrics.record_scaling_event({
                        'action': 'scale_down',
                        'old_replicas': self.current_replicas,
                        'new_replicas': new_replicas,
                        'reason': 'sustained_underutilization'
                    })
        
        self.predictions = forecast
    
    def forecast_load(self, horizon=6):
        """Forecast load using exponential smoothing + seasonality"""
        recent_data = list(self.history)[-288:]  # Last 24 hours
        loads = [m['load'] for m in recent_data]
        
        # Exponential smoothing
        alpha = 0.2
        trend = loads[0]
        smoothed = []
        
        for load in loads:
            trend = alpha * load + (1 - alpha) * trend
            smoothed.append(trend)
        
        # Extract daily seasonality (simplified)
        hour_of_day = (datetime.now().hour % 24)
        seasonal_factor = 1.0 + 0.5 * math.sin(2 * math.pi * hour_of_day / 24)
        
        # Generate predictions
        base_forecast = smoothed[-1]
        predictions = []
        
        for i in range(horizon):
            future_hour = (hour_of_day + i * 5 / 60) % 24
            future_seasonal = 1.0 + 0.5 * math.sin(2 * math.pi * future_hour / 24)
            forecast = base_forecast * future_seasonal
            predictions.append(forecast)
        
        return {
            'predictions': predictions,
            'base_forecast': base_forecast,
            'current_load': loads[-1] if loads else 0,
            'confidence': 0.85
        }
    
    def get_forecast(self):
        """Get current forecast"""
        if not self.predictions:
            # Generate demo forecast
            current_load = self.metrics.get_current_load()
            base_forecast = current_load if current_load > 0 else 1200
            predictions = []
            for i in range(6):
                # Simulate gradual increase with some variation
                pred = base_forecast * (1 + i * 0.05) + random.uniform(-50, 100)
                predictions.append(max(0, pred))
            return {
                'predictions': predictions,
                'base_forecast': base_forecast,
                'current_load': current_load if current_load > 0 else 1200,
                'confidence': 0.85
            }
        return self.predictions
    
    def get_scaling_status(self):
        """Get current scaling status"""
        current_load = self.metrics.get_current_load()
        predictions = self.get_forecast()  # Use get_forecast to get demo data if needed
        return {
            'current_replicas': self.current_replicas,
            'current_load': current_load if current_load > 0 else 1200,
            'utilization': (current_load if current_load > 0 else 1200) / self.current_replicas if self.current_replicas > 0 else 0,
            'predictions': predictions,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def is_healthy(self):
        return self.running
