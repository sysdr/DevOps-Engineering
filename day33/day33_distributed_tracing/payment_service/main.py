from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import random
import logging
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize tracing
resource = Resource.create({"service.name": "payment-service"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

app = FastAPI(title="Payment Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app)

class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    customer_id: str

@app.get("/")
async def root():
    return {
        "service": "payment-service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "process_payment": "POST /payments/process",
            "get_payment": "GET /payments/{transaction_id}",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "payment"}

@app.post("/payments/process")
async def process_payment(payment: PaymentRequest):
    span = trace.get_current_span()
    span.set_attribute("payment.order_id", payment.order_id)
    span.set_attribute("payment.amount", payment.amount)
    span.set_attribute("payment.customer_id", payment.customer_id)
    
    trace_id = format(span.get_span_context().trace_id, '032x')
    logger.info(f"Processing payment for order {payment.order_id}, amount: ${payment.amount}, trace_id: {trace_id}")
    
    # Validate payment details
    with tracer.start_as_current_span("validate_payment") as validate_span:
        validate_span.set_attribute("validation.type", "payment")
        await asyncio.sleep(0.010)
        
        if payment.amount <= 0:
            validate_span.set_status(Status(StatusCode.ERROR, "Invalid amount"))
            raise HTTPException(status_code=400, detail="Invalid payment amount")
    
    # Call payment gateway
    with tracer.start_as_current_span("payment_gateway_call") as gateway_span:
        gateway_span.set_attribute("gateway.provider", "stripe")
        gateway_span.set_attribute("gateway.amount", payment.amount)
        
        # Simulate payment gateway latency
        await asyncio.sleep(0.030)
        
        # Simulate occasional payment failures (5% failure rate)
        if random.random() < 0.05:
            gateway_span.set_status(Status(StatusCode.ERROR, "Payment declined"))
            logger.error(f"Payment declined for order {payment.order_id}, trace_id: {trace_id}")
            raise HTTPException(status_code=400, detail="Payment declined")
        
        transaction_id = f"TXN-{random.randint(100000, 999999)}"
        gateway_span.set_attribute("transaction.id", transaction_id)
    
    # Record transaction
    with tracer.start_as_current_span("record_transaction") as record_span:
        record_span.set_attribute("db.system", "postgresql")
        record_span.set_attribute("db.operation", "INSERT")
        record_span.set_attribute("transaction.id", transaction_id)
        await asyncio.sleep(0.015)
    
    logger.info(f"Payment processed successfully, transaction: {transaction_id}, trace_id: {trace_id}")
    
    return {
        "status": "success",
        "transaction_id": transaction_id,
        "amount": payment.amount
    }

@app.get("/payments/{transaction_id}")
async def get_payment(transaction_id: str):
    span = trace.get_current_span()
    span.set_attribute("transaction.id", transaction_id)
    
    return {
        "transaction_id": transaction_id,
        "status": "completed",
        "amount": 299.99
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
