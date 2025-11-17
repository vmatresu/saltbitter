# SaltBitter Development Guide

This guide will help you set up and work with the SaltBitter dating platform in your local development environment.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** (v20.10+) - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (v2.0+) - Included with Docker Desktop
- **Git** - For version control
- **Make** (optional but recommended) - For convenient commands

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/vmatresu/saltbitter.git
cd saltbitter
```

### 2. Start Development Environment

```bash
make dev-up
```

Or without Make:

```bash
./scripts/dev-up.sh
```

This command will:
- Build all Docker images
- Start all services (PostgreSQL, Redis, Backend, Frontend, etc.)
- Wait for services to become healthy
- Display access URLs

### 3. Access the Application

Once started, you can access:

- **Frontend (React)**: http://localhost:3000
- **Backend API (FastAPI)**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Documentation (ReDoc)**: http://localhost:8000/redoc
- **Mailhog (Email Testing)**: http://localhost:8025
- **MinIO Console (S3)**: http://localhost:9001 (admin/minioadmin)
- **Adminer (Database UI)**: http://localhost:8080

## Development Services

### Core Services

1. **PostgreSQL 15** (`postgres`)
   - Database for persistent storage
   - Port: 5432
   - Credentials: postgres/postgres
   - Database: saltbitter_dev

2. **Redis 7** (`redis`)
   - Cache and session storage
   - Port: 6379

3. **FastAPI Backend** (`backend`)
   - Python 3.11 with FastAPI
   - Hot reload enabled
   - Port: 8000

4. **React Frontend** (`frontend`)
   - React 18 + TypeScript + Vite
   - Hot reload enabled
   - Port: 3000

### Supporting Services

5. **MinIO** (`minio`)
   - S3-compatible storage for local development
   - API Port: 9000
   - Console Port: 9001
   - Credentials: minioadmin/minioadmin

6. **Mailhog** (`mailhog`)
   - Email testing tool
   - SMTP: localhost:1025
   - Web UI: http://localhost:8025

7. **Adminer** (`adminer`)
   - Database management UI
   - Port: 8080

## Common Commands

### Environment Management

```bash
# Start all services
make dev-up

# Stop all services
make dev-down

# Restart all services
make dev-restart

# View logs from all services
make dev-logs

# View logs from specific service
./scripts/dev-logs.sh backend
./scripts/dev-logs.sh frontend

# Reset entire environment (deletes all data!)
make dev-reset
```

### Container Access

```bash
# Open shell in backend container
make dev-shell-backend

# Open shell in frontend container
make dev-shell-frontend

# Open PostgreSQL shell
make dev-db
```

### Development Tasks

```bash
# Run tests
make test

# Run linters
make lint

# Format code
make format

# Clean temporary files
make clean
```

## Project Structure

```
saltbitter/
├── .agents/                    # Multi-agent framework
├── backend/                    # FastAPI backend
│   ├── main.py                # Application entry point
│   ├── api/                   # API endpoints
│   ├── models/                # SQLAlchemy models
│   ├── services/              # Business logic
│   └── tests/                 # Backend tests
├── frontend/                   # React frontend
│   ├── src/                   # Source code
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API clients
│   │   └── utils/             # Utility functions
│   └── tests/                 # Frontend tests
├── docs/                       # Documentation
├── scripts/                    # Development scripts
│   ├── dev-up.sh              # Start services
│   ├── dev-down.sh            # Stop services
│   ├── dev-reset.sh           # Reset environment
│   └── dev-logs.sh            # View logs
├── docker-compose.yml          # Docker services definition
├── .env.example               # Example environment variables
├── .env.local                 # Local environment variables (gitignored)
└── Makefile                   # Convenience commands
```

## Environment Variables

Environment variables are managed through:

1. **`.env.example`** - Template with all available variables and documentation
2. **`.env.local`** - Your local configuration (gitignored)

To customize your environment:

```bash
cp .env.example .env.local
# Edit .env.local with your preferred values
```

## Backend Development

### Running Tests

```bash
# Run all tests with coverage
docker-compose exec backend pytest tests/ -v --cov --cov-report=term-missing

# Run specific test file
docker-compose exec backend pytest tests/test_auth.py -v

