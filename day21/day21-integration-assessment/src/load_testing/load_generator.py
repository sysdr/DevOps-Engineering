import asyncio
import time
import json
import random
from typing import Dict, List, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import logging

@dataclass
class LoadTestConfig:
    target_url: str
    concurrent_users: int
    ramp_up_time: int
    test_duration: int
    request_patterns: List[Dict]

@dataclass
class LoadTestMetrics:
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float

class LoadTestGenerator:
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.response_times: List[float] = []
        self.error_count = 0
        self.success_count = 0
        self.start_time = None
        
    async def run_load_test(self) -> LoadTestMetrics:
        """Execute load testing with realistic traffic patterns"""
        self.start_time = time.time()
        
        # Create user behavior patterns
        user_scenarios = self._generate_user_scenarios()
        
        # Execute load test with ramping
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # Ramp up users gradually
            for i in range(self.config.concurrent_users):
                ramp_delay = (self.config.ramp_up_time / self.config.concurrent_users) * i
                task = asyncio.create_task(
                    self._user_scenario_runner(session, user_scenarios, ramp_delay)
                )
                tasks.append(task)
            
            # Wait for all users to complete
            await asyncio.gather(*tasks)
        
        return self._calculate_metrics()

    def _generate_user_scenarios(self) -> List[Dict]:
        """Generate realistic user behavior patterns"""
        scenarios = []
        
        # E-commerce user patterns
        ecommerce_pattern = {
            "name": "ecommerce_browse_buy",
            "steps": [
                {"endpoint": "/products", "method": "GET", "weight": 40},
                {"endpoint": "/products/search", "method": "GET", "weight": 30},
                {"endpoint": "/cart/add", "method": "POST", "weight": 20},
                {"endpoint": "/checkout", "method": "POST", "weight": 10}
            ]
        }
        
        # Social media user patterns  
        social_pattern = {
            "name": "social_engagement",
            "steps": [
                {"endpoint": "/feed", "method": "GET", "weight": 50},
                {"endpoint": "/posts/like", "method": "POST", "weight": 30},
                {"endpoint": "/posts/comment", "method": "POST", "weight": 15},
                {"endpoint": "/posts/share", "method": "POST", "weight": 5}
            ]
        }
        
        scenarios.extend([ecommerce_pattern, social_pattern])
        return scenarios

    async def _user_scenario_runner(self, session: aiohttp.ClientSession, 
                                  scenarios: List[Dict], ramp_delay: float):
        """Simulate individual user behavior"""
        await asyncio.sleep(ramp_delay)
        
        end_time = self.start_time + self.config.test_duration
        scenario = random.choice(scenarios)
        
        while time.time() < end_time:
            for step in scenario["steps"]:
                # Weighted random selection of requests
                if random.randint(1, 100) <= step["weight"]:
                    await self._make_request(session, step)
                    
            # Realistic user think time
            await asyncio.sleep(random.uniform(0.5, 3.0))

    async def _make_request(self, session: aiohttp.ClientSession, step: Dict):
        """Execute individual HTTP request with metrics collection"""
        url = f"{self.config.target_url}{step['endpoint']}"
        start_time = time.time()
        
        try:
            if step["method"] == "GET":
                async with session.get(url) as response:
                    await response.text()
                    response_time = time.time() - start_time
                    self._record_response(response.status, response_time)
                    
            elif step["method"] == "POST":
                # Generate realistic request data
                data = self._generate_request_data(step["endpoint"])
                async with session.post(url, json=data) as response:
                    await response.text()
                    response_time = time.time() - start_time
                    self._record_response(response.status, response_time)
                    
        except Exception as e:
            response_time = time.time() - start_time
            self._record_response(500, response_time)
            logging.error(f"Request failed: {e}")

    def _generate_request_data(self, endpoint: str) -> Dict:
        """Generate realistic request data based on endpoint"""
        if "cart" in endpoint:
            return {
                "product_id": random.randint(1, 1000),
                "quantity": random.randint(1, 5),
                "user_id": f"user_{random.randint(1, 10000)}"
            }
        elif "checkout" in endpoint:
            return {
                "payment_method": random.choice(["credit_card", "paypal", "apple_pay"]),
                "address": "123 Test Street"
            }
        elif "posts" in endpoint:
            return {
                "content": f"Test content {random.randint(1, 1000)}",
                "user_id": f"user_{random.randint(1, 10000)}"
            }
        return {}

    def _record_response(self, status_code: int, response_time: float):
        """Record response metrics"""
        self.response_times.append(response_time)
        if 200 <= status_code < 400:
            self.success_count += 1
        else:
            self.error_count += 1

    def _calculate_metrics(self) -> LoadTestMetrics:
        """Calculate comprehensive load test metrics"""
        if not self.response_times:
            return LoadTestMetrics(0, 0, 0, 0, 0, 0, 0, 100)
            
        total_requests = len(self.response_times)
        test_duration = time.time() - self.start_time
        
        # Sort response times for percentile calculations
        sorted_times = sorted(self.response_times)
        
        return LoadTestMetrics(
            total_requests=total_requests,
            successful_requests=self.success_count,
            failed_requests=self.error_count,
            average_response_time=sum(self.response_times) / len(self.response_times),
            p95_response_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_response_time=sorted_times[int(len(sorted_times) * 0.99)],
            requests_per_second=total_requests / test_duration,
            error_rate=(self.error_count / total_requests) * 100
        )
