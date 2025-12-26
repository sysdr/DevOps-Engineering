import asyncio
import asyncpg

async def init_database():
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        user='postgres',
        password='postgres',
        database='postgres'
    )
    
    # Create database
    try:
        await conn.execute('CREATE DATABASE monitoring')
        print("✓ Database created")
    except asyncpg.exceptions.DuplicateDatabaseError:
        print("✓ Database already exists")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(init_database())
