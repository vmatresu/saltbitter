# ADR-002: PostgreSQL over MongoDB for Primary Database

## Status
Accepted

## Context
We need to select a primary database for the SaltBitter dating platform. The main candidates were PostgreSQL (relational) and MongoDB (document-oriented).

### Data Characteristics
- User profiles with structured fields (name, email, bio)
- Relationships between entities (users, matches, messages, subscriptions)
- Financial transactions requiring ACID guarantees
- Geospatial queries for location-based matching
- JSON fields for flexible profile data (interests, preferences)
- Complex queries for compatibility algorithm

### PostgreSQL Strengths
- ACID compliance for transactions (critical for payments)
- Strong referential integrity with foreign keys
- Native JSON/JSONB support for flexible schema
- PostGIS for geospatial queries
- Mature ecosystem and tooling
- Battle-tested at scale (Instagram, Uber, Netflix)
- Cost-effective (AWS RDS Multi-AZ)

### MongoDB Strengths
- Flexible schema for evolving data models
- Horizontal scaling with sharding
- Native document structure
- Strong developer experience with aggregation pipeline

## Decision
We will use **PostgreSQL 15** as our primary database.

## Consequences

### Positive
- **ACID Transactions**: Critical for payment processing and subscription management
- **Data Integrity**: Foreign keys prevent orphaned records
- **Mature Tooling**: Extensive monitoring, backup, and migration tools
- **Geospatial Support**: PostGIS enables efficient location-based matching
- **JSON Flexibility**: JSONB columns provide schema flexibility where needed
- **Cost-Effective**: RDS Multi-AZ provides HA without expensive sharding
- **Query Optimization**: Mature query planner for complex compatibility algorithm
- **GDPR Compliance**: Easier to implement data deletion with foreign key cascades

### Negative
- **Schema Migrations**: Changes require Alembic migrations (vs MongoDB's flexibility)
- **Vertical Scaling Limits**: May need read replicas for analytics workloads
- **JSON Query Performance**: JSONB queries slower than native MongoDB

### Mitigation
- Use JSONB for fields needing flexibility (interests, preferences)
- Implement read replicas for reporting queries
- Cache frequently accessed data in Redis
- Use connection pooling (PgBouncer) for efficient connection management
- Design schema carefully upfront to minimize future migrations

## Technical Details

### Database Configuration
```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
```

### Geospatial Queries
```sql
-- Example: Find users within 50km
SELECT * FROM profiles
WHERE ST_DWithin(
  location,
  ST_MakePoint(-122.4194, 37.7749)::geography,
  50000
);
```

### JSONB Usage
```sql
-- Flexible preferences storage
CREATE TABLE profiles (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  preferences JSONB,
  interests JSONB
);

-- Query JSON fields
SELECT * FROM profiles
WHERE preferences->>'age_min' >= '25';
```

## Related Decisions
- ADR-001: Use FastAPI over Django
- ADR-007: Redis for caching and queues

## References
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostGIS Documentation](https://postgis.net/)
- [AWS RDS PostgreSQL Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)

## Date
2025-11-17

## Authors
- Architect Agent
- Database Team
