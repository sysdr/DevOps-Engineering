import asyncio
import aiohttp
import random
import time
from datetime import datetime
from typing import Dict
import hashlib

class EdgeAgent:
    def __init__(self, control_plane_url: str, location: Dict, capabilities: list):
        self.control_plane_url = control_plane_url
        self.location = location
        self.capabilities = capabilities
        self.device_id = None
        self.current_model = None
        self.inference_cache = {}
        self.data_buffer = []
        self.running = False
        
    async def start(self):
        """Start edge agent"""
        self.running = True
        
        # Register with control plane
        await self.register()
        
        # Start background tasks
        tasks = [
            self.heartbeat_loop(),
            self.inference_simulator(),
            self.data_sync_loop()
        ]
        await asyncio.gather(*tasks)
        
    async def register(self):
        """Register with control plane"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "location": self.location,
                "capabilities": self.capabilities
            }
            async with session.post(
                f"{self.control_plane_url}/api/devices/register",
                json=payload
            ) as response:
                result = await response.json()
                self.device_id = result["device_id"]
                print(f"Registered as {self.device_id}")
                
    async def heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.running:
            metrics = self.collect_metrics()
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "device_id": self.device_id,
                    "metrics": metrics
                }
                try:
                    async with session.post(
                        f"{self.control_plane_url}/api/devices/heartbeat",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        result = await response.json()
                        print(f"[{self.device_id}] Heartbeat sent - Status: {result.get('device_status')}")
                except Exception as e:
                    print(f"[{self.device_id}] Heartbeat failed (autonomous mode): {e}")
                    
            await asyncio.sleep(30)
            
    def collect_metrics(self) -> Dict:
        """Collect device metrics"""
        return {
            "cpu_percent": random.uniform(20, 85),
            "memory_percent": random.uniform(30, 75),
            "disk_percent": random.uniform(40, 70),
            "inference_count": len(self.inference_cache),
            "inference_latency_ms": random.uniform(15, 45),
            "bandwidth_mbps": random.uniform(10, 100),
            "sync_latency_ms": random.uniform(50, 150)
        }
        
    async def inference_simulator(self):
        """Simulate AI inference requests"""
        await asyncio.sleep(5)  # Wait for registration
        
        while self.running:
            # Simulate inference request
            input_hash = hashlib.md5(
                f"{random.randint(1, 100)}{time.time()}".encode()
            ).hexdigest()
            
            # Check cache first
            if input_hash in self.inference_cache:
                latency = 2  # Cache hit
            else:
                latency = random.uniform(15, 45)  # Model inference
                self.inference_cache[input_hash] = {
                    "result": random.random(),
                    "timestamp": datetime.now()
                }
                
            # Buffer result for sync
            self.data_buffer.append({
                "input_hash": input_hash,
                "latency_ms": latency,
                "timestamp": datetime.now().isoformat()
            })
            
            await asyncio.sleep(random.uniform(0.5, 2))
            
    async def data_sync_loop(self):
        """Sync buffered data to cloud"""
        await asyncio.sleep(10)
        
        while self.running:
            if self.data_buffer:
                # Batch upload
                batch = self.data_buffer[:50]
                self.data_buffer = self.data_buffer[50:]
                
                print(f"[{self.device_id}] Syncing {len(batch)} events to cloud")
                
                # Simulate compression (80% reduction)
                compressed_size = len(str(batch)) * 0.2
                print(f"[{self.device_id}] Uploaded {compressed_size:.0f} bytes (compressed)")
                
            await asyncio.sleep(60)  # Batch every 60 seconds
            
    async def deploy_model(self, model_id: str):
        """Deploy new model version"""
        print(f"[{self.device_id}] Deploying model {model_id}")
        
        # Simulate model download
        await asyncio.sleep(2)
        
        # Zero-downtime swap
        old_model = self.current_model
        self.current_model = model_id
        
        # Clear cache for new model
        self.inference_cache.clear()
        
        print(f"[{self.device_id}] Model deployed: {old_model} -> {model_id}")
