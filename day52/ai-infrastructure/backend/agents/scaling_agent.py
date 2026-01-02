import asyncio
import asyncpg
from datetime import datetime, timedelta
import numpy as np

class PredictiveScalingAgent:
    def __init__(self, db_pool, forecaster):
        self.db_pool = db_pool
        self.forecaster = forecaster
        self.min_replicas = 1
        self.max_replicas = 10
        self.provision_time_seconds = 90
        self.scale_threshold = 0.75  # Scale at 75% predicted capacity
        
    async def get_recent_metrics(self, deployment: str, metric: str, minutes: int = 10):
        """Fetch recent metric values"""
        start_time = datetime.now() - timedelta(minutes=minutes)
        
        rows = await self.db_pool.fetch('''
            SELECT value FROM metrics
            WHERE metric_name = $1
            AND time >= $2
            ORDER BY time ASC
        ''', metric, start_time)
        
        return [float(row['value']) for row in rows]
    
    async def calculate_required_replicas(self, predicted_load: float, current_replicas: int) -> int:
        """Calculate required replicas based on predicted load"""
        # Assume each replica can handle 20% load
        required = int(np.ceil(predicted_load / 20.0))
        
        # Add 10% buffer
        required = int(required * 1.1)
        
        # Apply limits
        required = max(self.min_replicas, min(self.max_replicas, required))
        
        return required
    
    async def make_scaling_decision(self, deployment: str):
        """Make predictive scaling decision"""
        try:
            # Get recent CPU usage
            recent_cpu = await self.get_recent_metrics(deployment, 'cpu_usage_percent', 10)
            
            if len(recent_cpu) < 60:
                print(f"Insufficient data for {deployment}")
                return
            
            # Get prediction 15 minutes ahead
            predicted_cpu, conf_lower, conf_upper = await self.forecaster.predict(
                'cpu_usage_percent', recent_cpu
            )
            
            if predicted_cpu is None:
                return
            
            # Current state
            current_cpu = recent_cpu[-1]
            current_replicas = 3  # Simulate current replicas
            
            # Calculate required capacity
            required_replicas = await self.calculate_required_replicas(predicted_cpu, current_replicas)
            
            # Decide if scaling is needed
            if required_replicas > current_replicas:
                # Check if we need to scale now (spike imminent)
                time_to_spike = 15 * 60  # 15 minutes in seconds
                
                if time_to_spike <= self.provision_time_seconds + 30:
                    reason = f"Predicted CPU spike to {predicted_cpu:.1f}% in 15min (current: {current_cpu:.1f}%)"
                    
                    await self.execute_scaling(deployment, current_replicas, 
                                              required_replicas, reason, predicted_cpu)
                    
                    print(f"✅ Preemptive scale: {deployment} {current_replicas}→{required_replicas} replicas")
                    print(f"   Reason: {reason}")
            
            elif required_replicas < current_replicas and current_cpu < 30:
                # Scale down if predicted load is low
                reason = f"Predicted low CPU {predicted_cpu:.1f}% in 15min (current: {current_cpu:.1f}%)"
                
                await self.execute_scaling(deployment, current_replicas, 
                                          required_replicas, reason, predicted_cpu)
                
                print(f"📉 Scale down: {deployment} {current_replicas}→{required_replicas} replicas")
                
        except Exception as e:
            print(f"Error in scaling decision: {e}")
    
    async def execute_scaling(self, deployment: str, current: int, target: int, 
                            reason: str, predicted_load: float):
        """Record scaling decision"""
        await self.db_pool.execute('''
            INSERT INTO scaling_decisions 
            (timestamp, deployment, current_replicas, target_replicas, reason, predicted_load, executed)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''', datetime.now(), deployment, current, target, reason, predicted_load, True)

class IncidentResponseAgent:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        
    async def analyze_root_cause(self, anomaly_id: int):
        """Perform root cause analysis"""
        # Fetch anomaly details
        anomaly = await self.db_pool.fetchrow('''
            SELECT * FROM anomalies WHERE id = $1
        ''', anomaly_id)
        
        if not anomaly:
            return
        
        # Fetch related metrics around the same time
        related_metrics = await self.db_pool.fetch('''
            SELECT metric_name, value FROM metrics
            WHERE time BETWEEN $1 AND $2
            AND metric_name != $3
            ORDER BY time
        ''', anomaly['detected_at'] - timedelta(minutes=5),
             anomaly['detected_at'] + timedelta(minutes=1),
             anomaly['metric_name'])
        
        # Simple correlation analysis
        symptoms = {
            'primary': anomaly['metric_name'],
            'related': [r['metric_name'] for r in related_metrics if abs(float(r['value']) - anomaly['value']) > 50]
        }
        
        # Determine likely root cause
        root_causes = {
            'cpu_usage_percent': 'High CPU utilization - possible compute-intensive workload or inefficient code',
            'memory_usage_percent': 'Memory pressure - potential memory leak or large dataset processing',
            'network_bytes_sent': 'Network saturation - high traffic volume or DDoS attack',
        }
        
        root_cause = root_causes.get(anomaly['metric_name'], 'Unknown cause - requires investigation')
        
        # Suggested remediation
        remediation = self.suggest_remediation(anomaly['metric_name'])
        
        # Create incident
        incident_id = await self.db_pool.fetchval('''
            INSERT INTO incidents (created_at, title, symptoms, root_cause, remediation_actions, status)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        ''', datetime.now(),
             f"Anomaly in {anomaly['metric_name']}",
             str(symptoms),
             root_cause,
             str(remediation),
             'analyzing')
        
        print(f"🔍 Incident #{incident_id} created: {root_cause}")
        print(f"   Suggested actions: {', '.join(remediation)}")
        
        return incident_id
    
    def suggest_remediation(self, metric_name: str) -> list:
        """Suggest remediation actions"""
        remediation_map = {
            'cpu_usage_percent': [
                'Scale up deployment',
                'Check for inefficient queries',
                'Enable CPU throttling',
                'Review recent code changes'
            ],
            'memory_usage_percent': [
                'Increase memory limits',
                'Check for memory leaks',
                'Restart high-memory pods',
                'Enable memory profiling'
            ],
            'network_bytes_sent': [
                'Enable rate limiting',
                'Check for DDoS attack',
                'Scale network capacity',
                'Review outbound traffic patterns'
            ]
        }
        
        return remediation_map.get(metric_name, ['Manual investigation required'])
