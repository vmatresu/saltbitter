#!/bin/bash
# Stop all development services

set -e

echo "🛑 Stopping SaltBitter development environment..."

# Stop services
docker-compose down

echo ""
echo "✅ All services stopped"
echo ""
echo "💡 Tips:"
echo "  - Data is preserved in Docker volumes"
echo "  - Run 'make dev-up' to start again"
echo "  - Run 'make dev-reset' to wipe all data and start fresh"
echo ""
