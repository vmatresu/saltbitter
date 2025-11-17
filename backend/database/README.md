# SaltBitter Database Schema

Complete PostgreSQL database schema with PostGIS support for the SaltBitter dating platform.

## Overview

This database schema implements all 12 tables required for the dating platform, including:
- User authentication and profiles
- Attachment theory assessments
- Matching and messaging
- AI interaction tracking (EU AI Act compliance)
- Subscriptions and payments
- Events and registrations
- GDPR compliance logging

## Technology Stack

- **Database**: PostgreSQL 15 with PostGIS extension
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic 1.12+
- **Geospatial**: GeoAlchemy2 for location data

## Database Tables

### Core Tables

#### 1. `users`
User authentication and account data.

**Columns:**
- `id` (UUID, PK): Primary key
- `email` (VARCHAR, UNIQUE): User email
- `password_hash` (VARCHAR): Bcrypt hashed password
- `verified` (BOOLEAN): Email verification status
- `subscription_tier` (VARCHAR): free, premium, or elite
- `created_at`, `updated_at`, `last_login_at` (TIMESTAMP)

**Indexes:**
- `ix_users_email` (UNIQUE)
- `ix_users_subscription_tier`

#### 2. `profiles`
User profile information with location data.

**Columns:**
- `user_id` (UUID, PK, FK → users.id): Primary key and foreign key
- `name` (VARCHAR): Display name
- `age` (INTEGER): User age
- `gender` (VARCHAR): Gender identity
- `bio` (TEXT): Profile bio
- `photos` (JSONB): Array of photo URLs
- `location` (GEOGRAPHY): PostGIS point for geospatial queries
- `completeness_score` (FLOAT): 0-100% profile completion
- `looking_for_gender`, `min_age`, `max_age`, `max_distance_km`: Preferences
- `created_at`, `updated_at` (TIMESTAMP)

**Indexes:**
- `ix_profiles_user_id`
- `ix_profiles_location` (GIST spatial index)

#### 3. `attachment_assessments`
Psychology-based attachment style assessments.

**Columns:**
- `id` (UUID, PK): Primary key
- `user_id` (UUID, FK → users.id, UNIQUE): One assessment per user
- `anxiety_score` (FLOAT): Attachment anxiety (0-100)
- `avoidance_score` (FLOAT): Attachment avoidance (0-100)
- `style` (VARCHAR): secure, anxious, avoidant, or fearful-avoidant
- `assessment_version` (VARCHAR): Version tracking
- `total_questions` (INTEGER): Number of questions
- `created_at`, `updated_at` (TIMESTAMP)

**Indexes:**
- `ix_attachment_assessments_user_id`
- `ix_attachment_assessments_style`

#### 4. `matches`
User matching and compatibility tracking.

**Columns:**
- `id` (UUID, PK): Primary key
- `user_a_id`, `user_b_id` (UUID, FK → users.id): Matched users
- `compatibility_score` (FLOAT): Compatibility score (0-100)
- `status` (VARCHAR): pending, liked, passed, matched, unmatched
- `created_at`, `updated_at` (TIMESTAMP)

**Constraints:**
- `different_users`: user_a_id ≠ user_b_id
- `valid_score`: 0 ≤ compatibility_score ≤ 100

**Indexes:**
- `ix_matches_user_a_id`, `ix_matches_user_b_id`
- `ix_matches_status`

#### 5. `messages`
Direct messaging between matched users.

**Columns:**
- `id` (UUID, PK): Primary key
- `from_user_id`, `to_user_id` (UUID, FK → users.id): Sender and recipient
- `content` (TEXT): Message content (encrypted in production)
- `read_at` (TIMESTAMP): When message was read
- `sent_at` (TIMESTAMP): When message was sent

**Indexes:**
- `ix_messages_from_user_id`, `ix_messages_to_user_id`
- `ix_messages_sent_at`

### AI & Compliance Tables

#### 6. `ai_interactions`
AI feature usage tracking for EU AI Act compliance.

**Columns:**
- `id` (UUID, PK): Primary key
- `user_id` (UUID, FK → users.id): User who interacted with AI
- `ai_type` (VARCHAR): practice_companion, relationship_coach, etc.
- `disclosure_shown` (BOOLEAN): Article 52 disclosure shown
- `user_consented` (BOOLEAN): User explicit consent
- `session_id` (VARCHAR): Session grouping
- `created_at` (TIMESTAMP)

