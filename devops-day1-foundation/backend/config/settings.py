import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class Settings:
    APP_NAME = "DevOps Foundation"
    VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # API Configuration
    API_PREFIX = "/api"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # AWS Configuration (for simulation)
    AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
    AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "123456789012")
    
    # Monitoring Configuration
    METRICS_INTERVAL = int(os.getenv("METRICS_INTERVAL", 5))
    RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", 30))

settings = Settings()
