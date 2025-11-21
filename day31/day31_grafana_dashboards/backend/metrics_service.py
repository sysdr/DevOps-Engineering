from fastapi import FastAPI, Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest, REGISTRY
import random
import time
from datetime import datetime

app = FastAPI(title="Business Metrics Service")

# Define custom metrics
user_registrations = Counter(
    'business_user_registrations_total',
    'Total number of user registrations',
    ['source']
)

active_users = Gauge(
    'business_active_users',
    'Current number of active users',
    ['tier']
)

order_processing_time = Histogram(
    'business_order_processing_seconds',
    'Time spent processing orders',
    ['payment_method'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

payment_success_rate = Gauge(
    'business_payment_success_rate',
    'Payment success rate percentage',
    ['gateway']
)

api_requests = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

response_time = Histogram(
    'api_response_time_seconds',
    'API response time',
    ['endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

# Simulate business activity
def simulate_metrics():
    """Generate realistic business metrics"""
    # Simulate user activity
    active_users.labels(tier='free').set(random.randint(1000, 1500))
    active_users.labels(tier='premium').set(random.randint(200, 350))
    active_users.labels(tier='enterprise').set(random.randint(50, 100))
    
    # Simulate registrations
    if random.random() > 0.7:
        user_registrations.labels(source='organic').inc(random.randint(1, 5))
    if random.random() > 0.8:
        user_registrations.labels(source='referral').inc(random.randint(1, 3))
    if random.random() > 0.9:
        user_registrations.labels(source='paid').inc(random.randint(1, 2))
    
    # Simulate order processing
    for _ in range(random.randint(0, 3)):
        payment_method = random.choice(['credit_card', 'paypal', 'crypto'])
        processing_time = random.uniform(0.5, 3.0)
        order_processing_time.labels(payment_method=payment_method).observe(processing_time)
    
    # Simulate payment success rates
    payment_success_rate.labels(gateway='stripe').set(random.uniform(96.5, 99.5))
    payment_success_rate.labels(gateway='paypal').set(random.uniform(94.0, 98.0))
    payment_success_rate.labels(gateway='square').set(random.uniform(95.0, 98.5))
    
    # Simulate API activity
    endpoints = ['/api/users', '/api/orders', '/api/products', '/api/analytics']
    for _ in range(random.randint(5, 15)):
        endpoint = random.choice(endpoints)
        method = random.choice(['GET', 'POST', 'PUT'])
        status = random.choice(['200'] * 9 + ['500'])  # 90% success rate
        api_requests.labels(method=method, endpoint=endpoint, status=status).inc()
        response_time.labels(endpoint=endpoint).observe(random.uniform(0.01, 0.5))

@app.get("/")
async def root():
    return {
        "service": "Business Metrics Exporter",
        "version": "1.0.0",
        "metrics_endpoint": "/metrics"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    simulate_metrics()
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain"
    )

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
