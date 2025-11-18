# Engineering Onboarding Guide

**Welcome to SaltBitter! This guide will get you productive in your first week.**

## Week 1: Getting Started

### Day 1: Setup & Orientation

**Morning: Account Setup**
- [ ] Get access to GitHub organization (github.com/vmatresu/saltbitter)
- [ ] Get added to Slack workspace (#engineering, #deploys, #incidents)
- [ ] Get access to AWS Console (staging and production)
- [ ] Get access to DataDog
- [ ] Get access to PagerDuty (if on-call rotation)
- [ ] Set up 1Password team vault

**Afternoon: Local Development**
```bash
# Clone repository
git clone git@github.com:vmatresu/saltbitter.git
cd saltbitter

# Install dependencies
# Backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend/web
npm install

# Start local environment
cd ../..
docker-compose up -d

# Verify services
curl http://localhost:8000/health  # Backend
curl http://localhost:3000          # Frontend
```

- [ ] Run local development environment
- [ ] Run test suite: `pytest backend/tests/`
- [ ] Explore codebase in your IDE

**Reading**:
- [ ] [README.md](../README.md)
- [ ] [Architecture Documentation](./ARCHITECTURE.md)
- [ ] [API Documentation](./API.md)

### Day 2: Understand the System

**Morning: Architecture Deep Dive**
- [ ] Read [Architecture Documentation](./ARCHITECTURE.md)
- [ ] Read [Database Schema](./DATABASE.md)
- [ ] Review [ADRs](./adrs/) (Architecture Decision Records)

**Afternoon: Code Walkthrough**
Schedule 1-hour pairing session with team lead to walk through:
- FastAPI application structure
- Service modules (auth, profile, matching)
- Database models and migrations
- Testing patterns

**Shadow a deploy**:
- Watch the CI/CD pipeline in action
- See how staging deployment works
- Understand rollback procedures

### Day 3: First Contribution

**Morning: Pick a Starter Task**
Look for issues tagged `good-first-issue`:
```bash
gh issue list --label "good-first-issue"
```

Typical starter tasks:
- Fix a typo in documentation
- Add unit test for uncovered code
- Improve error message clarity
- Optimize a slow query

**Afternoon: Development Workflow**
1. Create feature branch: `git checkout -b feature/your-task`
2. Make changes
3. Run tests: `pytest backend/tests/ -v`
4. Run linting: `ruff check . && mypy .`
5. Commit with descriptive message
6. Push and create PR
7. Address code review feedback
8. Merge!

**Reading**:
- [ ] [CONTRIBUTING.md](../CONTRIBUTING.md)
- [ ] [Code Review Checklist](./SECURITY.md#code-review-security-checklist)

### Day 4: Deeper Dive

**Morning: Explore a Service Module**
Pick one service (auth, profile, matching, etc.) and understand:
- How it handles requests (routes.py)
- Business logic (service.py)
- Database interactions (models/)
- Tests (tests/)

**Afternoon: Debug a Real Issue**
Pair with engineer to:
- Investigate a DataDog alert
- Trace a slow API request
- Review error logs
- Propose a fix

### Day 5: End-to-End Feature

**Morning: Implement Small Feature**
Example: Add a new profile field
1. Add database migration (Alembic)
2. Update SQLAlchemy model
3. Add Pydantic schema
4. Update API endpoint
5. Write tests
6. Update API documentation

**Afternoon: Knowledge Share**
- Present what you learned this week to team (15 min)
- Ask questions about anything unclear
- Schedule recurring 1-on-1 with manager

---

## Week 2-4: Ramp Up

### Goals
- [ ] Deploy a feature to production
- [ ] Participate in on-call rotation (shadow first week)
- [ ] Review 5+ pull requests from teammates
- [ ] Optimize a slow query or API endpoint
- [ ] Write or update a runbook

### On-Call Preparation
Before joining rotation:
- [ ] Read [Incident Response Playbook](./INCIDENT_RESPONSE.md)
- [ ] Shadow on-call engineer for 1 week
- [ ] Have PagerDuty app installed and tested
- [ ] Know how to access DataDog, AWS Console, logs
- [ ] Know escalation contacts (CTO, DevOps lead)

---

## Development Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `fix/*`: Bug fixes
- `hotfix/*`: Critical production fixes

### Code Quality Standards
- **Test Coverage**: ≥85% for backend, ≥70% for frontend
- **Type Checking**: mypy --strict must pass
- **Linting**: ruff and Black for Python, ESLint for TypeScript
- **Security**: Bandit scans must pass (no high/critical issues)

### Pull Request Process
1. Create PR with descriptive title and description
2. Link related issue: `Closes #123`
3. Ensure CI passes (tests, linting, security scans)
4. Request review from 1-2 teammates
5. Address feedback promptly
6. Squash commits if needed
7. Merge using "Squash and merge"

---

## Tools & Access

### Development
- **IDE**: VS Code or PyCharm (team uses both)
- **Database Client**: DBeaver or pgAdmin
- **API Client**: Postman or Insomnia (collections in `docs/postman/`)

### Productivity
- **Slack**: #engineering, #deploys, #incidents, #random
- **GitHub**: Issues, PRs, Actions
- **Linear**: Project management (optional)
- **Notion**: Team wiki and docs

### Monitoring & Debugging
- **DataDog**: APM, logs, traces, dashboards
- **AWS Console**: ECS, RDS, CloudWatch
- **Stripe Dashboard**: Payment testing (test mode)

---

## Key Concepts

### Attachment Theory Matching
Read [ADR-003](./adrs/003-attachment-theory-algorithm.md) to understand our unique matching algorithm based on attachment theory.

### GDPR & Privacy
We take privacy seriously. Read:
- [Compliance Documentation](./COMPLIANCE.md)
- [Security Best Practices](./SECURITY.md)
- Never log PII or sensitive data

### Testing Philosophy
- **Unit Tests**: Test individual functions in isolation
- **Integration Tests**: Test service interactions
- **E2E Tests**: Test full user flows
- **Mocking**: Mock external APIs (Stripe, OpenAI) in tests

---

## Common Commands

### Backend
```bash
# Run tests
pytest backend/tests/ -v

# Run with coverage
pytest --cov=backend --cov-report=html

# Type checking
mypy backend/

# Linting
ruff check backend/
black backend/ --check

# Security scan
bandit -r backend/

# Database migration
alembic upgrade head
alembic revision -m "add new field"
```

### Frontend
```bash
# Run tests
npm test

# Lint
npm run lint

# Type check
tsc --noEmit

# Build
npm run build
```

### Docker
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Restart service
docker-compose restart api

# Stop all
docker-compose down
```

---

## Learning Resources

### Internal
- [Architecture Documentation](./ARCHITECTURE.md)
- [API Documentation](./API.md) (also at http://localhost:8000/docs)
- [ADRs](./adrs/) - Why we made key technical decisions
- Team wiki (Notion)

### External
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Pydantic V2](https://docs.pydantic.dev/latest/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)

---

## Team Culture

- **Async-first**: Don't expect immediate responses
- **Documentation**: If it's not documented, it doesn't exist
- **Blameless post-mortems**: Focus on systems, not people
- **Continuous improvement**: Always ask "how can we do better?"
- **Work-life balance**: No messages outside work hours unless on-call

---

## Questions?

**Technical Questions**: Ask in #engineering Slack
**Process Questions**: Ask your manager
**Urgent Issues**: Ping on-call engineer in #incidents

**Welcome to the team! 🚀**

---

**Last Updated**: 2025-11-18
**Maintained By**: Engineering Manager
