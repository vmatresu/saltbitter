# ADR-005: Modular Monolith over True Microservices

## Status
Accepted

## Context
We need to decide on the backend architecture approach for the SaltBitter dating platform. The options ranged from a monolithic application to true microservices with separate deployments.

### Business Context
- **Team Size**: 3-5 engineers initially, growing to 10-15 in Year 1
- **Timeline**: MVP in 3 months, full launch in 6 months
- **Scale**: 10,000 concurrent users initially, 100,000+ by Year 2
- **Complexity**: 8 distinct service domains (auth, profiles, matching, messaging, AI, payments, events, compliance)

### Architecture Options

**Option A: Monolith**
- Single codebase, single deployment
- Simplest to develop and deploy
- Risk of tight coupling and scaling limits

**Option B: Microservices**
- Separate services with independent deployments
- Maximum flexibility and scaling granularity
- High operational complexity, distributed transactions

**Option C: Modular Monolith**
- Single deployment with clear module boundaries
- Organized as logical services within one codebase
- Can extract to true microservices later if needed

## Decision
We will implement a **modular monolith** architecture with clear service boundaries, allowing future extraction to microservices.

## Rationale

### Why Not Full Microservices (Yet)
1. **Team Size**: 3-5 engineers don't need 8 separate services
2. **Deployment Complexity**: CI/CD, monitoring, logging multiplied by 8x
3. **Transaction Complexity**: Distributed transactions across payment + subscription + audit trail
4. **Network Overhead**: Inter-service calls add latency
5. **Development Speed**: Shared models and utilities speed up development
6. **Premature Optimization**: Unknown which services need independent scaling

### Why Not Pure Monolith
1. **Team Growth**: Need clear boundaries for parallel development
2. **Testing**: Modular structure enables focused unit/integration tests
3. **Future Migration**: Clean interfaces allow later service extraction
4. **Mental Model**: Aligns with domain boundaries for developers

## Implementation Structure

### Directory Structure
```
backend/
├── main.py                    # FastAPI app, router registration
├── database/
│   ├── models/                # SQLAlchemy models (shared)
│   └── migrations/            # Alembic migrations
├── services/
│   ├── auth/                  # Authentication service module
│   │   ├── routes.py          # FastAPI router
│   │   ├── service.py         # Business logic
│   │   ├── schemas.py         # Pydantic models
│   │   └── tests/
│   ├── profile/               # Profile service module
│   ├── attachment/            # Attachment assessment module
│   ├── matching/              # Matching algorithm module
│   ├── messaging/             # Real-time messaging module
│   ├── ai/                    # AI companions & coaching module
│   ├── payment/               # Stripe payment module
│   ├── event/                 # Virtual events module
│   └── compliance/            # GDPR compliance module
└── shared/                    # Shared utilities
    ├── auth.py                # JWT utilities
    ├── cache.py               # Redis client
    └── s3.py                  # S3 client
```

### Module Boundaries

Each service module has:
- **Routes** (`routes.py`): FastAPI endpoints
- **Service** (`service.py`): Business logic, no HTTP dependencies
- **Schemas** (`schemas.py`): Pydantic request/response models
- **Tests** (`tests/`): Unit and integration tests

### Communication Rules
```python
# ✅ ALLOWED: Direct function calls within same deployment
from services.auth.service import get_current_user
from services.profile.service import get_profile

@router.get("/api/matches")
async def get_matches(user = Depends(get_current_user)):
    profile = await get_profile(user.id)  # Direct call, OK
    matches = await matching_service.get_matches(profile)
    return matches

# ❌ FORBIDDEN: Tight coupling, importing models from other services
# from services.auth.schemas import UserInternalModel  # NO!

# ✅ ALLOWED: Shared database models
from database.models import User, Profile  # OK, shared layer
```

## Migration Path to Microservices

When service needs independent scaling (likely candidates):
1. **Messaging Service**: High WebSocket concurrency
2. **Matching Service**: CPU-intensive algorithm, batch processing
3. **AI Service**: Expensive GPT-4 API calls

### Extraction Process
1. Define clear API contract (OpenAPI spec)
2. Replace function calls with HTTP client
3. Extract module to separate FastAPI application
4. Deploy as separate ECS service
5. Add service-to-service authentication
6. Monitor and optimize independently

### Example: Extracting AI Service
```python
# Before: Direct call
from services.ai.service import chat_with_companion
response = await chat_with_companion(user_id, message)

# After: HTTP call
ai_client = AIServiceClient(base_url="http://ai-service")
response = await ai_client.chat_with_companion(user_id, message)
```

## Consequences

### Positive
- **Faster Development**: Shared code, no network overhead
- **Simpler Deployment**: Single Docker image, one ECS service
- **Easier Debugging**: Single process, stack traces cross modules
- **ACID Transactions**: Database transactions span all services
- **Lower Costs**: One ECS task vs. 8+ separate services
- **Team Velocity**: Clear boundaries without microservice overhead
- **Future-Proof**: Can extract high-load services later

### Negative
- **Shared Scaling**: Can't scale messaging independently of matching
- **Deployment Coupling**: Single service failure affects all endpoints
- **Larger Container**: Docker image contains all services (~500MB)
- **Resource Contention**: CPU-heavy matching shares resources with real-time messaging

### Mitigation
- Use asynchronous workers (Celery) for CPU-heavy tasks
- Implement circuit breakers for external APIs (OpenAI, Stripe)
- Monitor per-endpoint metrics to identify extraction candidates
- Design with clean interfaces from day 1
- Document migration path in runbooks

## Scaling Strategy

### Horizontal Scaling
- ECS auto-scaling based on CPU/memory
- Target 10,000 concurrent users per task
- Scale from 2 tasks (staging) to 10+ (production)

### Vertical Scaling Limits
- Task size: 4 vCPU, 8GB RAM
- When limits hit, extract CPU-heavy services

### Database Scaling
- Read replicas for analytics queries
- Connection pooling (PgBouncer)
- Redis cache for hot data

## Related Decisions
- ADR-001: FastAPI framework (enables modular monolith)
- ADR-007: Redis for caching (reduces database load)
- ADR-008: Deployment strategy (ECS Fargate)

## References
- [Modular Monolith by Simon Brown](https://www.codingthearchitecture.com/)
- [Shopify's Modular Monolith](https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity)
- [Martin Fowler - Monolith First](https://martinfowler.com/bliki/MonolithFirst.html)

## Date
2025-11-17

## Authors
- Architect Agent
- Engineering Team
