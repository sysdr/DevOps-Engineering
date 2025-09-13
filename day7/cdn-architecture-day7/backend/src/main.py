import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import hashlib
import time
import random
from urllib.parse import urlparse
import aiohttp
from aiohttp import web
from aiohttp.web import middleware
import aiohttp_cors

@dataclass
class EdgeNode:
    id: str
    region: str
    lat: float
    lng: float
    capacity: int
    current_load: int
    status: str = "healthy"
    cache_size: int = 1000
    cached_items: Dict = None
    
    def __post_init__(self):
        if self.cached_items is None:
            self.cached_items = {}

@dataclass
class CacheItem:
    key: str
    content: str
    size: int
    timestamp: datetime
    ttl: int
    hit_count: int = 0
    region: str = ""

class CDNRouter:
    def __init__(self):
        self.edge_nodes = self._initialize_edge_nodes()
        self.health_checks = {}
        self.request_logs = []
        self.cost_metrics = {"bandwidth": 0, "requests": 0, "cache_hits": 0}
        
    def _initialize_edge_nodes(self) -> Dict[str, EdgeNode]:
        nodes = {
            "us-east": EdgeNode("us-east", "US East", 40.7128, -74.0060, 1000, 0),
            "us-west": EdgeNode("us-west", "US West", 37.7749, -122.4194, 1000, 0),
            "eu-west": EdgeNode("eu-west", "EU West", 51.5074, -0.1278, 800, 0),
            "ap-south": EdgeNode("ap-south", "AP South", 19.0760, 72.8777, 600, 0),
            "ap-east": EdgeNode("ap-east", "AP East", 35.6762, 139.6503, 700, 0)
        }
        
        # Pre-populate some cache items
        sample_content = ["homepage.html", "logo.png", "app.js", "styles.css", "api-data.json"]
        for node_id, node in nodes.items():
            for i, content in enumerate(sample_content):
                cache_key = f"{content}-{i}"
                node.cached_items[cache_key] = CacheItem(
                    key=cache_key,
                    content=f"Content for {content} cached in {node_id}",
                    size=random.randint(1, 100),
                    timestamp=datetime.now() - timedelta(minutes=random.randint(1, 60)),
                    ttl=3600,
                    region=node_id
                )
        return nodes
        
    def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        return 2 * asin(sqrt(a)) * 6371  # Earth radius in km
        
    def find_optimal_edge(self, user_lat: float, user_lng: float) -> EdgeNode:
        """Find the optimal edge node based on distance and health"""
        healthy_nodes = [node for node in self.edge_nodes.values() if node.status == "healthy"]
        
        if not healthy_nodes:
            # Emergency fallback - return any node
            return list(self.edge_nodes.values())[0]
            
        # Calculate weighted score: distance + load factor
        best_node = None
        best_score = float('inf')
        
        for node in healthy_nodes:
            distance = self.calculate_distance(user_lat, user_lng, node.lat, node.lng)
            load_factor = node.current_load / node.capacity
            score = distance * (1 + load_factor)  # Penalize high load
            
            if score < best_score:
                best_score = score
                best_node = node
                
        return best_node
        
    async def handle_request(self, resource: str, user_lat: float, user_lng: float, 
                           user_ip: str) -> Dict:
        """Handle CDN request with geographic routing"""
        start_time = time.time()
        
        # Find optimal edge node
        edge_node = self.find_optimal_edge(user_lat, user_lng)
        
        # Check cache
        cache_hit = resource in edge_node.cached_items
        
        if cache_hit:
            cached_item = edge_node.cached_items[resource]
            # Check TTL
            if datetime.now() - cached_item.timestamp > timedelta(seconds=cached_item.ttl):
                cache_hit = False
                del edge_node.cached_items[resource]
            else:
                cached_item.hit_count += 1
                
        response_time = time.time() - start_time
        
        # Simulate origin fetch if cache miss
        if not cache_hit:
            await asyncio.sleep(0.1)  # Simulate origin latency
            # Add to cache
            edge_node.cached_items[resource] = CacheItem(
                key=resource,
                content=f"Content for {resource} from origin",
                size=random.randint(1, 100),
                timestamp=datetime.now(),
                ttl=3600,
                region=edge_node.id
            )
            response_time += 0.1
            
        # Update metrics
        edge_node.current_load = min(edge_node.current_load + 1, edge_node.capacity)
        self.cost_metrics["requests"] += 1
        self.cost_metrics["bandwidth"] += edge_node.cached_items[resource].size
        
        if cache_hit:
            self.cost_metrics["cache_hits"] += 1
            
        # Log request
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "resource": resource,
            "edge_node": edge_node.id,
            "user_location": f"{user_lat},{user_lng}",
            "user_ip": user_ip,
            "cache_hit": cache_hit,
            "response_time": response_time * 1000,  # Convert to ms
            "cost": edge_node.cached_items[resource].size * (0.01 if cache_hit else 0.05)
        }
        self.request_logs.append(log_entry)
        
        return {
            "status": "success",
            "edge_node": asdict(edge_node),
            "cache_hit": cache_hit,
            "response_time_ms": response_time * 1000,
            "content": edge_node.cached_items[resource].content,
            "cost_usd": log_entry["cost"]
        }
        
    async def health_check(self):
        """Simulate health checks and random failures"""
        while True:
            for node_id, node in self.edge_nodes.items():
                # Random failure simulation (2% chance)
                if random.random() < 0.02:
                    node.status = "failed"
                elif node.status == "failed" and random.random() < 0.1:
                    node.status = "healthy"
                    
                # Simulate load decay
                node.current_load = max(0, node.current_load - random.randint(1, 5))
                
            await asyncio.sleep(5)  # Check every 5 seconds

