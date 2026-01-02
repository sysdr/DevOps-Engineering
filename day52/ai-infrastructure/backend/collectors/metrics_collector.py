import asyncio
import asyncpg
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
import random
import math

class MetricsCollector:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.collection_interval = 10  # seconds
        
    async def simulate_node_metrics(self, node_name: str) -> Dict:
        """Simulate realistic node metrics with patterns"""
        hour = datetime.now().hour
        minute = datetime.now().minute
        
        # Daily pattern: higher load during business hours (9-17)
        base_cpu = 30 + (30 * math.sin((hour - 6) * math.pi / 12))
        base_cpu = max(10, min(80, base_cpu))
        
        # Add weekly pattern (higher on weekdays)
        day_of_week = datetime.now().weekday()
        if day_of_week >= 5:  # Weekend
            base_cpu *= 0.6
            
        # Add randomness
        cpu_usage = base_cpu + random.uniform(-5, 5)
        
        # Memory follows similar pattern but slower
        memory_usage = 40 + (20 * math.sin((hour - 3) * math.pi / 12)) + random.uniform(-3, 3)
        
        # Network I/O correlates with CPU
        network_bytes = int(cpu_usage * 1000000)
        
        return {
            'cpu_usage_percent': round(cpu_usage, 2),
            'memory_usage_percent': round(memory_usage, 2),
            'network_bytes_sent': network_bytes,
            'network_bytes_recv': int(network_bytes * 0.8),
            'disk_io_read': random.randint(1000, 50000),
            'disk_io_write': random.randint(500, 30000),
            'pod_count': random.randint(10, 50)
        }
    
    async def collect_and_store(self):
        """Collect metrics from all nodes and store"""
        nodes = [f'node-{i}' for i in range(1, 6)]  # 5 nodes
        
        while True:
            try:
                timestamp = datetime.now()
                
                for node in nodes:
                    metrics = await self.simulate_node_metrics(node)
                    
                    # Store each metric
                    for metric_name, value in metrics.items():
                        await self.db_pool.execute('''
                            INSERT INTO metrics (time, node_name, metric_name, value, labels)
                            VALUES ($1, $2, $3, $4, $5)
                        ''', timestamp, node, metric_name, value, json.dumps({'node': node}))
                
                print(f"[{timestamp}] Collected metrics from {len(nodes)} nodes")
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                print(f"Error collecting metrics: {e}")
                await asyncio.sleep(5)

async def start_collector():
    db_pool = await asyncpg.create_pool(
        host='localhost',
        port=5433,
        user='postgres',
        password='postgres',
        database='postgres',
        min_size=2,
        max_size=10
    )
    
    collector = MetricsCollector(db_pool)
    await collector.collect_and_store()

if __name__ == '__main__':
    asyncio.run(start_collector())
