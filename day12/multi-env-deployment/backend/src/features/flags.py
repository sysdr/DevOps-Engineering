import json
from typing import Dict, List, Optional
from datetime import datetime

class FeatureFlagService:
    def __init__(self):
        self.flags = {
            "new_checkout_flow": {
                "enabled": True,
                "rollout_percentage": 25,
                "user_segments": ["beta_users"],
                "environments": ["dev", "staging"],
                "created_at": "2024-01-15T10:00:00Z"
            },
            "dark_mode": {
                "enabled": False,
                "rollout_percentage": 0,
                "user_segments": [],
                "environments": ["dev"],
                "created_at": "2024-01-20T14:30:00Z"
            },
            "advanced_analytics": {
                "enabled": True,
                "rollout_percentage": 100,
                "user_segments": ["premium_users"],
                "environments": ["prod"],
                "created_at": "2024-01-10T09:15:00Z"
            }
        }
    
    async def get_all_flags(self) -> Dict:
        return {"flags": self.flags}
    
    async def get_flag(self, flag_name: str) -> Optional[Dict]:
        return self.flags.get(flag_name)
    
    async def update_flag(self, flag_name: str, config: Dict) -> Dict:
        if flag_name in self.flags:
            self.flags[flag_name].update(config)
            self.flags[flag_name]["updated_at"] = datetime.now().isoformat()
            return {"status": "updated", "flag": self.flags[flag_name]}
        else:
            self.flags[flag_name] = {
                **config,
                "created_at": datetime.now().isoformat()
            }
            return {"status": "created", "flag": self.flags[flag_name]}
    
    async def evaluate_flag(self, flag_name: str, user_id: str, environment: str) -> bool:
        flag = self.flags.get(flag_name)
        if not flag or not flag["enabled"]:
            return False
        
        # Check environment
        if environment not in flag["environments"]:
            return False
        
        # Simple percentage-based rollout
        user_hash = hash(user_id) % 100
        return user_hash < flag["rollout_percentage"]
    
    async def create_flag(self, flag_name: str, config: Dict) -> Dict:
        default_config = {
            "enabled": False,
            "rollout_percentage": 0,
            "user_segments": [],
            "environments": ["dev"],
            "created_at": datetime.now().isoformat()
        }
        
        self.flags[flag_name] = {**default_config, **config}
        return {"status": "created", "flag": self.flags[flag_name]}
