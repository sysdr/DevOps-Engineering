import requests
from typing import Dict, List, Optional
import json

class GrafanaAPI:
    def __init__(self, base_url: str = "http://localhost:3000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        else:
            # Use admin:admin for default Grafana setup
            self.auth = ('admin', 'admin')
    
    def get_dashboards(self) -> List[Dict]:
        """List all dashboards"""
        try:
            response = requests.get(
                f"{self.base_url}/api/search?type=dash-db",
                headers=self.headers,
                auth=getattr(self, 'auth', None),
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching dashboards: {e}")
            return []
    
    def get_dashboard(self, uid: str) -> Optional[Dict]:
        """Get dashboard by UID"""
        try:
            response = requests.get(
                f"{self.base_url}/api/dashboards/uid/{uid}",
                headers=self.headers,
                auth=getattr(self, 'auth', None),
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching dashboard {uid}: {e}")
            return None
    
    def create_dashboard(self, dashboard: Dict) -> Dict:
        """Create or update dashboard"""
        payload = {
            "dashboard": dashboard,
            "overwrite": True
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/dashboards/db",
                headers=self.headers,
                auth=getattr(self, 'auth', None),
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating dashboard: {e}")
            return {"error": str(e)}
    
    def get_health(self) -> Dict:
        """Check Grafana health"""
        try:
            response = requests.get(
                f"{self.base_url}/api/health",
                timeout=5
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
