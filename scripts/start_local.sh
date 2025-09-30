#!/bin/bash

# BigQuery Analytics AI Agent - Local Startup Script
# This script starts both backend and frontend services

echo "🚀 Starting BigQuery Analytics AI Agent..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Function to start backend
start_backend() {
    echo -e "${YELLOW}Starting Backend API...${NC}"
    cd "$PROJECT_ROOT/genai-agents-backend"
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        echo -e "${RED}❌ .env file not found in genai-agents-backend/${NC}"
        echo "Please copy .env.example to .env and configure your settings"
        exit 1
    fi
    
    # Start backend in background
    python3 app.py &
    BACKEND_PID=$!
    echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID) on http://localhost:8010${NC}"
}

# Function to start frontend
start_frontend() {
    echo -e "${YELLOW}Starting Frontend UI...${NC}"
    cd "$PROJECT_ROOT/gradio-chatbot"
    
    # Wait for backend to be ready
    echo "Waiting for backend to be ready..."
    sleep 5
    
    # Start frontend in background
    python3 app.py &
    FRONTEND_PID=$!
    echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID) on http://localhost:7860${NC}"
}

# Function to stop services
stop_services() {
    echo -e "\n${YELLOW}Stopping services...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo -e "${GREEN}✓ Backend stopped${NC}"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    fi
    
    # Kill any remaining python processes on ports 8010 and 7860
    lsof -ti:8010 | xargs kill -9 2>/dev/null
    lsof -ti:7860 | xargs kill -9 2>/dev/null
    
    exit 0
}

# Set up trap to handle Ctrl+C
trap stop_services INT

# Main execution
echo -e "${GREEN}Project Root: $PROJECT_ROOT${NC}"
echo "================================================"

# Start services
start_backend
sleep 3
start_frontend

echo "================================================"
echo -e "${GREEN}✅ All services started successfully!${NC}"
echo ""
echo "🌐 Backend API: http://localhost:8010"
echo "🎨 Frontend UI: http://localhost:7860"
echo "📚 API Docs: http://localhost:8010/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "================================================"

# Keep script running
while true; do
    sleep 1
done