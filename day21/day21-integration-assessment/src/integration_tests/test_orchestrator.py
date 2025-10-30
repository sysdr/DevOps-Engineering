import asyncio
import json
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
import logging

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TestResult:
    test_name: str
    status: TestStatus
    duration: float
    error_message: str = None
    metrics: Dict[str, Any] = None

class IntegrationTestOrchestrator:
    def __init__(self, config_path: str = "config/test_config.json"):
        self.config = self._load_config(config_path)
        self.results: List[TestResult] = []
        self.session = None
        
    def _load_config(self, config_path: str) -> Dict:
        default_config = {
            "services": {
                # Point to built-in mock endpoints served by the main API on port 8000
                "user-service": {"url": "http://localhost:8000/mock/user-service", "health_check": "/health"},
                "order-service": {"url": "http://localhost:8000/mock/order-service", "health_check": "/health"},
                "payment-service": {"url": "http://localhost:8000/mock/payment-service", "health_check": "/health"}
            },
            "test_scenarios": [
                {
                    "name": "user_registration_flow",
                    "steps": ["create_user", "verify_email", "login"],
                    "timeout": 30
                },
                {
                    "name": "order_checkout_flow", 
                    "steps": ["add_to_cart", "checkout", "payment", "confirmation"],
                    "timeout": 45
                }
            ]
        }
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return default_config

    async def run_integration_tests(self) -> List[TestResult]:
        """Execute all integration test scenarios"""
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Health checks first
            await self._health_check_services()
            
            # Run test scenarios
            for scenario in self.config["test_scenarios"]:
                result = await self._run_scenario(scenario)
                self.results.append(result)
                
        return self.results

    async def _health_check_services(self):
        """Verify all services are healthy before testing"""
        for service_name, service_config in self.config["services"].items():
            try:
                async with self.session.get(
                    f"{service_config['url']}{service_config['health_check']}"
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Service {service_name} unhealthy: {response.status}")
            except Exception as e:
                logging.error(f"Health check failed for {service_name}: {e}")
                raise

    async def _run_scenario(self, scenario: Dict) -> TestResult:
        """Execute a specific test scenario"""
        start_time = time.time()
        
        try:
            for step in scenario["steps"]:
                await self._execute_step(step, scenario["name"])
                
            duration = time.time() - start_time
            return TestResult(
                test_name=scenario["name"],
                status=TestStatus.PASSED,
                duration=duration,
                metrics={"steps_completed": len(scenario["steps"])}
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=scenario["name"],
                status=TestStatus.FAILED,
                duration=duration,
                error_message=str(e)
            )

    async def _execute_step(self, step: str, scenario_name: str):
        """Execute individual test step"""
        # Simulate realistic test step execution
        if step == "create_user":
            await self._test_user_creation()
        elif step == "add_to_cart":
            await self._test_add_to_cart()
        elif step == "checkout":
            await self._test_checkout()
        # Add more step implementations as needed
        
        await asyncio.sleep(0.1)  # Simulate processing time

    async def _test_user_creation(self):
        """Test user creation endpoint"""
        user_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "testpass123"
        }
        
        async with self.session.post(
            f"{self.config['services']['user-service']['url']}/users",
            json=user_data
        ) as response:
            if response.status not in [200, 201]:
                raise Exception(f"User creation failed: {response.status}")

    async def _test_add_to_cart(self):
        """Test add to cart functionality"""
        cart_data = {
            "user_id": "test_user",
            "product_id": "test_product",
            "quantity": 1
        }
        
        async with self.session.post(
            f"{self.config['services']['order-service']['url']}/cart",
            json=cart_data
        ) as response:
            if response.status not in [200, 201]:
                raise Exception(f"Add to cart failed: {response.status}")

    async def _test_checkout(self):
        """Test checkout process"""
        checkout_data = {
            "user_id": "test_user",
            "payment_method": "credit_card"
        }
        
        async with self.session.post(
            f"{self.config['services']['order-service']['url']}/checkout",
            json=checkout_data
        ) as response:
            if response.status not in [200, 201]:
                raise Exception(f"Checkout failed: {response.status}")

    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in self.results if r.status == TestStatus.FAILED])
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "status": r.status.value,
                    "duration": r.duration,
                    "error_message": r.error_message,
                    "metrics": r.metrics
                }
                for r in self.results
            ]
        }
