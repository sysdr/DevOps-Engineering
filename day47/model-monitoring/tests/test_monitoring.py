import asyncio
import asyncpg
from datetime import datetime
import sys
sys.path.append('backend')

async def test_database_connection():
    """Test database connection"""
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        user='postgres',
        password='postgres',
        database='monitoring'
    )
    assert conn is not None
    await conn.close()
    print("✓ Database connection test passed")

async def test_prediction_storage():
    """Test prediction storage"""
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        user='postgres',
        password='postgres',
        database='monitoring'
    )
    
    # Store test prediction
    await conn.execute('''
        INSERT INTO predictions 
        (timestamp, model_id, prediction_id, features, prediction, ground_truth)
        VALUES ($1, $2, $3, $4, $5, $6)
    ''', datetime.utcnow(), 'test-model', 'test-pred-1',
        '{"amount": 100.0, "frequency": 5}', 0.75, 1)
    
    # Verify storage
    result = await conn.fetchval(
        'SELECT COUNT(*) FROM predictions WHERE model_id = $1',
        'test-model'
    )
    
    assert result > 0
    await conn.close()
    print("✓ Prediction storage test passed")

if __name__ == "__main__":
    asyncio.run(test_database_connection())
    asyncio.run(test_prediction_storage())
    print("\n✓ All tests passed!")
