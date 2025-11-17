# Project: SaltBitter

## Project Overview
SaltBitter is a modern web application built with a separation of frontend and backend concerns. This document provides universal context for all AI agents working on this codebase.

## Architecture

### Stack
- **Backend**: Python, FastAPI (planned)
- **Frontend**: Modern JavaScript/TypeScript framework (planned)
- **Database**: PostgreSQL (planned)
- **Cache**: Redis (optional)
- **Containerization**: Docker

### Structure
```
saltbitter/
├── backend/          # Backend API service
├── frontend/         # Frontend application
├── tests/            # Test suites
├── data/             # Data files and migrations
├── docs/             # Documentation
└── .agents/          # Agent orchestration system
```

### Key Patterns
- **Repository Pattern**: Data access abstraction
- **Dependency Injection**: For testability and modularity
- **RESTful API Design**: Clear, predictable endpoints
- **Component-Based Frontend**: Reusable UI components

## Development Workflow

### Task Management
1. Tasks are defined in `.agents/tasks/queue.json`
2. Agents claim tasks atomically via Git commits
3. Feature branches follow pattern: `feature/TASK-{id}-{slug}`
4. Fix branches follow pattern: `fix/TASK-{id}-{slug}`
5. Commit messages use format: `[TASK-{id}] {description}`

### Development Process
1. **Task Assignment**: Coordinator assigns tasks based on priority and dependencies
2. **Branch Creation**: Agent creates feature/fix branch from main
3. **Implementation**: Code, test, iterate
4. **Testing**: Unit tests + integration tests required
5. **Code Review**: Reviewer agent validates quality
6. **Merge**: Automated merge after all checks pass

### Quality Gates
All code must pass:
- ✅ Unit tests (pytest)
- ✅ Integration tests (if applicable)
- ✅ Code coverage ≥80%
- ✅ Linting (ruff)
- ✅ Type checking (mypy)
- ✅ Security scan (bandit)
- ✅ Reviewer agent approval

## Code Standards

### Python Style Guide
- **Formatter**: Black (line length: 88)
- **Linter**: Ruff (replaces flake8, isort, pyupgrade)
- **Type Checking**: MyPy in strict mode
- **Docstrings**: Google style docstrings
- **Import Order**: Standard library → Third-party → Local

### Example Code Structure
```python
"""Module docstring explaining purpose."""

from typing import Optional, List
import asyncio

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


class UserService:
    """Service for user operations.

    Args:
        db: Database session

    Attributes:
        db: Database session instance
    """

    def __init__(self, db: Session):
        self.db = db

    async def get_user(self, user_id: int) -> Optional[User]:
        """Retrieve a user by ID.

        Args:
            user_id: The user's unique identifier

        Returns:
            User object if found, None otherwise

        Raises:
            DatabaseError: If database connection fails
        """
        # Implementation here
        pass
```

### Testing Standards
- **Framework**: pytest with async support (pytest-asyncio)
- **Coverage**: Minimum 80% code coverage
- **Fixtures**: Use pytest fixtures for setup/teardown
- **Mocking**: Use unittest.mock or pytest-mock
- **Test Structure**: Arrange-Act-Assert pattern

### Example Test Structure
```python
"""Tests for user service."""

import pytest
from unittest.mock import Mock, patch

from app.services.user_service import UserService


@pytest.fixture
def mock_db():
    """Provide a mock database session."""
    return Mock()


@pytest.mark.asyncio
async def test_get_user_success(mock_db):
    """Test successful user retrieval."""
    # Arrange
    service = UserService(mock_db)
    expected_user = User(id=1, name="Test User")
    mock_db.query.return_value.filter.return_value.first.return_value = expected_user

    # Act
    result = await service.get_user(1)

    # Assert
    assert result == expected_user
    mock_db.query.assert_called_once()
```

## Off-The-Shelf Tools (Prefer Over Custom)

### Development Tools
- **Testing**: pytest, pytest-cov, pytest-asyncio, pytest-xdist (parallel)
- **Linting**: ruff (fast, comprehensive)
- **Formatting**: black
- **Type Checking**: mypy
- **Security**: bandit (code), safety (dependencies)
- **API Testing**: httpx + pytest
- **Database**: Alembic (migrations), SQLAlchemy (ORM)

### CI/CD
- **Platform**: GitHub Actions (native integration)
- **Container**: Docker + Docker Compose
- **Deployment**: TBD (AWS, GCP, or Azure)

### Optional Services
- **Monitoring**: Sentry (error tracking)
- **Logging**: Structured logging with Python logging module
- **Documentation**: Sphinx or MkDocs

## Agent Capabilities Registry

Agents can have one or more of these capabilities:

