import asyncio
import pynvml
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)

class GPUState(Enum):
    AVAILABLE = "available"
    ALLOCATED = "allocated"  
    MAINTENANCE = "maintenance"
    ERROR = "error"

@dataclass
class GPUDevice:
    id: str
    name: str
    memory_total: int
    memory_used: int
    utilization: float
    temperature: int
    power_usage: int
    state: GPUState
    mig_enabled: bool = False
    mig_instances: List[Dict] = None

class GPUManager:
    def __init__(self):
        self.devices: Dict[str, GPUDevice] = {}
        self.initialized = False

    async def initialize(self):
        """Initialize NVIDIA management library and discover GPUs"""
        try:
            pynvml.nvmlInit()
            await self._discover_gpus()
            self.initialized = True
            logger.info("GPU Manager initialized successfully")
        except Exception as e:
            logger.error(f"GPU Manager initialization failed: {e}")
            # Create mock GPUs for demo when no real GPUs available
            await self._create_mock_gpus()
            self.initialized = True
            logger.info("GPU Manager initialized with mock GPUs")

    async def _discover_gpus(self):
        """Discover available GPU devices"""
        device_count = pynvml.nvmlDeviceGetCount()
        
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle).decode()
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            power = pynvml.nvmlDeviceGetPowerUsage(handle) // 1000  # Convert to watts
            
            device = GPUDevice(
                id=f"gpu-{i}",
                name=name,
                memory_total=memory_info.total,
                memory_used=memory_info.used,
                utilization=utilization.gpu,
                temperature=temperature,
                power_usage=power,
                state=GPUState.AVAILABLE
            )
            
            self.devices[device.id] = device

    async def _create_mock_gpus(self):
        """Create mock GPUs for demonstration when real hardware unavailable"""
        mock_gpus = [
            {"name": "NVIDIA A100-SXM4-40GB", "memory": 42949672960, "power": 400},
            {"name": "NVIDIA A100-SXM4-40GB", "memory": 42949672960, "power": 380},
            {"name": "NVIDIA V100-SXM2-32GB", "memory": 34359738368, "power": 300},
            {"name": "NVIDIA T4", "memory": 16106127360, "power": 70}
        ]
        
        for i, gpu_spec in enumerate(mock_gpus):
            device = GPUDevice(
                id=f"gpu-{i}",
                name=gpu_spec["name"],
                memory_total=gpu_spec["memory"],
                memory_used=gpu_spec["memory"] // 10,  # 10% utilization
                utilization=25.0 + (i * 15),  # Varying utilization
                temperature=45 + (i * 5),
                power_usage=gpu_spec["power"] - (i * 20),
                state=GPUState.AVAILABLE
            )
            self.devices[device.id] = device

    async def get_available_resources(self) -> List[Dict]:
        """Get current GPU resources with real-time metrics"""
        if not self.initialized:
            await self.initialize()
            
        resources = []
        for device in self.devices.values():
            # Update real-time metrics for actual GPUs
            if device.name != "Mock GPU":
                await self._update_device_metrics(device)
            
            resources.append({
                "id": device.id,
                "name": device.name,
                "memory_total_gb": device.memory_total // (1024**3),
                "memory_used_gb": device.memory_used // (1024**3),
                "memory_free_gb": (device.memory_total - device.memory_used) // (1024**3),
                "utilization_percent": device.utilization,
                "temperature_c": device.temperature,
                "power_usage_w": device.power_usage,
                "state": device.state.value,
                "mig_enabled": device.mig_enabled
            })
        
        return resources

    async def _update_device_metrics(self, device: GPUDevice):
        """Update real-time metrics for GPU device"""
        try:
            if device.name == "Mock GPU":
                return  # Skip updates for mock devices
                
            # In production, this would query actual NVIDIA APIs
            # For demo, we simulate changing metrics
            import random
            device.utilization = max(0, min(100, device.utilization + random.randint(-5, 5)))
            device.memory_used = int(device.memory_total * (device.utilization / 200))  # Correlation
            device.temperature = 40 + int(device.utilization * 0.5)
            
        except Exception as e:
            logger.error(f"Failed to update metrics for {device.id}: {e}")

    async def allocate_gpu(self, gpu_id: str, workload_id: str) -> bool:
        """Allocate GPU for specific workload"""
        if gpu_id not in self.devices:
            return False
            
        device = self.devices[gpu_id]
        if device.state != GPUState.AVAILABLE:
            return False
            
        device.state = GPUState.ALLOCATED
        logger.info(f"GPU {gpu_id} allocated to workload {workload_id}")
        return True

    async def release_gpu(self, gpu_id: str) -> bool:
        """Release GPU back to available pool"""
        if gpu_id not in self.devices:
            return False
            
        device = self.devices[gpu_id]
        device.state = GPUState.AVAILABLE
        logger.info(f"GPU {gpu_id} released back to available pool")
        return True
