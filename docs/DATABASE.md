# Database Schema Documentation

**PostgreSQL 15 Database Schema for SaltBitter**

## Entity Relationship Diagram

See [diagrams/database-er.mmd](./diagrams/database-er.mmd) for the complete ER diagram.

## Overview

The SaltBitter platform uses PostgreSQL 15 with the following extensions:
- **uuid-ossp**: UUID generation
- **postgis**: Geospatial queries for location-based matching
- **pg_trgm**: Full-text search for profiles

## Database Tables

### users
Primary user authentication and account information.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_subscription_tier ON users(subscription_tier);
```

**Columns**:
- `id`: Unique user identifier (UUID)
- `email`: User's email address (unique)
- `password_hash`: bcrypt hashed password (12 rounds)
- `subscription_tier`: Enum: 'free', 'premium', 'elite'
- `email_verified`: Whether email is verified
- `created_at`: Account creation timestamp
- `updated_at`: Last profile update timestamp
- `last_login_at`: Last login timestamp

---

### profiles
User profile information and preferences.

```sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(50),
    bio TEXT,
    photos JSONB DEFAULT '[]',
    interests JSONB DEFAULT '[]',
    location GEOGRAPHY(POINT, 4326),
    city VARCHAR(100),
    country VARCHAR(100),
    preferences JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_profiles_user_id ON profiles(user_id);
CREATE INDEX idx_profiles_location ON profiles USING GIST(location);
```

**Columns**:
- `user_id`: Foreign key to `users.id`
- `name`: Display name
- `date_of_birth`: Date of birth (used to calculate age)
- `bio`: Profile biography (max 500 chars)
- `photos`: JSON array of S3 photo URLs (max 6)
- `interests`: JSON array of interest tags
- `location`: PostGIS geography point (latitude, longitude)
- `preferences`: JSON object with matching preferences (age_min, age_max, distance_km)

---

### attachment_assessments
Attachment style assessment results (ECR-R).

```sql
CREATE TABLE attachment_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    anxiety_score DECIMAL(3,2) NOT NULL,
    avoidance_score DECIMAL(3,2) NOT NULL,
    style VARCHAR(50) NOT NULL,
    responses JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_attachment_user_id ON attachment_assessments(user_id);
CREATE INDEX idx_attachment_style ON attachment_assessments(style);
```

**Columns**:
- `anxiety_score`: Anxiety dimension score (1.0 - 7.0)
- `avoidance_score`: Avoidance dimension score (1.0 - 7.0)
- `style`: Enum: 'secure', 'anxious', 'avoidant', 'fearful'
- `responses`: JSON array of assessment responses

---

### matches
Daily match records with compatibility scores.

```sql
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_a_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_b_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    compatibility_score DECIMAL(4,3) NOT NULL,
    compatibility_breakdown JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    matched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_a_id, user_b_id)
);

CREATE INDEX idx_matches_user_a ON matches(user_a_id, status);
CREATE INDEX idx_matches_user_b ON matches(user_b_id, status);
CREATE INDEX idx_matches_score ON matches(compatibility_score DESC);
```

**Columns**:
- `user_a_id`, `user_b_id`: The two matched users
- `compatibility_score`: Overall compatibility (0.0 - 1.0)
- `compatibility_breakdown`: JSON with score breakdown (attachment, interests, values, demographics)
- `status`: Enum: 'pending', 'liked', 'passed', 'mutual'

---

### messages
Chat messages between matched users (future phase).

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    to_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    moderation_flagged BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_messages_from ON messages(from_user_id, sent_at DESC);
CREATE INDEX idx_messages_to ON messages(to_user_id, sent_at DESC);
CREATE INDEX idx_messages_conversation ON messages(from_user_id, to_user_id, sent_at DESC);
```

---

### subscriptions
Stripe subscription records.

```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier VARCHAR(50) NOT NULL,
    stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
```

**Columns**:
- `tier`: Enum: 'premium', 'elite'
- `stripe_subscription_id`: Stripe subscription ID
- `status`: Enum: 'incomplete', 'active', 'past_due', 'canceled', 'unpaid'

---

### refresh_tokens
JWT refresh tokens for authentication.

```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) UNIQUE NOT NULL,
    device_info TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
```

---

### consent_logs
GDPR consent tracking.

```sql
CREATE TABLE consent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(100) NOT NULL,
    granted BOOLEAN NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_consent_user_id ON consent_logs(user_id, created_at DESC);
```

**Consent Types**:
- `terms_of_service`
- `privacy_policy`
- `ai_features`
- `ai_coaching`
- `marketing_emails`

---

### compliance_logs
Audit trail for GDPR and compliance actions.

```sql
CREATE TABLE compliance_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL,
    metadata JSONB,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_compliance_user_id ON compliance_logs(user_id, created_at DESC);
CREATE INDEX idx_compliance_action ON compliance_logs(action_type, created_at DESC);
```

**Action Types**:
- `data_export_requested`
- `data_export_completed`
- `data_deletion_requested`
- `data_deletion_completed`
- `breach_detected`
- `breach_notified`

---

## Migrations

Database migrations are managed using **Alembic**.

### Migration Files Location
`backend/database/alembic/versions/`

### Common Migration Commands

```bash
# Create a new migration
alembic revision -m "description"

# Auto-generate migration from model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View current migration version
alembic current

# View migration history
alembic history
```

---

## Indexes and Performance

### Critical Indexes
1. **users.email**: Unique index for login queries
2. **profiles.location**: GiST index for geospatial queries
3. **matches.user_a_id, matches.status**: Composite index for fetching user's matches
4. **messages.from_user_id, messages.to_user_id, messages.sent_at**: Composite index for conversation queries

### Query Performance Tips
- Use `EXPLAIN ANALYZE` to profile slow queries
- Monitor slow query log (queries >100ms)
- Consider materialized views for complex aggregations
- Use connection pooling (PgBouncer) to manage connections

---

## Backup and Recovery

### Automated Backups
- **RDS Automated Snapshots**: Daily at 3:00 AM UTC, retained 7 days
- **Manual Snapshots**: Before major schema changes
- **Point-in-Time Recovery**: Enabled (5-minute granularity)

### Restore Procedure
```bash
# Restore from snapshot (AWS CLI)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier saltbitter-restored \
  --db-snapshot-identifier saltbitter-snapshot-2025-11-18

# Restore to point in time
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier saltbitter-prod \
  --target-db-instance-identifier saltbitter-restored \
  --restore-time 2025-11-18T08:30:00Z
```

---

## Data Retention Policies

| Data Type | Retention Period | Rationale |
|-----------|------------------|-----------|
| User accounts (active) | Indefinite | Until user deletes account |
| Deleted accounts | 30 days | GDPR grace period for recovery |
| Messages | Indefinite | Part of user data |
| Logs (application) | 90 days | Compliance and debugging |
| Logs (compliance) | 7 years | Legal requirement |
| Refresh tokens | 7 days (auto-expire) | Security |
| Old matches | Indefinite | Historical data |

---

## Related Documentation
- [Architecture Documentation](./ARCHITECTURE.md)
- [ADR-002: PostgreSQL over MongoDB](./adrs/002-postgresql-over-mongodb.md)
- [Entity Relationship Diagram](./diagrams/database-er.mmd)

---

**Last Updated**: 2025-11-18
**Schema Version**: 1.0.0
**PostgreSQL Version**: 15
