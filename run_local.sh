#!/bin/bash

# BigQuery Analytics AI Agent - Local Run Script
# Runs backend on port 8010 and frontend on port 7860

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/genai-agents-backend"
FRONTEND_DIR="$PROJECT_ROOT/gradio-chatbot"

# Log file
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  BigQuery Analytics AI Agent${NC}"
echo -e "${BLUE}  Local Development Environment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    echo -e "${YELLOW}Killing process on port $port...${NC}"
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
    sleep 2
}

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    kill_port 8010
    kill_port 7860
    echo -e "${GREEN}Services stopped.${NC}"
    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup SIGINT SIGTERM

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please create .env file with required configuration.${NC}"
    exit 1
fi

# Check backend port
if check_port 8010; then
    echo -e "${YELLOW}Port 8010 is already in use.${NC}"
    read -p "Kill existing process? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill_port 8010
    else
        echo -e "${RED}Cannot start backend. Exiting.${NC}"
        exit 1
    fi
fi

# Check frontend port
if check_port 7860; then
    echo -e "${YELLOW}Port 7860 is already in use.${NC}"
    read -p "Kill existing process? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill_port 7860
    else
        echo -e "${RED}Cannot start frontend. Exiting.${NC}"
        exit 1
    fi
fi

# Start Backend
echo -e "${BLUE}Starting Backend on port 8010...${NC}"
cd "$BACKEND_DIR"
python app.py > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
echo -e "  Log: $BACKEND_LOG"

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8010/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Backend failed to start. Check logs: $BACKEND_LOG${NC}"
        tail -20 "$BACKEND_LOG"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Start Frontend
echo -e "${BLUE}Starting Frontend on port 7860...${NC}"
cd "$FRONTEND_DIR"
python app.py > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo -e "  Log: $FRONTEND_LOG"

# Wait for frontend to be ready
echo -e "${YELLOW}Waiting for frontend to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:7860 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Frontend failed to start. Check logs: $FRONTEND_LOG${NC}"
        tail -20 "$FRONTEND_LOG"
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Display status
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Services Running Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Backend:${NC}  http://localhost:8010"
echo -e "${BLUE}Frontend:${NC} http://localhost:7860"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend:  $BACKEND_LOG"
echo -e "  Frontend: $FRONTEND_LOG"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Monitor processes
while true; do
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}✗ Backend process died unexpectedly!${NC}"
        echo -e "Last 20 lines of backend log:"
        tail -20 "$BACKEND_LOG"
        kill $FRONTEND_PID 2>/dev/null || true
        exit 1
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}✗ Frontend process died unexpectedly!${NC}"
        echo -e "Last 20 lines of frontend log:"
        tail -20 "$FRONTEND_LOG"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    
    sleep 5
done
