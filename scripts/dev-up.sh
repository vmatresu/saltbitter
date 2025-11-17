#!/bin/bash
# Start all development services

set -e

echo "🚀 Starting SaltBitter development environment..."

# Load environment variables
if [ -f .env.local ]; then
    export $(cat .env.local | grep -v '^#' | xargs)
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start services
echo "📦 Building Docker images..."
docker-compose build

echo "🔄 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "🏥 Checking service health..."

services=(postgres redis backend frontend)
for service in "${services[@]}"; do
    if docker-compose ps | grep -q "$service.*Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service failed to start"
        docker-compose logs "$service"
        exit 1
    fi
done

echo ""
echo "✨ Development environment is ready!"
echo ""
echo "📍 Available services:"
echo "  Backend API:    http://localhost:8000"
echo "  Frontend:       http://localhost:3000"
echo "  Mailhog UI:     http://localhost:8025"
echo "  MinIO Console:  http://localhost:9001"
echo "  Adminer (DB):   http://localhost:8080"
echo ""
echo "📚 Useful commands:"
echo "  make dev-logs     - View logs"
echo "  make dev-down     - Stop services"
echo "  make dev-restart  - Restart services"
echo "  make dev-reset    - Reset database"
echo ""