- **python**: Python development (FastAPI, SQLAlchemy, etc.)
- **fastapi**: FastAPI framework expertise
- **postgresql**: PostgreSQL database design and optimization
- **redis**: Redis caching and session management
- **docker**: Container configuration and orchestration
- **testing**: Test writing and TDD practices
- **frontend**: JavaScript/TypeScript frontend development
- **database**: Database schema design and migrations
- **devops**: CI/CD, deployment, infrastructure
- **security**: Security best practices and vulnerability assessment
- **code-review**: Code quality validation
- **quality-assurance**: QA and testing validation
- **architecture**: System design and technical planning
- **planning**: Task decomposition and estimation
- **design**: UI/UX design

## Integration Points

### Database
- **Development**: PostgreSQL on localhost:5432
- **CI**: GitHub Actions service container
- **Production**: TBD (managed PostgreSQL service)

### Cache (Optional)
- **Development**: Redis on localhost:6379
- **CI**: GitHub Actions service container
- **Production**: TBD (managed Redis service)

### External APIs
- Document any third-party APIs here as they are integrated

### Authentication
- JWT-based authentication (planned)
- OAuth2 integration (future consideration)

## Environment Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/saltbitter
DATABASE_POOL_SIZE=10

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Application
APP_ENV=development  # development, staging, production
SECRET_KEY=your-secret-key-here
DEBUG=true

# API Keys (as needed)
# EXTERNAL_API_KEY=...
```

### Configuration Files
- `.env` - Local environment variables (NOT committed)
- `.env.example` - Template for environment setup (committed)
- `config.yml` - Application configuration
- `.agents/config.yml` - Agent system configuration

## Completion Criteria

A feature/task is considered "done" when:

- [ ] All acceptance criteria from task description are met
- [ ] Code implementation is complete and functional
- [ ] Unit tests written with ≥80% coverage
- [ ] Integration tests added (if applicable)
- [ ] All tests passing locally and in CI
- [ ] Code coverage meets or exceeds 80% threshold
- [ ] Linting passes (ruff)
- [ ] Type checking passes (mypy)
- [ ] Security scan passes (bandit)
- [ ] No unresolved code review comments
- [ ] Documentation updated (docstrings, README, etc.)
- [ ] Reviewer agent has approved the changes
- [ ] PR merged to main branch
- [ ] Agent status file updated to "completed"
- [ ] Task moved to "completed" in queue

## Common Pitfalls to Avoid

### Security
- ❌ Never commit secrets, API keys, or passwords
- ❌ Never use `eval()` or `exec()` with user input
- ❌ Always validate and sanitize user input
- ❌ Don't trust client-side validation alone
- ✅ Use parameterized queries (SQLAlchemy ORM)
- ✅ Implement proper authentication and authorization
- ✅ Use HTTPS in production
- ✅ Keep dependencies updated

### Performance
- ❌ Avoid N+1 query problems
- ❌ Don't load entire datasets into memory
- ✅ Use database indexes appropriately
- ✅ Implement caching for expensive operations
- ✅ Use async/await for I/O-bound operations
- ✅ Paginate large result sets

### Code Quality
- ❌ Don't write untested code
- ❌ Avoid deeply nested logic (>3 levels)
- ❌ Don't use generic variable names (x, temp, data)
- ✅ Write self-documenting code with clear names
- ✅ Keep functions small and focused (single responsibility)
- ✅ Use type hints consistently
- ✅ Write meaningful commit messages

## Getting Help

### Documentation Resources
- Project README: `/README.md`
- API Documentation: `/docs/api.md` (when available)
- Architecture Decisions: `/docs/architecture/` (when available)

### Agent Coordination
- Task Queue: `.agents/tasks/queue.json`
- Agent Registry: `.agents/registry.json`
- Agent Status: `.agents/status/{agent-id}.md`
- Logs: `.agents/logs/`

### External Resources
- FastAPI Docs: https://fastapi.tiangolo.com
- SQLAlchemy Docs: https://docs.sqlalchemy.org
- Pytest Docs: https://docs.pytest.org
- Python Best Practices: https://docs.python-guide.org

## Project-Specific Notes

### Current Status
- ✅ Repository structure initialized
- ✅ Agent orchestration framework implemented
- ⏳ Backend API implementation (pending)
- ⏳ Frontend application (pending)
- ⏳ Database schema design (pending)
- ⏳ Authentication system (pending)

### Immediate Priorities
1. Define core database models
2. Implement basic API endpoints
3. Set up authentication system
4. Create frontend structure
5. Implement user management

### Long-term Goals
- Scalable architecture supporting growth
- High code quality and test coverage
- Automated deployment pipeline
- Comprehensive documentation
- Active agent-driven development

---

*Last Updated: 2025-11-17*
*This document should be updated as the project evolves*
