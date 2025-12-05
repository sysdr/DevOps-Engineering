import time
import functools
from prometheus_client import Histogram, Counter
from typing import Callable

# Prometheus metrics
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['service', 'endpoint', 'method', 'status']
)

REQUEST_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['service', 'endpoint', 'method', 'status']
)

def track_sli(service_name: str):
    """Decorator to track SLI metrics for service endpoints"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "500"
            
            try:
                result = await func(*args, **kwargs)
                status = "200"
                return result
            except Exception as e:
                status = "500"
                raise e
            finally:
                duration = time.time() - start_time
                endpoint = func.__name__
                
                REQUEST_LATENCY.labels(
                    service=service_name,
                    endpoint=endpoint,
                    method="POST",
                    status=status
                ).observe(duration)
                
                REQUEST_TOTAL.labels(
                    service=service_name,
                    endpoint=endpoint,
                    method="POST",
                    status=status
                ).inc()
        
        return wrapper
    return decorator
