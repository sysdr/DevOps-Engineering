#!/bin/bash

echo "🎯 Day 6: Advanced Storage & Database Patterns Demo"

source venv/bin/activate

echo "📊 1. Database Connection Pool Performance Test"
python3 -c "
import asyncio
import asyncpg
import time
from concurrent.futures import ThreadPoolExecutor

async def test_direct_connections():
    start_time = time.time()
    tasks = []
    
    for i in range(50):
        task = asyncpg.connect(
            host='localhost',
            port=5432,
            user='admin',
            password='secure_password_123',
            database='productiondb'
        )
        tasks.append(task)
    
    connections = await asyncio.gather(*tasks)
    
    # Close connections
    for conn in connections:
        await conn.close()
    
    end_time = time.time()
    print(f'Direct connections (50): {end_time - start_time:.2f} seconds')

async def test_pooled_connections():
    start_time = time.time()
    
    pool = await asyncpg.create_pool(
        host='localhost',
        port=6432,  # PgBouncer port
        user='admin',
        password='secure_password_123',
        database='productiondb',
        min_size=5,
        max_size=20
    )
    
    tasks = []
    for i in range(50):
        tasks.append(pool.fetchval('SELECT 1'))
    
    await asyncio.gather(*tasks)
    await pool.close()
    
    end_time = time.time()
    print(f'Pooled connections (50): {end_time - start_time:.2f} seconds')

async def main():
    await test_direct_connections()
    await test_pooled_connections()

asyncio.run(main())
"

echo "🔄 2. Replication Status Check"
curl -s http://localhost:8000/replication/status | python3 -m json.tool

echo "💾 3. Backup System Demonstration"
python src/backup.py

echo "📈 4. Database Performance Metrics"
curl -s http://localhost:8000/database/stats | python3 -m json.tool

echo "🧪 5. Load Testing with Concurrent Users"
python3 -c "
import asyncio
import httpx
import time
import random

async def create_test_load():
    async with httpx.AsyncClient() as client:
        tasks = []
        
        # Create multiple users concurrently
        for i in range(20):
            user_data = {
                'username': f'load_test_user_{i}_{int(time.time())}',
                'email': f'load_test_{i}_{int(time.time())}@example.com'
            }
            tasks.append(client.post('http://localhost:8000/users', json=user_data))
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        successful = sum(1 for r in responses if r.status_code == 200)
        print(f'Created {successful}/20 users in {end_time - start_time:.2f} seconds')
        
        # Create transactions for the users
        transaction_tasks = []
        for i in range(successful):
            transaction_data = {
                'user_id': i + 1,
                'amount': random.uniform(10.0, 1000.0),
                'transaction_type': random.choice(['deposit', 'withdrawal'])
            }
            transaction_tasks.append(client.post('http://localhost:8000/transactions', json=transaction_data))
        
        start_time = time.time()
        transaction_responses = await asyncio.gather(*transaction_tasks, return_exceptions=True)
        end_time = time.time()
        
        successful_transactions = sum(1 for r in transaction_responses if hasattr(r, 'status_code') and r.status_code == 200)
        print(f'Created {successful_transactions} transactions in {end_time - start_time:.2f} seconds')

asyncio.run(create_test_load())
"

echo "🎉 Demo completed! Check the dashboard at http://localhost:8000/dashboard"
