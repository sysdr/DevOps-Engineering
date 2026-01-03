from typing import Dict, List, Optional
import asyncio
from datetime import datetime
import random
import hashlib

class EdgeController:
    def __init__(self):
        self.devices: Dict = {}
        self.models: Dict = {}
        self.sync_queue: List = []
        self.deployment_history: List = []
        
    def register_device(self, location: Dict, capabilities: List[str]) -> str:
        """Register new edge device"""
        device_id = f"edge-{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        
        from models.edge_device import EdgeDevice, DeviceStatus
        device = EdgeDevice(device_id, location, capabilities)
        device.status = DeviceStatus.PROVISIONING
        self.devices[device_id] = device
        
        # Simulate provisioning (will be done asynchronously if called from async context)
        # For synchronous calls, status will be updated later when async context is available
        
        return device_id
        
    async def _provision_device(self, device_id: str):
        """Simulate device provisioning process"""
        await asyncio.sleep(2)  # Simulate K3s installation
        if device_id in self.devices:
            from models.edge_device import DeviceStatus
            self.devices[device_id].status = DeviceStatus.READY
            
    def process_heartbeat(self, device_id: str, metrics: Dict) -> Dict:
        """Process device heartbeat and update status"""
        if device_id not in self.devices:
            return {"error": "Device not found"}
            
        device = self.devices[device_id]
        device.update_heartbeat(metrics)
        
        return {
            "status": "ok",
            "device_status": device.status.value,
            "instructions": self._get_device_instructions(device)
        }
        
    def _get_device_instructions(self, device) -> Dict:
        """Generate instructions for edge device"""
        instructions = {"sync_interval": 30}
        
        # Adjust based on status
        if device.status.value == "degraded":
            instructions["sync_interval"] = 60  # Reduce frequency
            instructions["warning"] = "High resource usage detected"
            
        return instructions
        
    def deploy_model(self, model_id: str, version: str, 
                    optimization: str, selector: Dict) -> Dict:
        """Deploy model to matching devices"""
        from models.edge_device import ModelVersion
        
        model_key = f"{model_id}-{version}"
        if model_key not in self.models:
            self.models[model_key] = ModelVersion(model_id, version, optimization)
            
        # Select devices based on selector
        target_devices = self._select_devices(selector)
        
        deployment_id = hashlib.md5(f"{model_key}{datetime.now()}".encode()).hexdigest()[:8]
        
        deployment = {
            "deployment_id": deployment_id,
            "model_id": model_id,
            "version": version,
            "optimization": optimization,
            "target_devices": [d.device_id for d in target_devices],
            "status": "in_progress",
            "started_at": datetime.now().isoformat()
        }
        
        self.deployment_history.append(deployment)
        
        # Update devices
        for device in target_devices:
            device.current_model = model_key
            self.models[model_key].deployed_count += 1
            
        return deployment
        
    def _select_devices(self, selector: Dict) -> List:
        """Select devices matching selector criteria"""
        selected = []
        for device in self.devices.values():
            if device.is_healthy():
                # Check capabilities
                if "gpu" in selector:
                    if selector["gpu"] and "gpu" in device.capabilities:
                        selected.append(device)
                    elif not selector["gpu"] and "gpu" not in device.capabilities:
                        selected.append(device)
                else:
                    selected.append(device)
                    
        return selected
        
    def get_fleet_status(self) -> Dict:
        """Get overall fleet status"""
        total = len(self.devices)
        status_counts = {}
        
        for device in self.devices.values():
            status = device.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
        return {
            "total_devices": total,
            "status_breakdown": status_counts,
            "models_deployed": len(self.models),
            "total_deployments": len(self.deployment_history)
        }
        
    def get_sync_metrics(self) -> Dict:
        """Calculate synchronization metrics"""
        total_bandwidth = sum(
            d.metrics.get("bandwidth_mbps", 0) 
            for d in self.devices.values()
        )
        
        avg_latency = sum(
            d.metrics.get("sync_latency_ms", 0) 
            for d in self.devices.values()
        ) / max(len(self.devices), 1)
        
        return {
            "total_bandwidth_mbps": round(total_bandwidth, 2),
            "avg_sync_latency_ms": round(avg_latency, 2),
            "sync_queue_size": len(self.sync_queue)
        }
