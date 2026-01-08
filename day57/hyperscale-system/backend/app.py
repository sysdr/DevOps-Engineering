from fastapi import FastAPI, WebSocket, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, List
import asyncio
import json
import time
import hashlib
import random
from collections import defaultdict
from datetime import datetime

app = FastAPI(title="Hyperscale Architecture System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class HyperscaleSystem:
    def __init__(self):
        self.regions = {
            "us-east": {"lat": 40.7, "lon": -74.0, "capacity": 1000000, "health": 98},
            "us-west": {"lat": 37.7, "lon": -122.4, "capacity": 1000000, "health": 96},
            "eu-west": {"lat": 51.5, "lon": -0.1, "capacity": 500000, "health": 97}
        }
        self.shards = {}
        self.cache_stats = {
            "l1_hits": 0, "l2_hits": 0, "l3_hits": 0, "misses": 0
        }
        self.request_count = 0
        self.cache_data = {}
        self.shard_data = defaultdict(dict)
        self.active_load = False
        self.failed_regions = set()
        
        # Initialize shards with consistent hashing
        self.init_shards(4)
        
    def init_shards(self, num_shards: int):
        """Initialize shards with consistent hashing"""
        self.num_shards = num_shards
        self.virtual_nodes = 256
        self.hash_ring = []
        
        for shard_id in range(num_shards):
            for vnode in range(self.virtual_nodes):
                # Create virtual node hash
                key = f"shard_{shard_id}_vnode_{vnode}"
                hash_val = int(hashlib.md5(key.encode()).hexdigest(), 16)
                self.hash_ring.append((hash_val, shard_id))
                
        # Sort ring by hash value
        self.hash_ring.sort(key=lambda x: x[0])
        
        # Initialize shard statistics
        for shard_id in range(num_shards):
            self.shards[f"shard_{shard_id}"] = {
                "id": shard_id,
                "keys": 0,
                "load_pct": 0.0,
                "requests": 0
            }
    
    def get_shard(self, key: str) -> int:
        """Get shard for a key using consistent hashing"""
        key_hash = int(hashlib.md5(key.encode()).hexdigest(), 16)
        
        # Binary search for next virtual node
        left, right = 0, len(self.hash_ring) - 1
        result_idx = 0
        
        while left <= right:
            mid = (left + right) // 2
            if self.hash_ring[mid][0] >= key_hash:
                result_idx = mid
                right = mid - 1
            else:
                left = mid + 1
        
        return self.hash_ring[result_idx][1]
    
    def route_request(self, user_location: tuple) -> str:
        """Route request to nearest healthy region"""
        if not user_location:
            user_location = (40.7, -74.0)  # Default to US-East
        
        best_region = None
        min_distance = float('inf')
        
        for region_name, region_info in self.regions.items():
            if region_name in self.failed_regions:
                continue
                
            if region_info["health"] < 50:
                continue
            
            # Calculate distance
            lat_diff = user_location[0] - region_info["lat"]
            lon_diff = user_location[1] - region_info["lon"]
            distance = (lat_diff ** 2 + lon_diff ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                best_region = region_name
        
        return best_region or "us-east"
    
    def check_cache(self, cache_key: str, ttl: int = 300) -> Optional[Dict]:
        """Check multi-tier cache"""
        if cache_key in self.cache_data:
            entry = self.cache_data[cache_key]
            age = time.time() - entry["timestamp"]
            
            if age < 30:  # L1 cache - 30 seconds
                self.cache_stats["l1_hits"] += 1
                return entry["data"]
            elif age < 300:  # L2 cache - 5 minutes
                self.cache_stats["l2_hits"] += 1
                return entry["data"]
            elif age < 1800:  # L3 cache - 30 minutes
                self.cache_stats["l3_hits"] += 1
                return entry["data"]
            else:
                # Expired
                del self.cache_data[cache_key]
        
        self.cache_stats["misses"] += 1
        return None
    
    def set_cache(self, cache_key: str, data: Dict):
        """Set cache entry"""
        self.cache_data[cache_key] = {
            "data": data,
            "timestamp": time.time()
        }
    
    def get_metrics(self) -> Dict:
        """Get current system metrics"""
        total_cache_requests = sum(self.cache_stats.values())
        cache_hit_rate = 0.0
        if total_cache_requests > 0:
            hits = self.cache_stats["l1_hits"] + self.cache_stats["l2_hits"] + self.cache_stats["l3_hits"]
            cache_hit_rate = hits / total_cache_requests
        
        # Calculate shard distribution
        total_shard_keys = sum(shard["keys"] for shard in self.shards.values())
        for shard_name, shard_info in self.shards.items():
            if total_shard_keys > 0:
                shard_info["load_pct"] = (shard_info["keys"] / total_shard_keys) * 100
        
        return {
            "timestamp": int(time.time()),
            "global_rps": self.request_count,
            "regions": {
                name: {
                    "health": info["health"],
                    "rps": int(self.request_count * 0.33) if name not in self.failed_regions else 0,
                    "latency_p99": random.randint(40, 60),
                    "failed": name in self.failed_regions
                }
                for name, info in self.regions.items()
            },
            "cache": {
                "hit_rate": cache_hit_rate,
                "l1_hits": self.cache_stats["l1_hits"],
                "l2_hits": self.cache_stats["l2_hits"],
                "l3_hits": self.cache_stats["l3_hits"],
                "misses": self.cache_stats["misses"]
            },
            "shards": self.shards
        }

# Global system instance
system = HyperscaleSystem()

@app.get("/")
async def root():
    return {
        "service": "Hyperscale Architecture System",
        "version": "1.0.0",
        "regions": list(system.regions.keys()),
        "shards": system.num_shards
    }

@app.get("/api/user/{user_id}")
async def get_user_data(
    user_id: str,
    x_user_lat: Optional[float] = Header(None),
    x_user_lon: Optional[float] = Header(None)
):
    """Get user data with geographic routing and caching"""
    system.request_count += 1
    
    # Determine user location
    user_location = None
    if x_user_lat and x_user_lon:
        user_location = (x_user_lat, x_user_lon)
    
    # Route to appropriate region
    region = system.route_request(user_location)
    
    # Generate cache key with time bucketing (5-minute buckets)
    time_bucket = int(time.time() / 300) * 300
    cache_key = f"user:{user_id}:bucket:{time_bucket}"
    
    # Check cache
    cached_data = system.check_cache(cache_key)
    if cached_data:
        cached_data["cache_hit"] = True
        cached_data["region"] = region
        return cached_data
    
    # Get shard for user
    shard_id = system.get_shard(user_id)
    shard_name = f"shard_{shard_id}"
    
    # Simulate database query
    await asyncio.sleep(0.001)  # 1ms query time
    
    # Store data in shard
    if user_id not in system.shard_data[shard_name]:
        system.shards[shard_name]["keys"] += 1
    
    system.shard_data[shard_name][user_id] = {
        "user_id": user_id,
        "name": f"User {user_id}",
        "tier": random.choice(["free", "premium", "enterprise"]),
        "last_seen": datetime.utcnow().isoformat()
    }
    
    system.shards[shard_name]["requests"] += 1
    
    # Prepare response
    response = {
        "user_id": user_id,
        "shard": shard_name,
        "region": region,
        "data": system.shard_data[shard_name][user_id],
        "cache_hit": False
    }
    
    # Cache the response
    system.set_cache(cache_key, response)
    
    return response

@app.post("/admin/start-load")
async def start_load(config: Dict):
    """Start load generation"""
    system.active_load = True
    target_rps = config.get("target_rps", 100000)
    
    return {
        "status": "started",
        "target_rps": target_rps,
        "message": "Load generation started"
    }

@app.post("/admin/fail-region/{region_name}")
async def fail_region(region_name: str):
    """Simulate region failure"""
    if region_name not in system.regions:
        raise HTTPException(status_code=404, detail="Region not found")
    
    system.failed_regions.add(region_name)
    system.regions[region_name]["health"] = 0
    
    return {
        "status": "failed",
        "region": region_name,
        "message": f"Region {region_name} marked as failed",
        "failover": "Traffic redistributed to healthy regions"
    }

@app.post("/admin/recover-region/{region_name}")
async def recover_region(region_name: str):
    """Recover failed region"""
    if region_name not in system.regions:
        raise HTTPException(status_code=404, detail="Region not found")
    
    system.failed_regions.discard(region_name)
    system.regions[region_name]["health"] = random.randint(95, 99)
    
    return {
        "status": "recovered",
        "region": region_name,
        "health": system.regions[region_name]["health"]
    }

@app.get("/metrics")
async def get_metrics():
    """Get current system metrics"""
    return system.get_metrics()

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics"""
    await websocket.accept()
    
    try:
        while True:
            # Simulate some traffic
            if system.active_load:
                system.request_count += random.randint(8000, 12000)
            
            # Send metrics
            metrics = system.get_metrics()
            await websocket.send_json(metrics)
            
            await asyncio.sleep(0.5)  # Update every 500ms
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
