.PHONY: help dev-up dev-down dev-restart dev-logs dev-reset dev-shell-backend dev-shell-frontend dev-db test lint format clean

# Default target
help:
	@echo "SaltBitter Development Commands"
	@echo ""
	@echo "Environment Management:"
	@echo "  make dev-up              Start all development services"
	@echo "  make dev-down            Stop all development services"
	@echo "  make dev-restart         Restart all development services"
	@echo "  make dev-logs            View logs from all services"
	@echo "  make dev-reset           Reset database and volumes (WARNING: deletes data)"
	@echo ""
	@echo "Container Access:"
	@echo "  make dev-shell-backend   Open shell in backend container"
	@echo "  make dev-shell-frontend  Open shell in frontend container"
	@echo "  make dev-db              Open PostgreSQL shell"
	@echo ""
	@echo "Development Tasks:"
	@echo "  make test                Run all tests"
	@echo "  make lint                Run linters (ruff, mypy, eslint)"
	@echo "  make format              Format code (black, prettier)"
	@echo "  make clean               Clean up temporary files and caches"
	@echo ""

# Environment Management
dev-up:
	@./scripts/dev-up.sh

dev-down:
	@./scripts/dev-down.sh

dev-restart: dev-down dev-up
	@echo "✅ Services restarted"

dev-logs:
	@./scripts/dev-logs.sh

dev-reset:
	@./scripts/dev-reset.sh

# Container Access
dev-shell-backend:
	@echo "🐚 Opening shell in backend container..."
	@docker-compose exec backend /bin/bash

dev-shell-frontend:
	@echo "🐚 Opening shell in frontend container..."
	@docker-compose exec frontend /bin/sh

dev-db:
	@echo "🗄️  Opening PostgreSQL shell..."
	@docker-compose exec postgres psql -U postgres -d saltbitter_dev

# Development Tasks
test:
	@echo "🧪 Running backend tests..."
	@docker-compose exec backend pytest tests/ -v --cov --cov-report=term-missing
	@echo ""
	@echo "🧪 Running frontend tests..."
	@docker-compose exec frontend npm test

lint:
	@echo "🔍 Running backend linters..."
	@docker-compose exec backend ruff check .
	@docker-compose exec backend mypy --strict .
	@docker-compose exec backend bandit -r . -ll
	@echo ""
	@echo "🔍 Running frontend linters..."
	@docker-compose exec frontend npm run lint

format:
	@echo "🎨 Formatting backend code..."
	@docker-compose exec backend black .
	@docker-compose exec backend ruff check --fix .
	@echo ""
	@echo "🎨 Formatting frontend code..."
	@docker-compose exec frontend npm run format

clean:
	@echo "🧹 Cleaning up temporary files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "node_modules" -prune -o -type d -name ".cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete"
