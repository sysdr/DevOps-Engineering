import requests
import random
import time
from concurrent.futures import ThreadPoolExecutor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URLS = {
    'user': 'http://localhost:8001',
    'order': 'http://localhost:8002',
    'payment': 'http://localhost:8003'
}

def generate_user_requests():
    users = ['alice', 'bob', 'charlie', 'unknown_user']
    passwords = ['pass123', 'pass456', 'pass789', 'wrongpass']
    
    for _ in range(10):
        username = random.choice(users)
        password = random.choice(passwords)
        
        try:
            response = requests.post(
                f"{BASE_URLS['user']}/api/login",
                json={"username": username, "password": password},
                timeout=5
            )
            logger.info(f"User login: {username} - Status: {response.status_code}")
        except Exception as e:
            logger.error(f"User service error: {e}")
        
        time.sleep(random.uniform(0.1, 0.5))

def generate_order_requests():
    for _ in range(8):
        user_id = random.randint(1001, 1003)
        num_items = random.randint(1, 5)
        items = [
            {
                "product_id": random.randint(100, 110),
                "quantity": random.randint(1, 3),
                "price": round(random.uniform(10, 100), 2)
            }
            for _ in range(num_items)
        ]
        
        try:
            response = requests.post(
                f"{BASE_URLS['order']}/api/orders",
                json={"user_id": user_id, "items": items},
                timeout=5
            )
            logger.info(f"Order created: user {user_id} - Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Order service error: {e}")
        
        time.sleep(random.uniform(0.2, 0.7))

def generate_payment_requests():
    for _ in range(6):
        order_id = random.randint(1000, 1100)
        amount = round(random.uniform(50, 500), 2)
        payment_methods = ['credit_card', 'debit_card', 'paypal']
        
        try:
            response = requests.post(
                f"{BASE_URLS['payment']}/api/payments",
                json={
                    "order_id": order_id,
                    "amount": amount,
                    "payment_method": random.choice(payment_methods)
                },
                timeout=5
            )
            logger.info(f"Payment processed: order {order_id} - Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Payment service error: {e}")
        
        time.sleep(random.uniform(0.3, 0.8))

def main():
    logger.info("Starting load generator...")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        for _ in range(5):  # Run 5 iterations
            executor.submit(generate_user_requests)
            executor.submit(generate_order_requests)
            executor.submit(generate_payment_requests)
            time.sleep(2)
    
    logger.info("Load generation complete")

if __name__ == "__main__":
    main()
