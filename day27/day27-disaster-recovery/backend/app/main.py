from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
from app.backup_manager import BackupManager, ReplicationManager, DRMetricsCollector

backup_mgr = BackupManager()
replication_mgr = ReplicationManager()
metrics_collector = DRMetricsCollector()

class RequestHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/api/backups':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            
            backups = backup_mgr.list_backups()
            self.wfile.write(json.dumps({"backups": backups}).encode())
        
        elif parsed_path.path == '/api/replication/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            
            status = replication_mgr.get_status()
            self.wfile.write(json.dumps(status).encode())
        
        elif parsed_path.path == '/api/metrics':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            
            metrics = metrics_collector.get_metrics()
            self.wfile.write(json.dumps(metrics).encode())
        
        elif parsed_path.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body) if body else {}
        
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/api/backups':
            backup = backup_mgr.create_backup(
                name=data.get('name', 'manual-backup'),
                namespaces=data.get('namespaces', ['default']),
                backup_type=data.get('type', 'full')
            )
            
            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(backup).encode())
        
        elif parsed_path.path.startswith('/api/backups/') and parsed_path.path.endswith('/restore'):
            backup_id = parsed_path.path.split('/')[3]
            restore = backup_mgr.restore_backup(
                backup_id=backup_id,
                target_region=data.get('target_region', 'dr')
            )
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(restore).encode())
        
        elif parsed_path.path == '/api/failover':
            failover = replication_mgr.trigger_failover(
                target_region=data.get('target_region', 'us-west-2')
            )
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(failover).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_DELETE(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path.startswith('/api/backups/'):
            backup_id = parsed_path.path.split('/')[3]
            success = backup_mgr.delete_backup(backup_id)
            
            if success:
                self.send_response(204)
            else:
                self.send_response(404)
            
            self._send_cors_headers()
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def run_server(port=8000):
    server = HTTPServer(('0.0.0.0', port), RequestHandler)
    print(f"DR Management API running on http://localhost:{port}")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == '__main__':
    run_server()
