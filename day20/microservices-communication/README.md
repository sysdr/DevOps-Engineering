# Day 20: Microservices Communication Patterns

This project demonstrates microservices communication patterns including:

- Synchronous REST API communication with circuit breakers
- Asynchronous event-driven messaging using Kafka
- Service discovery with health checks
- CQRS pattern implementation
- Distributed transaction patterns

## Architecture

- **API Gateway** (Port 8000): Routes requests and implements circuit breakers
- **User Service** (Port 8001): Manages user data and publishes user events
- **Order Service** (Port 8002): Handles orders and publishes order events
- **Notification Service** (Port 8003): Consumes events and sends notifications
- **React Dashboard** (Port 3000): Modern UI for system monitoring

## Quick Start

1. **Setup and Start:**
   ```bash
   ./start.sh
   ```

2. **Access Dashboard:**
   - Open http://localhost:3000
   - Create users and orders to see event flow

3. **Run Tests:**
   ```bash
   source venv/bin/activate
   python -m pytest tests/ -v
   ```

4. **Stop Services:**
   ```bash
   ./stop.sh
   ```

## Features Demonstrated

- **Circuit Breaker Pattern**: Automatic failure detection and recovery
- **Event Sourcing**: All state changes captured as events
- **Service Discovery**: Dynamic service location and health monitoring
- **Asynchronous Processing**: Kafka-based event streaming
- **Modern UI**: Professional dashboard with real-time updates

## Testing the System

1. Create users through the dashboard
2. Watch notifications appear automatically
3. Create orders and observe event flow
4. Monitor circuit breaker states
5. Test failure scenarios by stopping services

The system demonstrates resilient microservices communication with production-ready patterns.