# Run with specific marker
docker-compose exec backend pytest -m "unit" -v
```

### Code Quality

```bash
# Run ruff linter
docker-compose exec backend ruff check .

# Auto-fix ruff issues
docker-compose exec backend ruff check --fix .

# Run mypy type checker
docker-compose exec backend mypy --strict .

# Run bandit security scanner
docker-compose exec backend bandit -r . -ll

# Format code with black
docker-compose exec backend black .
```

### Database Migrations

```bash
# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback one migration
docker-compose exec backend alembic downgrade -1

# View migration history
docker-compose exec backend alembic history
```

## Frontend Development

### Running Tests

```bash
# Run all tests
docker-compose exec frontend npm test

# Run tests with coverage
docker-compose exec frontend npm test -- --coverage

# Run tests in watch mode
docker-compose exec frontend npm test -- --watch
```

### Code Quality

```bash
# Run ESLint
docker-compose exec frontend npm run lint

# Auto-fix ESLint issues
docker-compose exec frontend npm run lint:fix

# Run TypeScript type checking
docker-compose exec frontend npm run type-check

# Format code with Prettier
docker-compose exec frontend npm run format
```

### Building for Production

```bash
# Build production bundle
docker-compose exec frontend npm run build

# Preview production build
docker-compose exec frontend npm run preview
```

## Debugging

### Backend Debugging

1. Add `debugpy` to your code:
   ```python
   import debugpy
   debugpy.listen(("0.0.0.0", 5678))
   debugpy.wait_for_client()
   ```

2. Uncomment debug port in `docker-compose.override.yml`

3. Connect your IDE to `localhost:5678`

### Frontend Debugging

Use browser DevTools:
- Chrome: F12 or Cmd+Option+I (Mac)
- Sources tab for breakpoints
- Console for logs
- Network tab for API calls

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker info

# Check for port conflicts
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL

# View service logs
docker-compose logs <service-name>

# Rebuild images
docker-compose build --no-cache
```

### Database Issues

```bash
# Reset database
make dev-reset

# Check database connection
docker-compose exec postgres pg_isready -U postgres

# Access database directly
make dev-db
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Clean up Docker system
docker system prune -a

# Remove unused volumes
docker volume prune
```

## Testing Features

### Email Testing (Mailhog)

1. Open http://localhost:8025
2. Send email from backend code
3. View received emails in Mailhog UI

### File Upload Testing (MinIO)

1. Open http://localhost:9001
2. Login: minioadmin / minioadmin
3. Create bucket: `saltbitter-dev`
4. Upload/download files

### API Testing

Use the built-in Swagger UI:
1. Open http://localhost:8000/docs
2. Expand endpoints
3. Click "Try it out"
4. Execute requests

Or use curl:
```bash
curl http://localhost:8000/health
```

## Code Style Guidelines

### Backend (Python)

- Use **Black** formatter (line length: 88)
- Follow **Google-style docstrings**
- Use **type hints** for all functions
- Minimum **85% test coverage**
- Pass **mypy strict mode**
- Pass **ruff** linting
- Pass **bandit** security scans

### Frontend (TypeScript)

- Use **Prettier** formatter
- Follow **ESLint** rules
- Use **TypeScript** strictly (no `any`)
- Minimum **70% test coverage**
- Use **functional components** with hooks
- Follow **React best practices**

## Git Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit: `git commit -m "Add feature"`
3. Push to remote: `git push origin feature/my-feature`
4. Create pull request
5. Wait for CI/CD checks to pass
6. Request code review
7. Merge after approval

## Multi-Agent Framework

This project uses a Git-native multi-agent coordination framework. See:
- `.agents/README.md` - Framework documentation
- `.agents/projects/dating-platform/` - Project specification
- `.agents/prompts/` - Agent role definitions

## Getting Help

- **Documentation**: Check `docs/` directory
- **Architecture**: See `.agents/projects/dating-platform/architecture.toon`
- **Issues**: Create GitHub issue
- **Questions**: Ask in team chat

## Next Steps

1. Read the [Architecture Documentation](./.agents/projects/dating-platform/architecture.toon)
2. Review the [Project Specification](./.agents/projects/dating-platform.toon)
3. Check available tasks in `.agents/projects/dating-platform/tasks/`
4. Start implementing features!

---

**Happy coding! 🚀**
