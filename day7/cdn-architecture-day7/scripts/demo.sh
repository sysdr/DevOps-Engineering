#!/bin/bash

echo "🎬 CDN Architecture Demo - Automated Testing"
echo "============================================"

API_URL="http://localhost:8080/api"

echo "🌍 Testing geographic routing..."

# Test requests from different locations
locations=(
    '{"resource":"homepage.html","lat":40.7128,"lng":-74.0060,"ip":"192.168.1.1","location":"New York"}'
    '{"resource":"homepage.html","lat":51.5074,"lng":-0.1278,"ip":"192.168.1.2","location":"London"}'
    '{"resource":"homepage.html","lat":35.6762,"lng":139.6503,"ip":"192.168.1.3","location":"Tokyo"}'
    '{"resource":"homepage.html","lat":19.0760,"lng":72.8777,"ip":"192.168.1.4","location":"Mumbai"}'
)

for location in "${locations[@]}"; do
    echo "📍 Testing from: $(echo $location | jq -r '.location')"
    response=$(curl -s -X POST $API_URL/cdn/request \
        -H "Content-Type: application/json" \
        -d "$location")
    
    edge_node=$(echo $response | jq -r '.edge_node.region')
    cache_hit=$(echo $response | jq -r '.cache_hit')
    response_time=$(echo $response | jq -r '.response_time_ms')
    
    echo "   🏢 Routed to: $edge_node"
    echo "   💾 Cache hit: $cache_hit"
    echo "   ⏱️  Response time: ${response_time}ms"
    echo ""
done

echo "📊 Getting overall metrics..."
metrics=$(curl -s $API_URL/cdn/metrics)
total_requests=$(echo $metrics | jq -r '.overview.total_requests')
cache_hit_rate=$(echo $metrics | jq -r '.overview.cache_hit_rate')
avg_response_time=$(echo $metrics | jq -r '.overview.avg_response_time')

echo "📈 Performance Summary:"
echo "   📨 Total requests: $total_requests"
echo "   💾 Cache hit rate: $cache_hit_rate%"
echo "   ⏱️  Avg response time: ${avg_response_time}ms"
echo ""

echo "🧹 Testing cache invalidation..."
curl -s -X POST $API_URL/cdn/invalidate \
    -H "Content-Type: application/json" \
    -d '{"resource":"homepage.html","regions":["us-east","eu-west"]}'

echo "✅ Cache invalidated for homepage.html"
echo ""

echo "🔄 Testing request after invalidation (should be cache miss)..."
response=$(curl -s -X POST $API_URL/cdn/request \
    -H "Content-Type: application/json" \
    -d '{"resource":"homepage.html","lat":40.7128,"lng":-74.0060,"ip":"192.168.1.1"}')

cache_hit=$(echo $response | jq -r '.cache_hit')
echo "   💾 Cache hit after invalidation: $cache_hit"

echo ""
echo "🎉 Demo completed! Visit http://localhost:3000 to explore the dashboard"
