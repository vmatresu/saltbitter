# ADR-010: DataDog for Observability and Monitoring

## Status
Accepted

## Context
We need comprehensive observability for the SaltBitter platform to:
- Monitor application performance (APM)
- Track infrastructure metrics (CPU, memory, disk)
- Centralize logs from multiple services
- Set up alerts for critical issues
- Debug production issues with distributed tracing
- Monitor user experience (Real User Monitoring)
- Track business metrics (MAU, conversion rates)

### Requirements
- **Metrics**: Time-series data (response times, error rates, throughput)
- **Logs**: Centralized logging with search and filtering
- **Traces**: Distributed tracing across services and external APIs
- **Alerts**: On-call notifications (PagerDuty integration)
- **Dashboards**: Real-time visibility for ops and engineering
- **RUM**: Frontend performance and user experience monitoring
- **Cost**: Reasonable pricing for startup scale

### Options Considered

**Option A: DataDog**
- Pros: All-in-one platform, excellent UX, strong APM, great integrations
- Cons: Most expensive option (~$2K/month for our scale)

**Option B: Prometheus + Grafana + Loki (self-hosted)**
- Pros: Open source, no per-host fees, full control
- Cons: High ops burden, requires 0.5 FTE to maintain, alerting less polished

**Option C: AWS CloudWatch + X-Ray**
- Pros: Native AWS integration, included in AWS bill, no new vendor
- Cons: Limited features, clunky UI, weak APM compared to DataDog

**Option D: New Relic**
- Pros: Similar to DataDog, good APM
- Cons: Pricing based on data ingestion (unpredictable), less intuitive UI

**Option E: Elastic (ELK) Stack**
- Pros: Powerful log search, open source option available
- Cons: Primarily logging, APM less mature, high memory requirements

## Decision
We will use **DataDog** as our primary observability platform.

## Rationale

### Why DataDog
1. **All-in-One**: Metrics, logs, traces, RUM, synthetics in one platform
2. **Developer Experience**: Intuitive UI, fast time-to-value
3. **APM**: Best-in-class application performance monitoring
4. **Integrations**: 500+ integrations (AWS, PostgreSQL, Redis, Stripe, etc.)
5. **Alerts**: Sophisticated alerting with PagerDuty, Slack, email
6. **Distributed Tracing**: Automatic instrumentation across services
7. **Log Correlation**: Link logs to traces to metrics automatically
8. **Business Metrics**: Custom metrics for conversion funnels, revenue

### Cost Analysis
- **DataDog**: ~$2,000/month for 10 hosts + logs + APM + RUM
- **Self-Hosted**: ~$1,000/month (EC2 + storage) + $5,000/month engineer time = $6,000/month
- **CloudWatch**: ~$800/month but limited functionality, hidden costs in lost productivity

**Decision**: Pay for DataDog's value, avoid undifferentiated heavy lifting

## Implementation Details

### Infrastructure Monitoring

```yaml
# docker-compose.yml - Add DataDog agent
services:
  datadog-agent:
    image: gcr.io/datadoghq/agent:7
    environment:
      - DD_API_KEY=${DATADOG_API_KEY}
      - DD_SITE=datadoghq.com
      - DD_LOGS_ENABLED=true
      - DD_LOGS_CONFIG_CONTAINER_COLLECT_ALL=true
      - DD_APM_ENABLED=true
      - DD_APM_NON_LOCAL_TRAFFIC=true
      - DD_PROCESS_AGENT_ENABLED=true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /proc/:/host/proc/:ro
      - /sys/fs/cgroup/:/host/sys/fs/cgroup:ro
```

```terraform
# Terraform: ECS with DataDog agent
resource "aws_ecs_task_definition" "app" {
  family = "saltbitter-app"

  container_definitions = jsonencode([
    {
      name  = "app"
      image = "saltbitter/backend:latest"
      # ...
      dockerLabels = {
        "com.datadoghq.tags.service" = "saltbitter-api"
        "com.datadoghq.tags.env"     = "production"
        "com.datadoghq.tags.version" = "1.0.0"
      }
    },
    {
      name  = "datadog-agent"
      image = "public.ecr.aws/datadog/agent:latest"
      environment = [
        { name = "DD_API_KEY", value = var.datadog_api_key },
        { name = "DD_SITE", value = "datadoghq.com" },
        { name = "ECS_FARGATE", value = "true" }
      ]
    }
  ])
}
```

