# ADR-007: Redis for Caching and Message Queuing

## Status
Accepted

## Context
We need solutions for:
1. **Caching**: Reduce database load for frequently accessed data
2. **Session Storage**: Store rate limiting counters and temporary data
3. **Message Queue**: Asynchronous job processing (match generation, emails, notifications)
4. **Real-time Messaging**: Pub/sub for WebSocket message routing across multiple server instances

### Requirements
- Sub-millisecond latency for cache reads
- Persistence for queue jobs (don't lose jobs on restart)
- Pub/sub for real-time features
- Cost-effective at scale
- Simple operations (not complex queries)

### Options Considered

**Option A: Memcached (caching) + RabbitMQ (queuing)**
- Pros: Specialized tools for each use case
- Cons: Two systems to maintain, higher operational cost

**Option B: Redis for everything**
- Pros: Single system, versatile, proven at scale
- Cons: Jack of all trades, master of none?

**Option C: DynamoDB (caching) + SQS (queuing)**
- Pros: Fully managed AWS services
- Cons: Higher cost, DynamoDB not optimized for caching patterns

## Decision
We will use **Redis 7** for caching, session storage, message queuing (via Celery), and pub/sub.

## Implementation Details

### 1. Caching Strategy

**Cache Keys Pattern**
```python
# Hierarchical key structure
CACHE_KEYS = {
    "user": "user:{user_id}",
    "profile": "profile:{user_id}",
    "attachment": "attachment:{user_id}",
    "matches": "matches:{user_id}:{date}",
    "compatibility": "compat:{user_a_id}:{user_b_id}",
}

# Example usage
async def get_profile(user_id: UUID) -> Profile:
    cache_key = f"profile:{user_id}"

    # Try cache first
    cached = await redis.get(cache_key)
    if cached:
        return Profile.parse_raw(cached)

    # Cache miss, fetch from database
    profile = await db.get_profile(user_id)

    # Store in cache with TTL
    await redis.setex(
        cache_key,
        timedelta(hours=1),
        profile.json()
    )

    return profile
```

**TTL Strategy**
```python
CACHE_TTL = {
    "user_profile": 3600,          # 1 hour
    "attachment_results": 86400,    # 24 hours
    "daily_matches": 86400,         # 24 hours (until next generation)
    "compatibility_score": 604800,  # 7 days (stable calculation)
    "rate_limit": 60,               # 1 minute
}
```

**Cache Invalidation**
```python
async def update_profile(user_id: UUID, updates: ProfileUpdate):
    # Update database
    profile = await db.update_profile(user_id, updates)

    # Invalidate related caches
    await redis.delete(f"profile:{user_id}")
    await redis.delete(f"attachment:{user_id}")

    # Invalidate compatibility scores with all matches
    match_ids = await db.get_user_match_ids(user_id)
    for match_id in match_ids:
        await redis.delete(f"compat:{user_id}:{match_id}")
        await redis.delete(f"compat:{match_id}:{user_id}")

    return profile
```

### 2. Message Queue (Celery)

**Task Examples**
```python
# backend/workers/celery_app.py
from celery import Celery

celery_app = Celery(
    "saltbitter",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

# Task: Generate daily matches
@celery_app.task(name="generate_daily_matches")
def generate_daily_matches():
    """Run daily at 6 AM user local time."""
    users_needing_matches = get_users_needing_matches()
    for user in users_needing_matches:
        matches = calculate_matches(user)
        store_matches(user.id, matches)
        send_notification(user.id, f"You have {len(matches)} new matches!")

# Task: Send welcome email
@celery_app.task(name="send_welcome_email")
def send_welcome_email(user_id: UUID):
    user = get_user(user_id)
    send_email(
        to=user.email,
        subject="Welcome to SaltBitter!",
        template="welcome",
        context={"name": user.name}
    )

# Task: Process profile photo
@celery_app.task(name="process_profile_photo")
def process_profile_photo(user_id: UUID, photo_url: str):
    # Download photo
    image = download_image(photo_url)

    # Resize and optimize
    thumbnails = generate_thumbnails(image)

    # Upload to S3
    s3_urls = upload_to_s3(user_id, thumbnails)

    # Update profile
    update_profile_photos(user_id, s3_urls)
```

**Celery Beat Scheduling**
```python
# backend/workers/celerybeat-schedule.py
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "generate-daily-matches": {
        "task": "generate_daily_matches",
        "schedule": crontab(hour=6, minute=0),  # 6 AM daily
    },
    "cleanup-expired-tokens": {
        "task": "cleanup_expired_refresh_tokens",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
    "send-weekly-coaching-summaries": {
        "task": "send_weekly_coaching_summaries",
        "schedule": crontab(day_of_week=1, hour=9, minute=0),  # Monday 9 AM
    },
}
```

### 3. Pub/Sub for Real-Time Messaging

**Message Broadcasting**
```python
# When user sends message
async def send_message(from_user_id: UUID, to_user_id: UUID, content: str):
    # Save to database
    message = await db.create_message(from_user_id, to_user_id, content)

    # Publish to Redis channel for real-time delivery
    await redis.publish(
        f"chat:{to_user_id}",
        message.json()
    )

    # If recipient offline, send push notification
    if not await is_user_online(to_user_id):
        await push_notification(to_user_id, f"New message from {from_user_id}")

    return message

# WebSocket connection subscribes to user's channel
async def websocket_handler(websocket: WebSocket, user_id: UUID):
    await websocket.accept()

    # Subscribe to user's channel
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"chat:{user_id}")

    # Listen for messages
    async for message in pubsub.listen():
        if message["type"] == "message":
            await websocket.send_json(message["data"])
```

### 4. Rate Limiting

```python
from datetime import datetime, timedelta

async def check_rate_limit(user_id: UUID, action: str, max_requests: int = 100, window_seconds: int = 60):
    """Token bucket rate limiting."""

    key = f"ratelimit:{action}:{user_id}"
    now = datetime.utcnow().timestamp()

    # Use Redis sorted set for sliding window
    async with redis.pipeline() as pipe:
        # Remove old entries outside window
        await pipe.zremrangebyscore(key, 0, now - window_seconds)

        # Count requests in window
        await pipe.zcard(key)

        # Add current request
        await pipe.zadd(key, {str(now): now})

        # Set expiration
        await pipe.expire(key, window_seconds)

        results = await pipe.execute()

    request_count = results[1]

    if request_count >= max_requests:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds}s"
        )
```

## Infrastructure Configuration

**AWS ElastiCache Redis**
```terraform
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "saltbitter-redis"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = "cache.r7g.large"  # 13.07 GiB memory
  num_cache_nodes      = 1                   # Single node for development
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]

  # Persistence for message queue
  snapshot_retention_limit = 5
  snapshot_window          = "03:00-05:00"

  # Automatic failover (production)
  automatic_failover_enabled = true
  multi_az_enabled          = true  # Production only
}
```

**Production: Redis Cluster**
```terraform
# For production with higher load
resource "aws_elasticache_replication_group" "redis_cluster" {
  replication_group_id       = "saltbitter-redis-cluster"
  replication_group_description = "Redis cluster for caching and queues"
  engine                     = "redis"
  engine_version             = "7.0"
  node_type                  = "cache.r7g.large"
  num_cache_clusters         = 3  # 1 primary + 2 replicas
  automatic_failover_enabled = true
  multi_az_enabled          = true

  # Persistence
  snapshot_retention_limit = 7
  snapshot_window          = "03:00-05:00"

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}
```

## Monitoring

```python
# Key metrics to track
REDIS_METRICS = [
    "cache_hit_rate",         # Target: >85%
    "evicted_keys",           # Target: <1% of total
    "connected_clients",      # Monitor for leaks
    "used_memory",            # Alert at 80% capacity
    "latency_ms",             # Target: <5ms p95
]

# CloudWatch alarms
- Memory > 80%: Scale up node type
- Evictions > 100/min: Increase cache size or reduce TTLs
- Cache hit rate < 80%: Review caching strategy
```

## Consequences

### Positive
- **Single System**: One tool for multiple use cases reduces ops complexity
- **Performance**: Sub-millisecond cache reads, 50,000+ ops/second
- **Cost-Effective**: $100-200/month for r7g.large vs. $400+ for multiple systems
- **Proven**: Used by Twitter, GitHub, Stack Overflow at massive scale
- **Persistence**: Snapshot + AOF prevents job loss on restarts
- **Pub/Sub**: Enables multi-instance WebSocket routing
- **Developer Experience**: Simple API, well-documented, excellent Python libraries

### Negative
- **Single Point of Failure**: Cache + queue + pub/sub all impacted if Redis down
- **Memory Constraints**: In-memory store limits dataset size
- **Not Durable**: Not suitable for critical data (use as cache, not primary store)
- **Queue Limitations**: Less sophisticated than dedicated queues (RabbitMQ)

### Mitigation
- Enable automatic failover with Multi-AZ (production)
- Monitor memory usage, alert at 80%
- Use persistence (RDB + AOF) for message queue
- Circuit breakers: Degrade gracefully if Redis unavailable
- Backup critical queue jobs to database

## Related Decisions
- ADR-001: FastAPI (async Redis clients)
- ADR-002: PostgreSQL (primary data store, Redis is cache)
- ADR-005: Modular monolith (Celery enables async processing)

## References
- [Redis Documentation](https://redis.io/documentation)
- [Celery with Redis](https://docs.celeryproject.org/en/stable/getting-started/backends-and-brokers/redis.html)
- [AWS ElastiCache Best Practices](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/BestPractices.html)

## Date
2025-11-17

## Authors
- Architect Agent
- Infrastructure Team
