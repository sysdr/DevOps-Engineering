import psutil
import time
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Monitor system resources"""
    
    @staticmethod
    def get_cpu_usage() -> float:
        """Get CPU utilization percentage"""
        return psutil.cpu_percent(interval=0.1)
    
    @staticmethod
    def get_memory_usage() -> Dict:
        """Get memory usage statistics"""
        mem = psutil.virtual_memory()
        return {
            'total': mem.total / (1024**3),  # GB
            'available': mem.available / (1024**3),
            'used': mem.used / (1024**3),
            'percent': mem.percent
        }
    
    @staticmethod
    def get_disk_usage() -> Dict:
        """Get disk usage statistics"""
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total / (1024**3),
            'used': disk.used / (1024**3),
            'free': disk.free / (1024**3),
            'percent': disk.percent
        }
    
    @staticmethod
    def get_system_metrics() -> Dict:
        """Get all system metrics"""
        return {
            'cpu': SystemMonitor.get_cpu_usage(),
            'memory': SystemMonitor.get_memory_usage(),
            'disk': SystemMonitor.get_disk_usage(),
            'timestamp': time.time()
        }
