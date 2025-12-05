import asyncio
import httpx
import random
from datetime import datetime

SERVICES = {
    'order': 'http://localhost:8001',
    'payment': 'http://localhost:8002',
    'inventory': 'http://localhost:8003',
    'notification': 'http://localhost:8004'
}

async def generate_traffic():
    """Generate continuous traffic to all services"""
    print("Starting traffic generation...")
    print("Sending requests to all services every 0.5 seconds")
    print("Press Ctrl+C to stop\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                # Order service
                await client.post(
                    f"{SERVICES['order']}/api/orders",
                    json={"items": ["item1", "item2"], "total": random.uniform(50, 500)}
                )
                
                # Payment service
                await client.post(
                    f"{SERVICES['payment']}/api/payments",
                    json={"amount": random.uniform(10, 1000), "method": "credit_card"}
                )
                
                # Inventory service
                await client.post(
                    f"{SERVICES['inventory']}/api/inventory/check",
                    json={"sku": f"SKU-{random.randint(1000, 9999)}"}
                )
                
                # Notification service
                await client.post(
                    f"{SERVICES['notification']}/api/notifications/send",
                    json={"channel": "email", "recipient": "user@example.com"}
                )
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent requests to all services")
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(generate_traffic())
    except KeyboardInterrupt:
        print("\nTraffic generation stopped")
