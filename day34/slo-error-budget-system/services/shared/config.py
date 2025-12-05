import os

class Config:
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
    
    # SLO Configurations
    SLOS = {
        'order': {
            'availability': 99.9,  # 99.9% availability
            'latency_p99': 500,     # 500ms p99 latency
            'latency_p95': 300,     # 300ms p95 latency
        },
        'payment': {
            'availability': 99.95,  # Higher SLO for critical service
            'latency_p99': 1000,
            'latency_p95': 500,
        },
        'inventory': {
            'availability': 99.5,
            'latency_p99': 800,
            'latency_p95': 400,
        },
        'notification': {
            'availability': 99.0,   # Lower SLO for non-critical
            'latency_p99': 2000,
            'latency_p95': 1000,
        }
    }
    
    # Burn rate thresholds
    BURN_RATE_THRESHOLDS = {
        'log': 2.0,      # 2x burn rate - log warning
        'ticket': 5.0,   # 5x burn rate - create ticket
        'page': 10.0,    # 10x burn rate - page on-call
        'critical': 20.0 # 20x burn rate - block deployments
    }
    
    # Time windows for burn rate calculation
    TIME_WINDOWS = ['1h', '6h', '24h', '72h']
