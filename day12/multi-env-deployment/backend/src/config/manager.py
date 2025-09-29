import yaml
import json
from typing import Dict, Any

class ConfigManager:
    def __init__(self):
        self.configs = {
            "base": {
                "app_name": "multi-env-platform",
                "version": "1.0.0",
                "database": {
                    "pool_size": 10,
                    "timeout": 30
                },
                "cache": {
                    "ttl": 3600
                }
            },
            "dev": {
                "debug": True,
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "name": "devdb"
                },
                "log_level": "DEBUG"
            },
            "staging": {
                "debug": False,
                "database": {
                    "host": "staging-db.internal",
                    "port": 5432,
                    "name": "stagingdb"
                },
                "log_level": "INFO",
                "performance_monitoring": True
            },
            "prod": {
                "debug": False,
                "database": {
                    "host": "prod-db.internal",
                    "port": 5432,
                    "name": "proddb",
                    "ssl": True
                },
                "log_level": "WARNING",
                "performance_monitoring": True,
                "security": {
                    "rate_limiting": True,
                    "cors_enabled": False
                }
            }
        }
    
    def get_config(self, environment: str) -> Dict[str, Any]:
        # Start with base config
        config = self.configs["base"].copy()
        
        # Merge environment-specific config
        if environment in self.configs:
            config = self._deep_merge(config, self.configs[environment])
        
        return config
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def update_config(self, environment: str, path: str, value: Any):
        if environment not in self.configs:
            self.configs[environment] = {}
        
        # Support dot notation: "database.host"
        keys = path.split('.')
        config = self.configs[environment]
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
