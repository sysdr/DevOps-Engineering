"""
API Server for Secrets Management Dashboard
"""
import asyncio
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
sys.path.append('.')

from drift_detector import DriftDetector
from secrets_manager import ExternalSecretsSimulator, SealedSecretsSimulator


class SecretsAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for secrets management API"""
    
    drift_detector = None
    eso_simulator = None
    ss_simulator = None
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if path == '/api/drift-status':
            self.handle_drift_status()
        elif path == '/api/secrets-status':
            self.handle_secrets_status()
        elif path == '/api/sealed-secrets-cert':
            self.handle_sealed_cert()
        elif path == '/api/health':
            self.handle_health()
        else:
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def handle_drift_status(self):
        """Return drift detection status"""
        if not self.drift_detector:
            self.drift_detector = DriftDetector()
        
        # Run drift detection
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(self.drift_detector.run_drift_detection())
        summary = self.drift_detector.get_drift_summary()
        loop.close()
        
        response = {
            'summary': summary,
            'results': [
                {
                    'resource_name': r.resource_name,
                    'resource_kind': r.resource_kind,
                    'namespace': r.namespace,
                    'drift_detected': r.drift_detected,
                    'diff_summary': r.diff_summary,
                    'last_checked': r.last_checked,
                    'remediation_action': r.remediation_action
                }
                for r in results
            ]
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def handle_secrets_status(self):
        """Return secrets synchronization status"""
        if not self.eso_simulator:
            self.eso_simulator = ExternalSecretsSimulator()
            # Create sample secrets
            self.eso_simulator.create_external_secret('db-credentials', 'default', 'prod/db/password')
            self.eso_simulator.create_external_secret('api-key', 'default', 'prod/api/key')
        
        statuses = self.eso_simulator.get_secret_status()
        
        response = {
            'total_secrets': len(statuses),
            'secrets': [
                {
                    'name': s.name,
                    'namespace': s.namespace,
                    'type': s.secret_type,
                    'last_sync': s.last_sync,
                    'status': s.sync_status,
                    'source': s.source,
                    'refresh_interval': s.refresh_interval
                }
                for s in statuses
            ]
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def handle_sealed_cert(self):
        """Return sealed secrets public certificate"""
        if not self.ss_simulator:
            self.ss_simulator = SealedSecretsSimulator()
        
        cert = self.ss_simulator.get_public_cert()
        
        response = {
            'certificate': cert,
            'algorithm': 'RSA-2048',
            'usage': 'Use this certificate with kubeseal to encrypt secrets'
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def handle_health(self):
        """Health check endpoint"""
        response = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'drift_detector': 'running',
                'external_secrets': 'running',
                'sealed_secrets': 'running'
            }
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def run_server(port=8000):
    """Start the API server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, SecretsAPIHandler)
    print(f"API Server running on port {port}")
    print(f"Endpoints:")
    print(f"  - http://localhost:{port}/api/drift-status")
    print(f"  - http://localhost:{port}/api/secrets-status")
    print(f"  - http://localhost:{port}/api/sealed-secrets-cert")
    print(f"  - http://localhost:{port}/api/health")
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
