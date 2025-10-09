#!/usr/bin/env python3
"""
Mock WebApp Operator for Demo Purposes
This version runs without requiring a real Kubernetes cluster
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any
from prometheus_client import start_http_server, Counter, Gauge, Histogram
import os
from datetime import datetime

# Metrics
WEBAPP_CREATED = Counter('webapp_created_total', 'Total WebApps created')
WEBAPP_DELETED = Counter('webapp_deleted_total', 'Total WebApps deleted')
WEBAPP_RECONCILED = Counter('webapp_reconciled_total', 'Total WebApp reconciliations')
WEBAPP_CURRENT = Gauge('webapp_current', 'Current number of WebApps')
RECONCILE_DURATION = Histogram('webapp_reconcile_duration_seconds', 'Time spent reconciling WebApps')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockWebAppOperator:
    def __init__(self):
        self.metrics_port = int(os.environ.get('METRICS_PORT', 8000))
        self.webapps = {}  # Store mock webapp state
        start_http_server(self.metrics_port)
        logger.info(f"Mock WebApp Operator started - Metrics server on port {self.metrics_port}")
        
        # Initialize with some demo data
        self._create_demo_webapps()

    def _create_demo_webapps(self):
        """Create some demo webapps for the dashboard"""
        demo_webapps = [
            {
                "name": "demo-webapp",
                "namespace": "default",
                "spec": {
                    "replicas": 3,
                    "image": "nginx:alpine",
                    "port": 80,
                    "resources": {
                        "cpu": "100m",
                        "memory": "128Mi"
                    },
                    "affinity": {
                        "zone": "us-west-2a"
                    }
                },
                "status": {
                    "phase": "Running",
                    "message": "WebApp is running successfully",
                    "created_at": datetime.now().isoformat(),
                    "replicas_ready": 3,
                    "replicas_total": 3
                }
            },
            {
                "name": "api-service",
                "namespace": "production",
                "spec": {
                    "replicas": 5,
                    "image": "node:18-alpine",
                    "port": 3000,
                    "resources": {
                        "cpu": "200m",
                        "memory": "256Mi"
                    },
                    "affinity": {
                        "zone": "us-west-2b"
                    }
                },
                "status": {
                    "phase": "Running",
                    "message": "API service is healthy",
                    "created_at": datetime.now().isoformat(),
                    "replicas_ready": 5,
                    "replicas_total": 5
                }
            }
        ]
        
        for webapp in demo_webapps:
            self.webapps[f"{webapp['namespace']}/{webapp['name']}"] = webapp
            WEBAPP_CREATED.inc()
            WEBAPP_CURRENT.inc()

    async def create_webapp(self, name: str, namespace: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Mock WebApp creation"""
        with RECONCILE_DURATION.time():
            logger.info(f"Creating WebApp {name} in namespace {namespace}")
            
            webapp_key = f"{namespace}/{name}"
            webapp = {
                "name": name,
                "namespace": namespace,
                "spec": spec,
                "status": {
                    "phase": "Running",
                    "message": f"WebApp {name} created successfully",
                    "created_at": datetime.now().isoformat(),
                    "replicas_ready": spec.get('replicas', 1),
                    "replicas_total": spec.get('replicas', 1)
                }
            }
            
            self.webapps[webapp_key] = webapp
            WEBAPP_CREATED.inc()
            WEBAPP_CURRENT.inc()
            WEBAPP_RECONCILED.inc()
            
            return {"phase": "Created", "message": f"WebApp {name} created successfully"}

    async def update_webapp(self, name: str, namespace: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Mock WebApp update"""
        with RECONCILE_DURATION.time():
            logger.info(f"Updating WebApp {name} in namespace {namespace}")
            
            webapp_key = f"{namespace}/{name}"
            if webapp_key in self.webapps:
                self.webapps[webapp_key]["spec"] = spec
                self.webapps[webapp_key]["status"]["message"] = f"WebApp {name} updated successfully"
                self.webapps[webapp_key]["status"]["replicas_ready"] = spec.get('replicas', 1)
                self.webapps[webapp_key]["status"]["replicas_total"] = spec.get('replicas', 1)
                
                WEBAPP_RECONCILED.inc()
                return {"phase": "Updated", "message": f"WebApp {name} updated successfully"}
            else:
                return await self.create_webapp(name, namespace, spec)

    async def delete_webapp(self, name: str, namespace: str) -> Dict[str, Any]:
        """Mock WebApp deletion"""
        logger.info(f"Deleting WebApp {name} in namespace {namespace}")
        
        webapp_key = f"{namespace}/{name}"
        if webapp_key in self.webapps:
            del self.webapps[webapp_key]
            WEBAPP_DELETED.inc()
            WEBAPP_CURRENT.dec()
            logger.info(f"Successfully deleted WebApp {name}")
            return {"phase": "Deleted", "message": f"WebApp {name} deleted successfully"}
        else:
            return {"phase": "NotFound", "message": f"WebApp {name} not found"}

    def get_webapps(self) -> Dict[str, Any]:
        """Get all webapps"""
        return self.webapps

    def get_webapp(self, name: str, namespace: str) -> Dict[str, Any]:
        """Get specific webapp"""
        webapp_key = f"{namespace}/{name}"
        return self.webapps.get(webapp_key, {})

# Initialize operator
operator = MockWebAppOperator()

# Simple HTTP server for API endpoints
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class MockOperatorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        elif self.path == '/api/webapps':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            webapps = operator.get_webapps()
            self.wfile.write(json.dumps(list(webapps.values())).encode())
        elif self.path == '/api/metrics':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            webapps = operator.get_webapps()
            metrics_data = {
                "webapps": [
                    {
                        "name": webapp["name"],
                        "replicas": webapp["spec"]["replicas"],
                        "status": webapp["status"]["phase"],
                        "zone": webapp["spec"].get("affinity", {}).get("zone", "default")
                    }
                    for webapp in webapps.values()
                ],
                "totalCreated": len(webapps),
                "totalDeleted": 0,
                "currentWebApps": len(webapps),
                "reconciliations": len(webapps) * 3  # Mock reconciliation count
            }
            self.wfile.write(json.dumps(metrics_data).encode())
        elif self.path == '/api/resources':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            webapps = operator.get_webapps()
            total_cpu = sum(int(webapp["spec"]["resources"]["cpu"].replace("m", "")) for webapp in webapps.values())
            total_memory = sum(int(webapp["spec"]["resources"]["memory"].replace("Mi", "")) for webapp in webapps.values())
            total_pods = sum(webapp["spec"]["replicas"] for webapp in webapps.values())
            
            resource_data = {
                "cpuUsage": min(95, (total_cpu / 1000) * 10),  # Mock CPU usage calculation
                "memoryUsage": min(95, (total_memory / 1000) * 15),  # Mock memory usage calculation
                "podCount": total_pods
            }
            self.wfile.write(json.dumps(resource_data).encode())
        elif self.path.startswith('/api/webapps/'):
            # Parse webapp name from path
            path_parts = self.path.split('/')
            if len(path_parts) >= 4:
                namespace_name = path_parts[3]
                if '/' in namespace_name:
                    namespace, name = namespace_name.split('/', 1)
                    webapp = operator.get_webapp(name, namespace)
                    if webapp:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(webapp).encode())
                    else:
                        self.send_response(404)
                        self.end_headers()
                else:
                    self.send_response(400)
                    self.end_headers()
            else:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith('/api/webapps/'):
            # Parse webapp name from path
            path_parts = self.path.split('/')
            if len(path_parts) >= 4:
                namespace_name = path_parts[3]
                if '/' in namespace_name:
                    namespace, name = namespace_name.split('/', 1)
                    
                    # Read request body
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    spec = json.loads(post_data.decode('utf-8'))
                    
                    # Create or update webapp
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(operator.update_webapp(name, namespace, spec))
                    loop.close()
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                else:
                    self.send_response(400)
                    self.end_headers()
            else:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        if self.path.startswith('/api/webapps/'):
            # Parse webapp name from path
            path_parts = self.path.split('/')
            if len(path_parts) >= 4:
                namespace_name = path_parts[3]
                if '/' in namespace_name:
                    namespace, name = namespace_name.split('/', 1)
                    
                    # Delete webapp
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(operator.delete_webapp(name, namespace))
                    loop.close()
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                else:
                    self.send_response(400)
                    self.end_headers()
            else:
                self.send_response(400)
                self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging
        pass

def run_mock_operator():
    """Run the mock operator HTTP server"""
    # Use port 8001 for API server to avoid conflict with Prometheus metrics on 8000
    api_port = 8001
    server = HTTPServer(('0.0.0.0', api_port), MockOperatorHandler)
    logger.info(f"Mock operator API server started on port {api_port}")
    logger.info("Available endpoints:")
    logger.info("  GET  /health - Health check")
    logger.info("  GET  /api/webapps - List all webapps")
    logger.info("  GET  /api/metrics - Get metrics data")
    logger.info("  GET  /api/resources - Get resource usage data")
    logger.info("  GET  /api/webapps/{namespace}/{name} - Get specific webapp")
    logger.info("  POST /api/webapps/{namespace}/{name} - Create/update webapp")
    logger.info("  DELETE /api/webapps/{namespace}/{name} - Delete webapp")
    logger.info("  GET  /metrics - Prometheus metrics (port 8000)")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down mock operator...")
        server.shutdown()

if __name__ == "__main__":
    run_mock_operator()
