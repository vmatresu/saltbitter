#!/bin/bash
# Reset the entire development environment (wipes all data)

set -e

echo "⚠️  WARNING: This will delete all database data, Redis cache, and uploaded files!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Reset cancelled"
    exit 0
fi

echo ""
echo "🗑️  Stopping services and removing volumes..."

# Stop and remove containers, networks, and volumes
docker-compose down -v

# Remove any dangling images
docker image prune -f

echo ""
echo "🧹 Cleanup complete!"
echo ""
echo "🔄 Starting fresh environment..."

# Start services again
./scripts/dev-up.sh
