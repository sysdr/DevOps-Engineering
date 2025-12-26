import asyncio
import asyncpg
import numpy as np
from datetime import datetime, timedelta
import json

async def generate_test_data(num_samples=1000):
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        user='postgres',
        password='postgres',
        database='monitoring'
    )
    
    print(f"Generating {num_samples} test predictions...")
    
    base_time = datetime.utcnow() - timedelta(hours=24)
    
    for i in range(num_samples):
        timestamp = base_time + timedelta(seconds=i * 86)
        
        features = {
            'amount': float(np.random.normal(100, 30)),
            'frequency': float(np.random.normal(5, 2)),
            'recency': float(np.random.exponential(10))
        }
        
        # Simulate prediction with some correlation to features
        prediction = 1 / (1 + np.exp(-(features['amount'] / 100 + features['frequency'] / 5) + np.random.normal(0, 0.5)))
        ground_truth = 1 if prediction > 0.5 else 0
        
        await conn.execute('''
            INSERT INTO predictions 
            (timestamp, model_id, prediction_id, features, prediction, ground_truth)
            VALUES ($1, $2, $3, $4, $5, $6)
        ''', timestamp, 'default', f'pred-{i}',
            json.dumps(features), float(prediction), ground_truth)
    
    print(f"✓ Generated {num_samples} test predictions")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(generate_test_data())