### Application Performance Monitoring (APM)

```python
# Backend: Auto-instrument FastAPI with DataDog APM
from ddtrace import patch_all, tracer
from ddtrace.contrib.fastapi import TraceMiddleware

# Patch all supported libraries (requests, psycopg2, redis, etc.)
patch_all()

# Add tracing middleware
app.add_middleware(
    TraceMiddleware,
    service="saltbitter-api",
    tracer=tracer
)

# Custom spans for business logic
from ddtrace import tracer

@router.get("/api/matches")
async def get_matches(user_id: UUID):
    with tracer.trace("matching.calculate_compatibility", service="matching"):
        compatibility_scores = await calculate_compatibility(user_id)

    with tracer.trace("matching.rank_matches", service="matching"):
        ranked_matches = rank_by_score(compatibility_scores)

    return ranked_matches

# Add custom metrics
from datadog import statsd

@router.post("/api/subscriptions")
async def create_subscription(tier: str):
    statsd.increment("subscriptions.created", tags=[f"tier:{tier}"])
    statsd.histogram("subscriptions.revenue", TIER_PRICES[tier], tags=[f"tier:{tier}"])

    # ... create subscription logic
```

### Structured Logging

```python
import logging
import json
from ddtrace import tracer

# JSON structured logging for DataDog
class JSONFormatter(logging.Formatter):
    def format(self, record):
        # Add trace IDs for correlation
        span = tracer.current_span()
        if span:
            record.dd_trace_id = span.trace_id
            record.dd_span_id = span.span_id

        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "dd.trace_id": getattr(record, "dd_trace_id", None),
            "dd.span_id": getattr(record, "dd_span_id", None),
            "environment": "production",
            "service": "saltbitter-api",
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# Configure logger
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("saltbitter")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage
logger.info("User logged in", extra={
    "user_id": str(user.id),
    "email": user.email,
    "subscription_tier": user.subscription_tier
})

logger.error("Payment failed", extra={
    "user_id": str(user.id),
    "payment_amount": 19.99,
    "stripe_error": error.message
})
```

### Real User Monitoring (RUM)

```typescript
// Frontend: React/React Native RUM
import { datadogRum } from '@datadog/browser-rum';

datadogRum.init({
  applicationId: 'your-app-id',
  clientToken: 'your-client-token',
  site: 'datadoghq.com',
  service: 'saltbitter-web',
  env: 'production',
  version: '1.0.0',
  sessionSampleRate: 100,
  sessionReplaySampleRate: 20,  // Record 20% of sessions
  trackUserInteractions: true,
  trackResources: true,
  trackLongTasks: true,
  defaultPrivacyLevel: 'mask-user-input'  // GDPR compliance
});

// Track custom user actions
datadogRum.addAction('subscription_upgraded', {
  tier: 'elite',
  user_id: userId,
  revenue: 49.99
});

// Set user context
datadogRum.setUser({
  id: userId,
  email: userEmail,  // Only if user consents (GDPR)
  subscription_tier: 'premium'
});
```

### Dashboards

**Key Dashboards to Create:**

1. **API Performance Dashboard**
   - Request rate (requests/second)
   - Error rate (errors/second, % of total)
   - Latency (p50, p95, p99)
   - Apdex score (user satisfaction)

2. **Infrastructure Dashboard**
   - ECS task count and status
   - CPU utilization (per service)
   - Memory usage (per service)
   - Network throughput

3. **Database Dashboard**
   - PostgreSQL connections
   - Query latency (p95, p99)
   - Slow queries (>100ms)
   - Replication lag (if replicas)

4. **Business Metrics Dashboard**
   - Active users (DAU, MAU)
   - Subscription conversions (by tier)
   - Match generation rate
   - Message sent rate
   - Revenue (MRR, daily)

5. **Error Dashboard**
   - Error rate by endpoint
   - Top error messages
   - Failed payment rate
   - 4xx vs 5xx errors

### Alerting

