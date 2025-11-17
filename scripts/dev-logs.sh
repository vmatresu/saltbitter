#!/bin/bash
# View logs from development services

set -e

# If a service name is provided, show only that service's logs
if [ -n "$1" ]; then
    echo "📋 Showing logs for: $1"
    docker-compose logs -f --tail=100 "$1"
else
    echo "📋 Showing logs for all services (last 50 lines each)"
    echo "💡 Tip: Run './scripts/dev-logs.sh <service>' to view specific service logs"
    echo ""
    docker-compose logs -f --tail=50
fi
