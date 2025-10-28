import httpx
import asyncio
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ServiceRegistry:
    def __init__(self):
        self.services: Dict[str, Dict] = {}

    def register_service(self, name: str, host: str, port: int, health_check_url: str):
        self.services[name] = {
            "host": host,
            "port": port,
            "health_check_url": health_check_url,
            "healthy": True,
            "last_check": None
        }
        logger.info(f"Registered service: {name} at {host}:{port}")

    def get_service_url(self, name: str) -> Optional[str]:
        if name in self.services and self.services[name]["healthy"]:
            service = self.services[name]
            return f"http://{service['host']}:{service['port']}"
        return None

    def list_healthy_services(self) -> List[str]:
        return [name for name, info in self.services.items() if info["healthy"]]

    async def health_check_all(self):
        for name, service in self.services.items():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"http://{service['host']}:{service['port']}{service['health_check_url']}",
                        timeout=5.0
                    )
                    service["healthy"] = response.status_code == 200
            except Exception as e:
                logger.warning(f"Health check failed for {name}: {e}")
                service["healthy"] = False

class ServiceDiscovery:
    def __init__(self):
        self.registry = ServiceRegistry()

    async def discover_service(self, name: str) -> Optional[str]:
        return self.registry.get_service_url(name)

    def register_service(self, name: str, host: str, port: int, health_check_url: str = "/health"):
        self.registry.register_service(name, host, port, health_check_url)

    async def health_check_loop(self, interval: int = 30):
        while True:
            await self.registry.health_check_all()
            await asyncio.sleep(interval)