**Indexes:**
- `ix_ai_interactions_user_id`
- `ix_ai_interactions_ai_type`

#### 7. `consent_logs`
GDPR consent tracking for special category data.

**Columns:**
- `id` (UUID, PK): Primary key
- `user_id` (UUID, FK → users.id): User giving consent
- `consent_type` (VARCHAR): Type of consent
- `granted` (BOOLEAN): Consent granted or withdrawn
- `consent_text` (TEXT): Exact text shown to user
- `ip_address` (VARCHAR): Audit trail
- `timestamp` (TIMESTAMP)

**Indexes:**
- `ix_consent_logs_user_id`
- `ix_consent_logs_consent_type`

#### 8. `compliance_logs`
Regulatory compliance audit trail.

**Columns:**
- `id` (UUID, PK): Primary key
- `user_id` (UUID, FK → users.id): User affected
- `action_type` (VARCHAR): Type of compliance action
- `metadata` (JSONB): Flexible action details
- `regulatory_framework` (VARCHAR): gdpr, eu_ai_act, ccpa, sb_243
- `timestamp` (TIMESTAMP)

**Indexes:**
- `ix_compliance_logs_user_id`
- `ix_compliance_logs_action_type`
- `ix_compliance_logs_timestamp`

### Monetization Tables

#### 9. `subscriptions`
User subscription management.

**Columns:**
- `id` (UUID, PK): Primary key
- `user_id` (UUID, FK → users.id, UNIQUE): One subscription per user
- `tier` (VARCHAR): free, premium, elite
- `stripe_subscription_id`, `stripe_customer_id` (VARCHAR): Stripe IDs
- `status` (VARCHAR): active, canceled, past_due, trialing
- `current_period_start`, `current_period_end` (TIMESTAMP)
- `created_at`, `updated_at` (TIMESTAMP)

**Indexes:**
- `ix_subscriptions_user_id`
- `ix_subscriptions_status`

#### 10. `payments`
Payment transaction history.

**Columns:**
- `id` (UUID, PK): Primary key
- `user_id` (UUID, FK → users.id): User who made payment
- `amount` (NUMERIC): Payment amount in USD
- `type` (VARCHAR): subscription, profile_boost, super_like, etc.
- `stripe_payment_id`, `stripe_invoice_id` (VARCHAR): Stripe IDs
- `status` (VARCHAR): succeeded, pending, failed, refunded
- `created_at` (TIMESTAMP)

**Indexes:**
- `ix_payments_user_id`
- `ix_payments_created_at`

### Event Tables

#### 11. `events`
Virtual events and community gatherings.

**Columns:**
- `id` (UUID, PK): Primary key
- `title`, `description` (VARCHAR/TEXT): Event details
- `type` (VARCHAR): speed_dating, workshop, ama, etc.
- `start_time`, `end_time` (TIMESTAMP): Event scheduling
- `capacity` (INTEGER): Maximum attendees
- `price` (NUMERIC): Event price (0.00 for free)
- `host_name`, `video_url` (VARCHAR): Event metadata
- `created_at`, `updated_at` (TIMESTAMP)

**Constraints:**
- `valid_event_duration`: end_time > start_time
- `positive_capacity`: capacity > 0
- `non_negative_price`: price ≥ 0

**Indexes:**
- `ix_events_type`
- `ix_events_start_time`

#### 12. `event_registrations`
User event attendance tracking.

**Columns:**
- `id` (UUID, PK): Primary key
- `event_id` (UUID, FK → events.id): Event registered for
- `user_id` (UUID, FK → users.id): User registered
- `status` (VARCHAR): registered, attended, no_show, canceled
- `payment_id` (UUID, FK → payments.id): Payment for paid events
- `created_at`, `updated_at` (TIMESTAMP)

**Indexes:**
- `ix_event_registrations_event_id`
- `ix_event_registrations_user_id`

## PostgreSQL Extensions

### PostGIS
Enables geospatial queries for location-based matching.

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

**Usage:**
- Store user locations as `GEOGRAPHY(POINT, 4326)` (WGS84 coordinate system)
- Query users within distance: `ST_DWithin(location, point, distance)`
- Create spatial indexes: `CREATE INDEX USING GIST (location)`

