#!/bin/bash

# Test script for Docker setup
set -e

echo "🐳 Testing Docker Setup for Content Management System"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Check prerequisites
echo "Checking prerequisites..."

# Check if Docker is installed
if command -v docker &> /dev/null; then
    print_status 0 "Docker is installed"
else
    print_status 1 "Docker is not installed"
fi

# Check if Docker Compose is installed
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    print_status 0 "Docker Compose is available"
else
    print_status 1 "Docker Compose is not available"
fi

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    print_warning "OPENAI_API_KEY environment variable is not set"
    echo "Please set it with: export OPENAI_API_KEY='your-key-here'"
else
    print_status 0 "OPENAI_API_KEY is set"
fi

echo ""
echo "Building and starting services..."

# Build and start services
docker compose up -d --build

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Test service health
echo ""
echo "Testing service health..."

# Test Nginx
if curl -s http://localhost/health > /dev/null; then
    print_status 0 "Nginx is responding"
else
    print_status 1 "Nginx is not responding"
fi

# Test Frontend
if curl -s http://localhost:3000/health > /dev/null; then
    print_status 0 "Frontend is responding"
else
    print_status 1 "Frontend is not responding"
fi

# Test Backend through proxy
if curl -s http://localhost/api/content > /dev/null; then
    print_status 0 "Backend API is responding through proxy"
else
    print_status 1 "Backend API is not responding through proxy"
fi

# Test Redis
if docker compose exec -T redis redis-cli ping | grep -q PONG; then
    print_status 0 "Redis is responding"
else
    print_status 1 "Redis is not responding"
fi

# Check container status
echo ""
echo "Container status:"
docker compose ps

# Show service logs (last 10 lines)
echo ""
echo "Recent logs:"
echo "============"
docker compose logs --tail=10

echo ""
echo "🎉 Docker setup test completed!"
echo ""
echo "Access your application at:"
echo "  Main App: http://localhost"
echo "  Health:   http://localhost/health"
echo "  API:      http://localhost/api/content"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop:      docker compose down" 