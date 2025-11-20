#!/bin/bash

echo "=========================================="
echo "OpenTelemetry Demo - Creating Orders"
echo "=========================================="

# Wait for services
echo "Checking service health..."
for service in "localhost:8000" "localhost:8001" "localhost:8002"; do
    until curl -s "http://$service/health" > /dev/null 2>&1; do
        echo "Waiting for $service..."
        sleep 2
    done
    echo "✓ $service is ready"
done

echo ""
echo "Creating test orders..."

# Create multiple orders to generate traces
for i in {1..5}; do
    echo ""
    echo "Order $i:"
    curl -s -X POST http://localhost:8000/orders \
        -H "Content-Type: application/json" \
        -d "{
            \"customer_id\": \"CUST-$(printf %03d $i)\",
            \"items\": [
                {
                    \"product_id\": \"PROD-00$((i % 5 + 1))\",
                    \"quantity\": $((RANDOM % 3 + 1)),
                    \"price\": $((RANDOM % 100 + 10)).99
                }
            ],
            \"payment_method\": \"credit_card\"
        }" | python3 -m json.tool
    
    sleep 1
done

echo ""
echo "=========================================="
echo "Demo Complete!"
echo "=========================================="
echo ""
echo "View traces in Jaeger: http://localhost:16686"
echo "View metrics in Prometheus: http://localhost:9090"
echo "View dashboard: http://localhost:3000"
echo ""
echo "Try these Prometheus queries:"
echo "  - otel_orders_created_total"
echo "  - otel_payments_processed_total"
echo "  - histogram_quantile(0.95, otel_orders_processing_duration_bucket)"
