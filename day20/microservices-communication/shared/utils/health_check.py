from typing import Dict, Any, List
import psutil
import time

class HealthChecker:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.start_time = time.time()

    def get_health_status(self) -> Dict[str, Any]:
        return {
            "service": self.service_name,
            "status": "healthy",
            "timestamp": time.time(),
            "uptime": time.time() - self.start_time,
            "system": self._get_system_health()
        }

    def _get_system_health(self) -> Dict[str, Any]:
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0
        }

    def check_dependencies(self, dependencies: List[str]) -> Dict[str, bool]:
        # In a real implementation, this would check actual service dependencies
        return {dep: True for dep in dependencies}
