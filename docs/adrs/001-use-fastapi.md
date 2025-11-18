# ADR-001: Use FastAPI over Django for Backend API

## Status
Accepted

## Context
We need to choose a Python web framework for the SaltBitter dating platform backend API. The primary candidates were Django REST Framework (DRF) and FastAPI.

### Requirements
- High-performance API with low latency (<200ms p95)
- WebSocket support for real-time messaging
- Automatic API documentation (OpenAPI/Swagger)
- Strong type checking and validation
- Async/await support for I/O-bound operations
- Active community and ecosystem

### Django REST Framework Strengths
- Mature ecosystem with extensive libraries
- Built-in admin interface
- Battle-tested ORM (Django ORM)
- Comprehensive authentication system
- Large talent pool

### FastAPI Strengths
- Native async/await support (3-4x faster for I/O operations)
- Automatic OpenAPI/Swagger documentation generation
- Built-in data validation using Pydantic
- Modern Python type hints for better IDE support
- Native WebSocket support
- Smaller memory footprint
- Better performance benchmarks (TechEmpower)

## Decision
We will use **FastAPI 0.104+** as our backend framework.

## Consequences

### Positive
- **Performance**: Async/await enables handling 10,000+ concurrent users efficiently
- **Type Safety**: Pydantic models provide runtime validation and compile-time type checking
- **Documentation**: OpenAPI spec auto-generated, reducing documentation drift
- **WebSockets**: Native support simplifies real-time messaging implementation
- **Developer Experience**: Type hints improve IDE autocomplete and catch errors early
- **Modern Stack**: Aligns with current Python best practices (Python 3.11+)

### Negative
- **Smaller Ecosystem**: Fewer third-party packages compared to Django
- **Less Built-in Features**: No admin interface out of the box (can add FastAPI-Admin if needed)
- **Team Learning Curve**: Team needs to learn async programming patterns
- **Custom Solutions**: May need to build utilities that Django provides (e.g., advanced auth)

### Mitigation
- Use SQLAlchemy for ORM (more flexible than Django ORM)
- Leverage FastAPI's dependency injection for reusable components
- Create shared utility libraries for common patterns
- Document async patterns in team onboarding guide

## Related Decisions
- ADR-002: PostgreSQL over MongoDB
- ADR-006: JWT authentication strategy

## References
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TechEmpower Benchmarks](https://www.techempower.com/benchmarks/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## Date
2025-11-17

## Authors
- Architect Agent
- Software Engineering Team