### pgcrypto
Provides `gen_random_uuid()` for UUID generation.

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

## Running Migrations

### Initial Setup

1. **Start Docker environment:**
   ```bash
   docker-compose up -d postgres
   ```

2. **Run migrations:**
   ```bash
   cd backend/database
   alembic upgrade head
   ```

3. **Seed development data:**
   ```bash
   python seed_data.py
   ```

### Creating New Migrations

```bash
cd backend/database
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Rolling Back

```bash
# Downgrade one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>

# Downgrade all
alembic downgrade base
```

## Development Workflow

### 1. Modify Models
Edit files in `backend/database/models/`

### 2. Generate Migration
```bash
cd backend/database
alembic revision --autogenerate -m "Add new column"
```

### 3. Review Migration
Check generated file in `alembic/versions/`

### 4. Apply Migration
```bash
alembic upgrade head
```

### 5. Test
```bash
python seed_data.py  # Populate test data
```

## Database Configuration

### Environment Variables

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/saltbitter_dev
```

### Connection Pool Settings

SQLAlchemy defaults (can be customized):
- Pool size: 5
- Max overflow: 10
- Pool recycle: 3600 seconds

## Indexes and Performance

All tables include:
- **Primary keys**: UUID with `gen_random_uuid()`
- **Foreign keys**: With `CASCADE` delete where appropriate
- **Indexes**: On commonly queried fields
- **Constraints**: Data validation at database level

### Spatial Queries

Location-based matching uses PostGIS:

```sql
-- Find users within 50km of a point
SELECT * FROM profiles
WHERE ST_DWithin(
    location,
    ST_SetSRID(ST_MakePoint(-122.4194, 37.7749), 4326)::geography,
    50000  -- meters
);
```

## Compliance Features

### GDPR
- `consent_logs`: Track all consent events
- `compliance_logs`: Audit trail for data operations
- Cascade deletes for user data removal

### EU AI Act
- `ai_interactions`: Track all AI feature usage
- `disclosure_shown`: Article 52 compliance
- Transparency logging

### California SB 243
- AI disclosure tracking
- Opt-out mechanism support

## Security Considerations

1. **Passwords**: Always store as bcrypt hashes (cost factor 12)
2. **Messages**: Encrypt content before storage (not implemented in base schema)
3. **PII**: Implement access controls and encryption at rest
4. **Audit Logging**: All compliance-relevant actions logged

## Testing

### Unit Tests
Test individual model methods and validations.

### Integration Tests
Test database operations with test database.

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/saltbitter_test pytest
```

## Schema Diagram

```
users (1) ──→ (1) profiles
  │
  ├──→ (1) attachment_assessments
  ├──→ (*) matches
  ├──→ (*) messages
  ├──→ (*) ai_interactions
  ├──→ (1) subscriptions
  ├──→ (*) payments
  ├──→ (*) event_registrations
  ├──→ (*) consent_logs
  └──→ (*) compliance_logs

events (1) ──→ (*) event_registrations
payments (1) ──→ (0..1) event_registrations
```

## Maintenance

### Backups
```bash
# Backup database
pg_dump -U postgres saltbitter_dev > backup.sql

# Restore database
psql -U postgres saltbitter_dev < backup.sql
```

### Vacuum
```bash
# Analyze tables for query optimization
VACUUM ANALYZE;
```

## Troubleshooting

### Common Issues

1. **PostGIS extension not found**
   - Ensure using `postgis/postgis` Docker image
   - Run: `CREATE EXTENSION postgis;`

2. **UUID generation fails**
   - Install pgcrypto: `CREATE EXTENSION pgcrypto;`

3. **Alembic can't find models**
   - Check `PYTHONPATH` includes backend directory
   - Verify `alembic/env.py` imports Base correctly

4. **Migration conflicts**
   - Pull latest: `git pull`
   - Resolve conflicts in migration files
   - Rerun: `alembic upgrade head`

## References

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [GeoAlchemy2 Documentation](https://geoalchemy-2.readthedocs.io/)

---

**Version**: 1.0.0
**Created**: 2025-11-17
**Author**: agent-software-engineer-claude
**Task**: TASK-004
