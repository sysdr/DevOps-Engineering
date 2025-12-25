import asyncio
import aiohttp
import time
from statistics import mean, median
import random

async def make_prediction(session, url):
    features = [
        random.uniform(4.0, 8.0),
        random.uniform(2.0, 4.5),
        random.uniform(1.0, 7.0),
        random.uniform(0.1, 2.5)
    ]
    
    start = time.time()
    try:
        async with session.post(
            f"{url}/v1/models/predict",
            json={"instances": [features]}
        ) as response:
            await response.json()
            latency = (time.time() - start) * 1000
            return {"success": True, "latency": latency, "status": response.status}
    except Exception as e:
        return {"success": False, "latency": 0, "error": str(e)}

async def run_load_test(url, num_requests, concurrency):
    print(f"Starting load test: {num_requests} requests with concurrency {concurrency}")
    
    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        start_time = time.time()
        
        tasks = [make_prediction(session, url) for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        
        duration = time.time() - start_time
        
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        latencies = [r["latency"] for r in successful]
        
        print("\n=== Load Test Results ===")
        print(f"Total requests: {num_requests}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Requests/sec: {num_requests / duration:.2f}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        
        if latencies:
            print(f"\nLatency Statistics:")
            print(f"  Mean: {mean(latencies):.2f} ms")
            print(f"  Median: {median(latencies):.2f} ms")
            print(f"  Min: {min(latencies):.2f} ms")
            print(f"  Max: {max(latencies):.2f} ms")
            print(f"  P95: {sorted(latencies)[int(len(latencies) * 0.95)]:.2f} ms")
            print(f"  P99: {sorted(latencies)[int(len(latencies) * 0.99)]:.2f} ms")

if __name__ == "__main__":
    url = "http://localhost:8000"
    asyncio.run(run_load_test(url, num_requests=1000, concurrency=50))
