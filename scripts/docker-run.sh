#!/bin/bash

# Docker Build and Run Script for ADK-Agents
# Magic UI Enhanced BigQuery Analytics Platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Header
print_color "$PURPLE" "=============================================="
print_color "$PURPLE" "✨ ADK-Agents Docker Deployment"
print_color "$PURPLE" "   Magic UI + BigQuery Analytics Platform"
print_color "$PURPLE" "=============================================="

# Check for .env file
if [ ! -f .env ]; then
    print_color "$YELLOW" "\n⚠️  No .env file found. Creating from example..."
    if [ -f .env.docker.example ]; then
        cp .env.docker.example .env
        print_color "$GREEN" "✅ Created .env file from .env.docker.example"
        print_color "$RED" "⚠️  Please edit .env file with your API keys before continuing!"
        print_color "$YELLOW" "   Required: GCP_PROJECT_ID and at least one LLM API key"
        exit 1
    else
        print_color "$RED" "❌ No .env.docker.example file found!"
        exit 1
    fi
fi

# Parse command
COMMAND=${1:-"up"}

case $COMMAND in
    "build")
        print_color "$BLUE" "\n🔨 Building Docker images..."
        docker-compose build --no-cache
        print_color "$GREEN" "✅ Build complete!"
        ;;
        
    "up")
        print_color "$BLUE" "\n🚀 Starting services..."
        docker-compose up -d
        
        # Wait for services to be healthy
        print_color "$YELLOW" "\n⏳ Waiting for services to be healthy..."
        
        # Wait for backend
        for i in {1..30}; do
            if docker-compose exec backend curl -f http://localhost:8010/health >/dev/null 2>&1; then
                print_color "$GREEN" "✅ Backend is healthy"
                break
            fi
            echo -n "."
            sleep 2
        done
        
        # Wait for frontend
        for i in {1..30}; do
            if docker-compose exec frontend curl -f http://localhost:80 >/dev/null 2>&1; then
                print_color "$GREEN" "✅ Frontend is healthy"
                break
            fi
            echo -n "."
            sleep 2
        done
        
        print_color "$GREEN" "\n✨ Services are running!"
        print_color "$PURPLE" "\n🎨 Access the application:"
        print_color "$BLUE" "   Frontend (Magic UI): http://localhost"
        print_color "$BLUE" "   Backend API: http://localhost:8010"
        print_color "$YELLOW" "\n📋 View logs: docker-compose logs -f"
        ;;
        
    "down")
        print_color "$YELLOW" "\n🛑 Stopping services..."
        docker-compose down
        print_color "$GREEN" "✅ Services stopped"
        ;;
        
    "restart")
        print_color "$YELLOW" "\n🔄 Restarting services..."
        docker-compose restart
        print_color "$GREEN" "✅ Services restarted"
        ;;
        
    "logs")
        print_color "$BLUE" "\n📋 Showing logs (Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
        
    "clean")
        print_color "$RED" "\n🧹 Cleaning up Docker resources..."
        docker-compose down -v --remove-orphans
        docker system prune -f
        print_color "$GREEN" "✅ Cleanup complete"
        ;;
        
    "status")
        print_color "$BLUE" "\n📊 Service Status:"
        docker-compose ps
        ;;
        
    "test")
        print_color "$BLUE" "\n🧪 Running health checks..."
        
        # Test backend
        if curl -f http://localhost:8010/health >/dev/null 2>&1; then
            print_color "$GREEN" "✅ Backend API: Healthy"
        else
            print_color "$RED" "❌ Backend API: Not responding"
        fi
        
        # Test frontend
        if curl -f http://localhost >/dev/null 2>&1; then
            print_color "$GREEN" "✅ Frontend UI: Healthy"
        else
            print_color "$RED" "❌ Frontend UI: Not responding"
        fi
        
        # Show container stats
        print_color "$BLUE" "\n📈 Container Statistics:"
        docker stats --no-stream
        ;;
        
    *)
        print_color "$YELLOW" "\nUsage: ./docker-run.sh [command]"
        print_color "$BLUE" "\nAvailable commands:"
        echo "  build    - Build Docker images"
        echo "  up       - Start services (default)"
        echo "  down     - Stop services"
        echo "  restart  - Restart services"
        echo "  logs     - View logs"
        echo "  clean    - Clean up Docker resources"
        echo "  status   - Show service status"
        echo "  test     - Run health checks"
        ;;
esac

print_color "$PURPLE" "\n=============================================="