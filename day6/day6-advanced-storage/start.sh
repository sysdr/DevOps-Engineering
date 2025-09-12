#!/bin/bash

echo "🚀 Starting Advanced Storage & Database Patterns Application"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
sleep 30

# Run database migrations/setup
echo "🗄️ Setting up database..."
python3 -c "
import asyncio
import asyncpg

async def wait_for_db():
    for i in range(30):
        try:
            conn = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='admin',
                password='secure_password_123',
                database='productiondb'
            )
            await conn.close()
            print('✅ Primary database ready')
            break
        except Exception as e:
            print(f'Waiting for database... ({i+1}/30)')
            await asyncio.sleep(2)
    else:
        print('❌ Database connection timeout')

asyncio.run(wait_for_db())
"

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Start the application
echo "🌟 Starting application server..."
python src/main.py &
APP_PID=$!

# Run backup demo
echo "💾 Running backup demonstration..."
sleep 10
python src/backup.py

echo "✅ Application started successfully!"
echo "🌐 Dashboard: http://localhost:8000/dashboard"
echo "📊 API Documentation: http://localhost:8000/docs"
echo "📈 Prometheus Metrics: http://localhost:9090"
echo "📊 Grafana Dashboard: http://localhost:3001 (admin/admin123)"
echo ""
echo "Press Ctrl+C to stop the application"

# Keep the script running
wait $APP_PID
