import os
import uuid
import random
import asyncio
import structlog
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.trace import Status, StatusCode

# Configuration
SERVICE_NAME = "payment-service"
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

# Setup OpenTelemetry
resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: SERVICE_NAME,
    ResourceAttributes.SERVICE_VERSION: "1.0.0",
    ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "development"
})

# Tracing
trace_provider = TracerProvider(resource=resource)
trace_exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

# Metrics
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True),
    export_interval_millis=5000
)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

# Custom Metrics
payments_processed = meter.create_counter(
    "payments.processed.total",
    description="Total payments processed",
    unit="1"
)

payments_succeeded = meter.create_counter(
    "payments.succeeded.total",
    description="Successful payments",
    unit="1"
)

payments_failed = meter.create_counter(
    "payments.failed.total",
    description="Failed payments",
    unit="1"
)

payment_amount = meter.create_histogram(
    "payments.amount",
    description="Payment amount distribution",
    unit="USD"
)

payment_duration = meter.create_histogram(
    "payments.processing.duration",
    description="Payment processing duration",
    unit="ms"
)

# Structured Logging
def add_trace_context(logger, method_name, event_dict):
    span = trace.get_current_span()
    if span:
        ctx = span.get_span_context()
        if ctx.is_valid:
            event_dict["trace_id"] = format(ctx.trace_id, '032x')
            event_dict["span_id"] = format(ctx.span_id, '016x')
    return event_dict

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_trace_context,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(SERVICE_NAME)
LoggingInstrumentor().instrument(set_logging_format=True)

# Models
class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    method: str
    customer_id: str

class PaymentResponse(BaseModel):
    transaction_id: str
    order_id: str
    status: str
    amount: float
    method: str
    processed_at: str

# Simulated payment processing
payments_db: dict[str, PaymentResponse] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("payment_service_starting", service=SERVICE_NAME)
    yield
    logger.info("payment_service_stopping", service=SERVICE_NAME)
    trace_provider.shutdown()
    meter_provider.shutdown()

app = FastAPI(
    title="Payment Service",
    description="Payment processing with OpenTelemetry",
    version="1.0.0",
    lifespan=lifespan
)

FastAPIInstrumentor.instrument_app(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": SERVICE_NAME}

@app.post("/payments/process", response_model=PaymentResponse)
async def process_payment(request: PaymentRequest):
    start_time = datetime.now()
    
    with tracer.start_as_current_span("process_payment") as span:
        span.set_attribute("order.id", request.order_id)
        span.set_attribute("payment.amount", request.amount)
        span.set_attribute("payment.method", request.method)
        span.set_attribute("customer.id", request.customer_id)
        
        payments_processed.add(1, {"method": request.method})
        payment_amount.record(request.amount, {"method": request.method})
        
        transaction_id = str(uuid.uuid4())
        span.set_attribute("transaction.id", transaction_id)
        
        logger.info(
            "payment_processing_started",
            order_id=request.order_id,
            transaction_id=transaction_id,
            amount=request.amount,
            method=request.method
        )
        
        # Validate payment
        with tracer.start_as_current_span("validate_payment") as val_span:
            val_span.set_attribute("validation.type", "card")
            
            # Simulate validation
            await asyncio.sleep(random.uniform(0.01, 0.03))
            
            # Simulate occasional validation failures (5% chance)
            if random.random() < 0.05:
                val_span.set_status(Status(StatusCode.ERROR, "Card validation failed"))
                val_span.add_event("validation_failed", {"reason": "invalid_card"})
                logger.error(
                    "payment_validation_failed",
                    order_id=request.order_id,
                    transaction_id=transaction_id
                )
                payments_failed.add(1, {"method": request.method, "reason": "validation"})
                raise HTTPException(status_code=400, detail="Card validation failed")
            
            val_span.add_event("validation_passed")
        
        # Process with payment gateway
        with tracer.start_as_current_span("payment_gateway") as gw_span:
            gw_span.set_attribute("gateway.name", "stripe")
            gw_span.set_attribute("gateway.region", "us-east-1")
            
            # Simulate gateway processing
            await asyncio.sleep(random.uniform(0.05, 0.15))
            
            # Simulate occasional gateway errors (3% chance)
            if random.random() < 0.03:
                gw_span.set_status(Status(StatusCode.ERROR, "Gateway timeout"))
                gw_span.add_event("gateway_error", {"error": "timeout"})
                logger.error(
                    "payment_gateway_error",
                    order_id=request.order_id,
                    transaction_id=transaction_id
                )
                payments_failed.add(1, {"method": request.method, "reason": "gateway"})
                raise HTTPException(status_code=503, detail="Payment gateway error")
            
            gw_span.add_event("gateway_success", {"gateway_ref": f"GW-{uuid.uuid4().hex[:8]}"})
        
        # Record success
        payment = PaymentResponse(
            transaction_id=transaction_id,
            order_id=request.order_id,
            status="completed",
            amount=request.amount,
            method=request.method,
            processed_at=datetime.utcnow().isoformat()
        )
        
        payments_db[transaction_id] = payment
        
        duration = (datetime.now() - start_time).total_seconds() * 1000
        payment_duration.record(duration, {"method": request.method, "status": "success"})
        payments_succeeded.add(1, {"method": request.method})
        
        span.set_status(Status(StatusCode.OK))
        logger.info(
            "payment_completed",
            order_id=request.order_id,
            transaction_id=transaction_id,
            duration_ms=duration
        )
        
        return payment

@app.get("/payments/{transaction_id}", response_model=PaymentResponse)
async def get_payment(transaction_id: str):
    with tracer.start_as_current_span("get_payment") as span:
        span.set_attribute("transaction.id", transaction_id)
        
        if transaction_id not in payments_db:
            span.set_status(Status(StatusCode.ERROR, "Payment not found"))
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return payments_db[transaction_id]

@app.get("/payments")
async def list_payments():
    with tracer.start_as_current_span("list_payments") as span:
        span.set_attribute("payments.count", len(payments_db))
        return list(payments_db.values())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
