#!/bin/bash

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "🚀 Starting Microservices Communication Platform..."

# Function to check if port is in use
check_port() {
    if command -v ss >/dev/null 2>&1; then
        if ss -tuln | grep -q ":$1 " 2>/dev/null; then
            echo "Port $1 is already in use"
            return 1
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -tuln | grep -q ":$1 " 2>/dev/null; then
            echo "Port $1 is already in use"
            return 1
        fi
    elif command -v lsof >/dev/null 2>&1; then
        if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "Port $1 is already in use"
            return 1
        fi
    fi
    return 0
}

# Check required ports
echo "📋 Checking required ports..."
ports=(3000 8000 8001 8002 8003 9092 2181)
for port in "${ports[@]}"; do
    if ! check_port $port; then
        echo "❌ Port $port is in use. Please free it and try again."
        exit 1
    fi
done

# Start infrastructure services
echo "🐳 Starting infrastructure services..."
cd "$PROJECT_DIR/docker"
docker-compose up -d
cd "$PROJECT_DIR"

# Wait for services to be ready
echo "⏳ Waiting for infrastructure services to be ready..."
sleep 10

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source "$PROJECT_DIR/venv/bin/activate"

# Create Kafka topics
echo "📝 Creating Kafka topics..."
docker exec $(docker ps -q -f name=kafka) kafka-topics --create --topic user-events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists 2>/dev/null || echo "Topic user-events already exists"
docker exec $(docker ps -q -f name=kafka) kafka-topics --create --topic order-events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists 2>/dev/null || echo "Topic order-events already exists"

# Start microservices
echo "🚀 Starting microservices..."
cd "$PROJECT_DIR/api-gateway" && python app/main.py > "$PROJECT_DIR/api-gateway.log" 2>&1 &
cd "$PROJECT_DIR/user-service" && python app/main.py > "$PROJECT_DIR/user-service.log" 2>&1 &
cd "$PROJECT_DIR/order-service" && python app/main.py > "$PROJECT_DIR/order-service.log" 2>&1 &
cd "$PROJECT_DIR/notification-service" && python app/main.py > "$PROJECT_DIR/notification-service.log" 2>&1 &

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 15

# Start frontend
echo "🌐 Installing frontend dependencies and starting React app..."
cd "$PROJECT_DIR/frontend"
npm install
npm start > "$PROJECT_DIR/frontend.log" 2>&1 &
cd "$PROJECT_DIR"

echo "✅ All services started successfully!"
echo ""
echo "🔗 Access URLs:"
echo "  • Dashboard: http://localhost:3000"
echo "  • API Gateway: http://localhost:8000"
echo "  • User Service: http://localhost:8001"
echo "  • Order Service: http://localhost:8002"
echo "  • Notification Service: http://localhost:8003"
echo ""
echo "📊 API Documentation:"
echo "  • Gateway API: http://localhost:8000/docs"
echo "  • User Service API: http://localhost:8001/docs"
echo "  • Order Service API: http://localhost:8002/docs"
echo "  • Notification Service API: http://localhost:8003/docs"
echo ""
echo "🧪 Run tests with: source venv/bin/activate && python -m pytest tests/ -v"
echo "🛑 Stop services with: ./stop.sh"
