import asyncio
import aiohttp
import time
from collections import defaultdict

async def send_request(session, user_id):
    """Send single request"""
    try:
        async with session.get(
            f"http://localhost:8000/api/user/{user_id}",
            headers={"x-user-lat": "40.7", "x-user-lon": "-74.0"}
        ) as response:
            return response.status == 200
    except:
        return False

async def load_test(duration=60, target_rps=10000):
    """Generate load for specified duration"""
    print(f"Starting load test: {target_rps} RPS for {duration} seconds")
    
    connector = aiohttp.TCPConnector(limit=1000)
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        start_time = time.time()
        request_count = 0
        success_count = 0
        
        while time.time() - start_time < duration:
            batch_start = time.time()
            
            # Send batch of requests
            tasks = [
                send_request(session, f"user_{i}")
                for i in range(target_rps // 10)  # 100ms batches
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            request_count += len(results)
            success_count += sum(1 for r in results if r is True)
            
            # Sleep to maintain target RPS
            elapsed = time.time() - batch_start
            sleep_time = 0.1 - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        elapsed = time.time() - start_time
        actual_rps = request_count / elapsed
        success_rate = (success_count / request_count) * 100
        
        print(f"\nLoad Test Results:")
        print(f"Duration: {elapsed:.1f}s")
        print(f"Requests: {request_count:,}")
        print(f"Success: {success_count:,} ({success_rate:.1f}%)")
        print(f"RPS: {actual_rps:,.0f}")

if __name__ == "__main__":
    asyncio.run(load_test(duration=60, target_rps=10000))
