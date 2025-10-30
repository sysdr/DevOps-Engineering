from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uvicorn
from datetime import datetime
import json

from integration_tests.test_orchestrator import IntegrationTestOrchestrator
from load_testing.load_generator import LoadTestGenerator, LoadTestConfig
from monitoring.performance_monitor import PerformanceMonitor
from documentation.doc_generator import DocumentationGenerator
from cost_analysis.cost_analyzer import CostAnalyzer

app = FastAPI(title="Phase 1 Integration Assessment API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
integration_orchestrator = IntegrationTestOrchestrator()
performance_monitor = PerformanceMonitor()
doc_generator = DocumentationGenerator()
cost_analyzer = CostAnalyzer()

# Mock services for demonstration
mock_services = {
    "user-service": {"status": "healthy", "url": "http://localhost:8000/mock/user-service"},
    "order-service": {"status": "healthy", "url": "http://localhost:8000/mock/order-service"},
    "payment-service": {"status": "healthy", "url": "http://localhost:8000/mock/payment-service"}
}

@app.get("/")
async def root():
    return {
        "message": "Phase 1 Integration Assessment API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "status": "operational"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "services": mock_services,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/integration-tests/run")
async def run_integration_tests():
    """Run comprehensive integration tests"""
    try:
        results = await integration_orchestrator.run_integration_tests()
        report = integration_orchestrator.generate_report()
        
        return {
            "status": "completed",
            "results": [
                {
                    "id": i + 1,
                    "name": result.test_name,
                    "status": result.status.value,
                    "duration": result.duration,
                    "timestamp": datetime.now().isoformat(),
                    "details": result.error_message or "Test completed successfully"
                }
                for i, result in enumerate(results)
            ],
            "summary": report["summary"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integration test failed: {str(e)}")

@app.post("/api/load-tests/run")
async def run_load_tests(concurrent_users: int = 10, test_duration: int = 60):
    """Run load testing with specified parameters"""
    try:
        config = LoadTestConfig(
            target_url="http://localhost:8000",
            concurrent_users=concurrent_users,
            ramp_up_time=10,
            test_duration=test_duration,
            request_patterns=[]
        )
        
        load_generator = LoadTestGenerator(config)
        metrics = await load_generator.run_load_test()
        
        return {
            "status": "completed",
            "metrics": {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "average_response_time": metrics.average_response_time,
                "p95_response_time": metrics.p95_response_time,
                "p99_response_time": metrics.p99_response_time,
                "requests_per_second": metrics.requests_per_second,
                "error_rate": metrics.error_rate
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Load test failed: {str(e)}")

@app.get("/api/performance/report")
async def get_performance_report():
    """Get comprehensive performance report"""
    try:
        report = performance_monitor.get_performance_report()
        return {
            "status": "success",
            "report": report,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance report failed: {str(e)}")

@app.post("/api/documentation/generate")
async def generate_documentation(doc_type: str = "architecture"):
    """Generate system documentation"""
    try:
        if doc_type == "architecture":
            content = doc_generator.generate_architecture_docs("config/")
        elif doc_type == "runbook":
            content = doc_generator.generate_runbook({})
        elif doc_type == "api":
            content = doc_generator.generate_api_docs("api_spec.yaml")
        else:
            raise HTTPException(status_code=400, detail="Invalid documentation type")
        
        filepath = doc_generator.save_documentation(doc_type, content, "docs/")
        
        return {
            "status": "generated",
            "type": doc_type,
            "filepath": filepath,
            "content_preview": content[:500] + "..." if len(content) > 500 else content,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Documentation generation failed: {str(e)}")

@app.get("/api/cost-analysis/report")
async def get_cost_analysis():
    """Get cost analysis and optimization recommendations"""
    try:
        # Generate mock usage data for demonstration
        mock_usage = [
            {
                "resource_type": "compute",
                "instance_type": "t3.medium",
                "hours_used": 24,
                "cpu_utilization": 25,
                "memory_utilization": 30
            },
            {
                "resource_type": "compute", 
                "instance_type": "t3.large",
                "hours_used": 24,
                "cpu_utilization": 75,
                "memory_utilization": 80
            },
            {
                "resource_type": "database",
                "instance_type": "db.t3.small",
                "hours_used": 24,
                "cpu_utilization": 40,
                "memory_utilization": 50
            }
        ]
        
        analysis = cost_analyzer.analyze_resource_usage(mock_usage)
        report_content = cost_analyzer.generate_cost_report()
        
        return {
            "status": "completed",
            "analysis": analysis,
            "report": report_content,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost analysis failed: {str(e)}")

""" Mock service endpoints to support local integration tests """

@app.get("/mock/user-service/health")
async def mock_user_service_health():
    return {"status": "ok"}

@app.post("/mock/user-service/users")
async def mock_user_service_create_user():
    return {"id": "mock_user_id", "status": "created"}

@app.get("/mock/order-service/health")
async def mock_order_service_health():
    return {"status": "ok"}

@app.post("/mock/order-service/cart")
async def mock_order_service_add_to_cart():
    return {"cart_id": "mock_cart_id", "status": "added"}

@app.post("/mock/order-service/checkout")
async def mock_order_service_checkout():
    return {"order_id": "mock_order_id", "status": "processed"}

@app.get("/mock/payment-service/health")
async def mock_payment_service_health():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting Phase 1 Integration Assessment API")
    print("📊 Performance monitoring initialized")
    print("🔧 Integration testing framework ready")
    print("⚡ Load testing engine prepared")
    print("📖 Documentation generator available")
    print("💰 Cost analyzer operational")
    # Start performance monitoring background tasks
    try:
        asyncio.create_task(performance_monitor.start_monitoring())
    except Exception as e:
        print(f"Failed to start performance monitoring: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
