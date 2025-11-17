#!/bin/bash

# Database migration helper script for SaltBitter
# Usage: ./migrate.sh [command]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to check if PostgreSQL is ready
wait_for_postgres() {
    print_info "Waiting for PostgreSQL to be ready..."

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if pg_isready -h localhost -p 5432 -U postgres > /dev/null 2>&1; then
            print_success "PostgreSQL is ready"
            return 0
        fi

        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done

    print_error "PostgreSQL is not ready after ${max_attempts} seconds"
    return 1
}

# Main command logic
case "${1:-help}" in
    upgrade|up)
        print_info "Running database migrations..."
        wait_for_postgres
        alembic upgrade head
        print_success "Migrations completed successfully"
        ;;

    downgrade|down)
        print_info "Rolling back database migration..."
        alembic downgrade -1
        print_success "Rollback completed"
        ;;

    reset)
        print_info "Resetting database to base..."
        alembic downgrade base
        print_success "Database reset to base"
        ;;

    seed)
        print_info "Seeding database with test data..."
        wait_for_postgres
        python seed_data.py
        print_success "Database seeded successfully"
        ;;

    init)
        print_info "Initializing database (migrate + seed)..."
        wait_for_postgres
        alembic upgrade head
        python seed_data.py
        print_success "Database initialized successfully"
        ;;

    revision|new)
        if [ -z "$2" ]; then
            print_error "Please provide a migration message"
            echo "Usage: $0 revision \"Add new column\""
            exit 1
        fi
        print_info "Creating new migration: $2"
        alembic revision --autogenerate -m "$2"
        print_success "Migration created"
        ;;

    current)
        print_info "Current database revision:"
        alembic current
        ;;

    history)
        print_info "Migration history:"
        alembic history
        ;;

    help|--help|-h)
        echo "SaltBitter Database Migration Helper"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  upgrade, up      - Run all pending migrations"
        echo "  downgrade, down  - Rollback one migration"
        echo "  reset            - Reset database to base (remove all tables)"
        echo "  seed             - Populate database with test data"
        echo "  init             - Initialize database (migrate + seed)"
        echo "  revision \"msg\"   - Create new migration"
        echo "  current          - Show current revision"
        echo "  history          - Show migration history"
        echo "  help             - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 init                    # Initialize new database"
        echo "  $0 upgrade                 # Apply pending migrations"
        echo "  $0 revision \"Add column\"  # Create new migration"
        echo "  $0 seed                    # Add test data"
        ;;

    *)
        print_error "Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac
