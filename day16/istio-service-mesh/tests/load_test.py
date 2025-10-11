import asyncio
import aiohttp
import time
import statistics

async def make_request(session, url):
    """Make a single HTTP request"""
    start_time = time.time()
    try:
        async with session.get(url, timeout=10) as response:
            await response.text()
            return time.time() - start_time, response.status
    except Exception as e:
        return time.time() - start_time, 0

async def load_test():
    """Perform load testing on the services"""
    base_url = "http://localhost:8080"
    endpoints = [
        f"{base_url}/users",
        f"{base_url}/products", 
        f"{base_url}/users/1",
        f"{base_url}/products/1",
        f"{base_url}/recommendations/1"
    ]
    
    concurrent_requests = 50
    total_requests = 1000
    
    print(f"🚀 Starting load test: {total_requests} requests, {concurrent_requests} concurrent")
    
    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        start_time = time.time()
        
        for i in range(total_requests):
            endpoint = endpoints[i % len(endpoints)]
            task = make_request(session, endpoint)
            tasks.append(task)
            
            # Control concurrency
            if len(tasks) >= concurrent_requests:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []
        
        # Complete remaining tasks
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
    
    print(f"✅ Load test completed in {total_time:.2f} seconds")
    print(f"📊 Average throughput: {total_requests/total_time:.2f} requests/second")

if __name__ == "__main__":
    asyncio.run(load_test())
