from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import hashlib

class DeviceStatus(str, Enum):
    PENDING = "pending"
    PROVISIONING = "provisioning"
    READY = "ready"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"

class EdgeDevice:
    def __init__(self, device_id: str, location: Dict, capabilities: List[str]):
        self.device_id = device_id
        self.location = location
        self.capabilities = capabilities
        self.status = DeviceStatus.PENDING
        self.current_model = None
        self.last_heartbeat = datetime.now()
        self.metrics = {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_percent": 0,
            "inference_count": 0,
            "inference_latency_ms": 0
        }
        self.created_at = datetime.now()
        
    def update_heartbeat(self, metrics: Dict):
        self.last_heartbeat = datetime.now()
        self.metrics.update(metrics)
        self._update_status()
        
    def _update_status(self):
        """Auto-transition based on metrics and heartbeat"""
        if (datetime.now() - self.last_heartbeat).seconds > 60:
            self.status = DeviceStatus.OFFLINE
        elif self.metrics["cpu_percent"] > 80 or self.metrics["memory_percent"] > 85:
            self.status = DeviceStatus.DEGRADED
        elif self.status == DeviceStatus.OFFLINE:
            # Recovered from offline
            self.status = DeviceStatus.READY
            
    def is_healthy(self) -> bool:
        return self.status in [DeviceStatus.READY, DeviceStatus.DEGRADED]
        
    def to_dict(self) -> Dict:
        return {
            "device_id": self.device_id,
            "location": self.location,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "current_model": self.current_model,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "metrics": self.metrics,
            "created_at": self.created_at.isoformat()
        }

class ModelVersion:
    def __init__(self, model_id: str, version: str, optimization: str):
        self.model_id = model_id
        self.version = version
        self.optimization = optimization  # full, quantized, ultra-light
        self.size_bytes = self._calculate_size()
        self.accuracy = self._calculate_accuracy()
        self.deployed_count = 0
        self.created_at = datetime.now()
        
    def _calculate_size(self) -> int:
        """Simulate model sizes based on optimization"""
        sizes = {
            "full": 150 * 1024 * 1024,  # 150MB
            "quantized": 40 * 1024 * 1024,  # 40MB
            "ultra-light": 10 * 1024 * 1024  # 10MB
        }
        return sizes.get(self.optimization, sizes["full"])
        
    def _calculate_accuracy(self) -> float:
        """Simulate accuracy trade-offs"""
        accuracies = {
            "full": 0.95,
            "quantized": 0.93,
            "ultra-light": 0.89
        }
        return accuracies.get(self.optimization, 0.95)
        
    def to_dict(self) -> Dict:
        return {
            "model_id": self.model_id,
            "version": self.version,
            "optimization": self.optimization,
            "size_mb": round(self.size_bytes / (1024 * 1024), 2),
            "accuracy": self.accuracy,
            "deployed_count": self.deployed_count,
            "created_at": self.created_at.isoformat()
        }
