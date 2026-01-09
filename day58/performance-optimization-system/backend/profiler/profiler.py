import asyncio
import time
import psutil
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)

class PerformanceProfiler:
    def __init__(self, metrics_collector):
        self.metrics = metrics_collector
        self.samples = deque(maxlen=1000)
        self.hotspots = {}
        self.sample_interval = 0.01  # 10ms
        self.aggregate_interval = 60  # 1 minute
        self.last_aggregate = time.time()
        self.cpu_threshold = 80.0
        self.running = False
        
    async def run(self):
        """Main profiler loop"""
        self.running = True
        logger.info("Performance Profiler started")
        
        while self.running:
            try:
                await self.sample_performance()
                
                # Aggregate samples periodically
                if time.time() - self.last_aggregate > self.aggregate_interval:
                    await self.aggregate_samples()
                    self.last_aggregate = time.time()
                
                await asyncio.sleep(self.sample_interval)
            except Exception as e:
                logger.error(f"Profiler error: {e}")
                await asyncio.sleep(1)
    
    async def sample_performance(self):
        """Capture performance sample"""
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        
        sample = {
            'timestamp': time.time(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': memory.used / (1024**3),
            'load_avg': psutil.getloadavg()[0]
        }
        
        self.samples.append(sample)
        self.metrics.record_sample(sample)
        
        # Detect high CPU usage
        if cpu_percent > self.cpu_threshold:
            await self.identify_hotspots()
    
    async def identify_hotspots(self):
        """Identify CPU hotspots"""
        # Simulate hotspot detection (in production, use py-spy or similar)
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                if proc.info['cpu_percent'] > 5.0:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.info['cpu_percent']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if processes:
            top_process = max(processes, key=lambda x: x['cpu_percent'])
            logger.warning(f"Hotspot detected: {top_process['name']} ({top_process['cpu_percent']:.1f}% CPU)")
            self.hotspots[top_process['name']] = top_process['cpu_percent']
    
    async def aggregate_samples(self):
        """Aggregate samples into summary statistics"""
        if not self.samples:
            return
        
        cpu_values = [s['cpu_percent'] for s in self.samples]
        memory_values = [s['memory_percent'] for s in self.samples]
        
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu_avg': statistics.mean(cpu_values),
            'cpu_p50': statistics.median(cpu_values),
            'cpu_p95': statistics.quantiles(cpu_values, n=20)[18] if len(cpu_values) > 20 else max(cpu_values),
            'memory_avg': statistics.mean(memory_values),
            'hotspots': dict(self.hotspots)
        }
        
        self.metrics.record_aggregate(summary)
        logger.info(f"Profile aggregate: CPU={summary['cpu_avg']:.1f}%, Memory={summary['memory_avg']:.1f}%")
    
    def get_flame_graph_data(self):
        """Generate flame graph data"""
        return {
            'hotspots': self.hotspots,
            'samples': list(self.samples)[-100:],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def is_healthy(self):
        return self.running
