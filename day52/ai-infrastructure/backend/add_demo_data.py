#!/usr/bin/env python3
"""Add demo data to the database for dashboard display"""
import asyncio
import asyncpg
from datetime import datetime, timedelta
import json
import random

async def add_demo_data():
    """Add demo anomalies, incidents, and scaling decisions"""
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        user='postgres',
        password='postgres',
        database='postgres'
    )
    
    try:
        # Add demo anomalies (within last 24 hours)
        print("Adding demo anomalies...")
        now = datetime.now()
        anomaly_times = [
            now - timedelta(hours=2),
            now - timedelta(hours=5),
            now - timedelta(hours=12),
            now - timedelta(hours=18),
            now - timedelta(hours=23),
        ]
        
        metrics = ['cpu_usage_percent', 'memory_usage_percent', 'network_bytes_sent']
        severities = ['high', 'medium', 'high', 'medium', 'medium']
        
        for i, anomaly_time in enumerate(anomaly_times):
            metric = metrics[i % len(metrics)]
            base_value = random.uniform(40, 60) if 'percent' in metric else random.uniform(1000000, 5000000)
            anomaly_value = base_value * (1.5 if severities[i] == 'high' else 1.3)
            
            await conn.execute('''
                INSERT INTO anomalies (detected_at, metric_name, value, expected_value, severity, detector_votes)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', 
            anomaly_time,
            metric,
            anomaly_value,
            base_value,
            severities[i],
            json.dumps({'statistical': True, 'isolation': severities[i] == 'high', 'rate_change': True})
            )
        
        # Add demo incidents (some active, some resolved)
        print("Adding demo incidents...")
        
        # Active incident
        await conn.execute('''
            INSERT INTO incidents (created_at, title, symptoms, root_cause, remediation_actions, status)
            VALUES ($1, $2, $3, $4, $5, $6)
        ''',
        now - timedelta(hours=3),
        'High CPU Usage on node-2',
        json.dumps({
            'metrics': ['cpu_usage_percent'],
            'nodes': ['node-2'],
            'description': 'CPU usage spiked to 85% sustained over 10 minutes'
        }),
        'Memory leak in application service causing CPU throttling',
        json.dumps([
            'Increased replicas of application service',
            'Restarted affected pods',
            'Monitoring for recurrence'
        ]),
        'investigating'
        )
        
        # Resolved incident (recent)
        await conn.execute('''
            INSERT INTO incidents (created_at, title, symptoms, root_cause, remediation_actions, status, resolved_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''',
        now - timedelta(hours=8),
        'Network Latency Spike',
        json.dumps({
            'metrics': ['network_bytes_sent'],
            'nodes': ['node-1', 'node-3'],
            'description': 'Network throughput dropped by 40%'
        }),
        'Network interface driver issue - updated driver',
        json.dumps([
            'Updated network driver on affected nodes',
            'Restarted network services'
        ]),
        'resolved',
        now - timedelta(hours=6)
        )
        
        # Another active incident
        await conn.execute('''
            INSERT INTO incidents (created_at, title, symptoms, root_cause, remediation_actions, status)
            VALUES ($1, $2, $3, $4, $5, $6)
        ''',
        now - timedelta(hours=1),
        'Memory Usage Anomaly Detected',
        json.dumps({
            'metrics': ['memory_usage_percent'],
            'nodes': ['node-4'],
            'description': 'Memory usage exceeded expected threshold'
        }),
        None,  # Root cause still being investigated
        None,
        'open'
        )
        
        # Add demo scaling decisions (within last 24 hours)
        print("Adding demo scaling decisions...")
        scaling_times = [
            now - timedelta(hours=1, minutes=30),
            now - timedelta(hours=4),
            now - timedelta(hours=10),
            now - timedelta(hours=20),
        ]
        
        deployments = ['nginx', 'api-service', 'worker-pool', 'api-service']
        current_replicas = [3, 5, 2, 5]
        target_replicas = [5, 8, 4, 8]
        reasons = [
            'Predicted CPU load increase requires scaling up',
            'Memory usage prediction indicates need for more replicas',
            'Traffic pattern suggests proactive scaling',
            'ML model predicts load spike in next 15 minutes'
        ]
        executed = [True, True, False, True]
        
        for i, scaling_time in enumerate(scaling_times):
            await conn.execute('''
                INSERT INTO scaling_decisions (timestamp, deployment, current_replicas, target_replicas, reason, predicted_load, executed)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''',
            scaling_time,
            deployments[i],
            current_replicas[i],
            target_replicas[i],
            reasons[i],
            random.uniform(70, 90),
            executed[i]
            )
        
        print("✅ Demo data added successfully!")
        print(f"   - 5 anomalies added (last 24h)")
        print(f"   - 3 incidents added (2 active, 1 resolved)")
        print(f"   - 4 scaling decisions added (last 24h)")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(add_demo_data())