```python
# Alert configurations (via DataDog UI or Terraform)
ALERTS = {
    "high_error_rate": {
        "query": "avg(last_5m):sum:trace.fastapi.request.errors{env:production}.as_count() / sum:trace.fastapi.request.hits{env:production}.as_count() > 0.01",
        "message": "Error rate is above 1% @pagerduty-oncall @slack-alerts",
        "escalation": "page",
        "tags": ["severity:critical", "team:backend"]
    },
    "slow_api_response": {
        "query": "avg(last_10m):p95:trace.fastapi.request.duration{env:production} > 0.5",
        "message": "API p95 latency above 500ms @slack-alerts",
        "escalation": "slack",
        "tags": ["severity:warning", "team:backend"]
    },
    "database_cpu_high": {
        "query": "avg(last_10m):avg:aws.rds.cpuutilization{dbinstanceidentifier:saltbitter-prod} > 80",
        "message": "Database CPU above 80% @slack-alerts",
        "escalation": "slack",
        "tags": ["severity:warning", "team:infra"]
    },
    "payment_failure_spike": {
        "query": "sum(last_15m):sum:subscriptions.payment_failed{env:production}.as_count() > 10",
        "message": "More than 10 payment failures in 15 minutes @pagerduty-oncall @slack-finance",
        "escalation": "page",
        "tags": ["severity:critical", "team:finance"]
    },
    "disk_space_low": {
        "query": "avg(last_5m):avg:system.disk.used{env:production} / avg:system.disk.total{env:production} > 0.85",
        "message": "Disk usage above 85% @slack-alerts",
        "escalation": "slack",
        "tags": ["severity:warning", "team:infra"]
    }
}
```

### Integrations

```python
# Key integrations to enable
INTEGRATIONS = [
    "AWS (ECS, RDS, ElastiCache, S3)",
    "PostgreSQL",
    "Redis",
    "Stripe (custom via API)",
    "PagerDuty (on-call alerts)",
    "Slack (team notifications)",
    "GitHub (link deploys to releases)"
]
```

## Cost Management

```python
# Control DataDog costs
COST_CONTROLS = {
    "log_indexing": "Index only ERROR and CRITICAL logs (exclude INFO/DEBUG)",
    "log_retention": "15 days for INFO, 30 days for ERROR, 90 days for CRITICAL",
    "apm_sampling": "100% sampling for production, 10% for staging",
    "rum_sampling": "100% user sessions, 20% session replay",
    "metrics_rollup": "Aggregate to 1-minute resolution after 15 days",
    "custom_metrics": "Limit to 100 custom metrics (avoid high cardinality tags)"
}

# Estimated costs at scale
COST_ESTIMATES = {
    "10_hosts": "$2,000/month",
    "50_hosts": "$6,000/month",
    "100_hosts": "$10,000/month"
}
```

## Consequences

### Positive
- **Single Pane of Glass**: All observability data in one place
- **Fast Debugging**: Correlate logs, traces, and metrics in seconds
- **Proactive Alerts**: Catch issues before users report them
- **User Experience**: RUM shows real user pain points
- **Business Insights**: Custom metrics track product and revenue metrics
- **Team Productivity**: Less time debugging, more time shipping features
- **Oncall Efficiency**: Rich context reduces MTTR by 50%+

### Negative
- **Cost**: $2K/month initially, scales with growth
- **Vendor Lock-In**: Difficult to migrate metrics, dashboards, alerts
- **Learning Curve**: Team needs training on DataDog features
- **Data Privacy**: Logs may contain PII (must configure scrubbing)

### Mitigation
- Budget for DataDog as critical infrastructure
- Use DataDog's API to export key metrics as backup
- Provide team training and documentation
- Configure log scrubbing to remove PII automatically
- Review and optimize costs monthly (disable unused features)

## Related Decisions
- ADR-001: FastAPI (auto-instrumented by DataDog)
- ADR-002: PostgreSQL (DataDog integration available)
- ADR-007: Redis (DataDog integration available)

## References
- [DataDog Documentation](https://docs.datadoghq.com/)
- [DataDog APM Python](https://docs.datadoghq.com/tracing/setup_overview/setup/python/)
- [DataDog Pricing](https://www.datadoghq.com/pricing/)
- [DataDog Best Practices](https://docs.datadoghq.com/logs/guide/best-practices/)

## Date
2025-11-17

## Authors
- Architect Agent
- Infrastructure Team
- Engineering Manager