# Web server setup
cdn_router = CDNRouter()

@middleware
async def cors_handler(request, handler):
    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

async def handle_cdn_request(request):
    """Handle CDN routing request"""
    data = await request.json()
    
    result = await cdn_router.handle_request(
        resource=data.get('resource', 'index.html'),
        user_lat=data.get('lat', 40.7128),
        user_lng=data.get('lng', -74.0060),
        user_ip=data.get('ip', '127.0.0.1')
    )
    
    return web.json_response(result)

async def handle_metrics(request):
    """Return CDN metrics"""
    cache_hit_rate = (cdn_router.cost_metrics["cache_hits"] / 
                     max(cdn_router.cost_metrics["requests"], 1)) * 100
    
    # Convert edge nodes to dict and handle datetime serialization
    edge_nodes_data = []
    for node in cdn_router.edge_nodes.values():
        node_dict = asdict(node)
        # Convert datetime objects in cached_items to ISO format strings
        for item_key, item in node_dict.get('cached_items', {}).items():
            if isinstance(item, dict) and 'timestamp' in item:
                item['timestamp'] = item['timestamp'].isoformat() if hasattr(item['timestamp'], 'isoformat') else str(item['timestamp'])
        edge_nodes_data.append(node_dict)
    
    metrics = {
        "edge_nodes": edge_nodes_data,
        "cost_metrics": cdn_router.cost_metrics,
        "cache_hit_rate": round(cache_hit_rate, 2),
        "recent_requests": cdn_router.request_logs[-10:],  # Last 10 requests
        "total_requests": len(cdn_router.request_logs)
    }
    
    return web.json_response(metrics)

async def handle_invalidate(request):
    """Handle cache invalidation"""
    data = await request.json()
    resource = data.get('resource')
    regions = data.get('regions', list(cdn_router.edge_nodes.keys()))
    
    invalidated = []
    for region in regions:
        if region in cdn_router.edge_nodes:
            node = cdn_router.edge_nodes[region]
            if resource in node.cached_items:
                del node.cached_items[resource]
                invalidated.append(region)
                
    return web.json_response({
        "status": "success",
        "invalidated_regions": invalidated,
        "resource": resource
    })

async def init_app():
    app = web.Application(middlewares=[cors_handler])
    
    app.router.add_post('/api/cdn/request', handle_cdn_request)
    app.router.add_get('/api/cdn/metrics', handle_metrics)
    app.router.add_post('/api/cdn/invalidate', handle_invalidate)
    
    # Start health check background task
    asyncio.create_task(cdn_router.health_check())
    
    return app

if __name__ == '__main__':
    web.run_app(init_app(), host='0.0.0.0', port=8080)
