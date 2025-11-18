#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting GitOps Observability Platform...${NC}"

# Setup Python virtual environment
echo -e "${GREEN}Setting up Python environment...${NC}"
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run tests
echo -e "${GREEN}Running backend tests...${NC}"
python -m pytest tests/ -v

# Start backend
echo -e "${GREEN}Starting backend server...${NC}"
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
echo $! > ../backend.pid
cd ..

# Wait for backend
sleep 3

# Setup and start frontend
echo -e "${GREEN}Setting up frontend...${NC}"
cd frontend
npm install
echo -e "${GREEN}Starting frontend server...${NC}"
nohup npm start > ../frontend.log 2>&1 &
echo $! > ../frontend.pid
cd ..

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}GitOps Observability Platform Started!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Dashboard: http://localhost:3000"
echo "API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Health: http://localhost:8000/health"
echo ""
echo "Logs: backend.log, frontend.log"
echo "Stop with: ./stop.sh"
