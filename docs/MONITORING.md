# Monitoring & Observability

**DataDog Monitoring Strategy for SaltBitter**

## Overview

SaltBitter uses DataDog for comprehensive observability across metrics, logs, traces, and real user monitoring (RUM).

## Key Dashboards

### 1. API Performance Dashboard
**URL**: https://app.datadoghq.com/dashboard/saltbitter-api

**Widgets**:
- Request rate (requests/second)
- Error rate (% and absolute count)
- Latency percentiles (p50, p95, p99)
- Apdex score (user satisfaction metric)
- Top 10 slowest endpoints
- Error breakdown by endpoint and status code

**Key Metrics**:
```
trace.fastapi.request.hits (count)
trace.fastapi.request.errors (count)
trace.fastapi.request.duration (histogram)
trace.fastapi.request.apdex (gauge, target: 0.8+)
```

### 2. Infrastructure Dashboard
**URL**: https://app.datadoghq.com/dashboard/saltbitter-infra

**Widgets**:
- ECS task count and status
- CPU utilization (per service, target: <70%)
- Memory usage (per service, target: <80%)
- Network throughput (in/out)
- Disk I/O (IOPS and throughput)

**Key Metrics**:
```
aws.ecs.cpuutilization (gauge)
aws.ecs.memory_utilization (gauge)
aws.rds.cpuutilization (gauge)
aws.elasticache.cpuutilization (gauge)
```

### 3. Database Dashboard
**URL**: https://app.datadoghq.com/dashboard/saltbitter-database

**Widgets**:
- PostgreSQL connections (current/max)
- Query latency (p95, p99)
- Slow queries (>100ms)
- Replication lag (if replicas exist)
- Disk usage (%, alert at 85%)
- Transaction rate (commits/rollbacks)

**Key Metrics**:
```
postgresql.connections (gauge)
postgresql.database.size (gauge)
postgresql.bgwriter.checkpoints_timed (count)
postgresql.replication.delay (gauge)
```

### 4. Business Metrics Dashboard
**URL**: https://app.datadoghq.com/dashboard/saltbitter-business

**Custom Metrics**:
```
saltbitter.users.active_daily (gauge)
saltbitter.users.active_monthly (gauge)
saltbitter.subscriptions.created (count, by tier)
saltbitter.subscriptions.revenue (gauge, MRR)
saltbitter.matches.generated (count)
saltbitter.messages.sent (count)
saltbitter.payments.succeeded (count)
saltbitter.payments.failed (count)
```

## Alert Configuration

### Critical Alerts (PagerDuty)

**High Error Rate**
```yaml
name: "API Error Rate Critical"
query: "avg(last_5m):sum:trace.fastapi.request.errors{env:production}.as_count() / sum:trace.fastapi.request.hits{env:production}.as_count() > 0.05"
message: "@pagerduty-oncall Error rate above 5% for 5 minutes"
severity: critical
threshold: 5%
```

**Database Down**
```yaml
name: "Database Unavailable"
query: "avg(last_2m):avg:aws.rds.database_connections{dbinstanceidentifier:saltbitter-prod} < 1"
message: "@pagerduty-oncall Database has no connections"
severity: critical
```

**Payment Processing Failures**
```yaml
name: "Payment Failure Spike"
query: "sum(last_15m):sum:saltbitter.payments.failed{env:production}.as_count() > 10"
message: "@pagerduty-oncall @slack-finance More than 10 payment failures in 15 minutes"
severity: critical
```

### Warning Alerts (Slack)

**Slow API Response**
```yaml
name: "API Latency High"
query: "avg(last_10m):p95:trace.fastapi.request.duration{env:production} > 0.5"
message: "@slack-eng-alerts API p95 latency above 500ms"
severity: warning
threshold: 500ms
```

**Database CPU High**
```yaml
name: "Database CPU Utilization High"
query: "avg(last_10m):avg:aws.rds.cpuutilization{dbinstanceidentifier:saltbitter-prod} > 80"
message: "@slack-eng-alerts Database CPU above 80%"
severity: warning
threshold: 80%
```

**Disk Space Low**
```yaml
name: "Disk Usage High"
query: "avg(last_5m):avg:system.disk.in_use{env:production} > 0.85"
message: "@slack-eng-alerts Disk usage above 85%"
severity: warning
threshold: 85%
```

## Logging Strategy

### Log Levels
- **DEBUG**: Development only (not indexed in production)
- **INFO**: Informational events (indexed, 15-day retention)
- **WARNING**: Potential issues (indexed, 30-day retention)
- **ERROR**: Errors that don't crash the app (indexed, 90-day retention)
- **CRITICAL**: System failures (indexed, 90-day retention)

### Structured Logging Format
```json
{
  "timestamp": "2025-11-18T08:00:00.123Z",
  "level": "ERROR",
  "message": "Payment processing failed",
  "service": "saltbitter-api",
  "environment": "production",
  "dd.trace_id": "1234567890",
  "dd.span_id": "9876543210",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "payment_amount": 19.99,
  "stripe_error": "card_declined",
  "request_id": "req_abc123"
}
```

### Log Queries (Examples)

**All Errors in Last Hour**
```
status:error env:production @timestamp:[now-1h TO now]
```

**Payment Failures**
```
service:saltbitter-api "payment" status:error @timestamp:[now-24h TO now]
```

**Slow Database Queries**
```
service:saltbitter-api "Query took" @query_duration:>100
```

## Distributed Tracing

### Trace Sampling
- **Production**: 100% sampling (all requests traced)
- **Staging**: 100% sampling
- **Development**: 10% sampling (reduce overhead)

### Trace Analysis

**View Trace for Specific Request**
1. Copy `trace_id` from logs or error
2. Navigate to APM → Traces
3. Search by trace ID
4. View full request flow across services and external APIs

**Identify Slow Spans**
- APM → Service → Resource → Traces
- Sort by duration (p95/p99)
- Look for spans >100ms

## Real User Monitoring (RUM)

### Session Replay
- **Sampling**: 20% of sessions recorded
- **Privacy**: Mask all user input fields, emails, passwords
- **Retention**: 30 days

### Key RUM Metrics
```
rum.performance.navigation.load_time (p75 target: <3s)
rum.performance.largest_contentful_paint (p75 target: <2.5s)
rum.error.count (target: <10 errors/1000 sessions)
rum.action.count (user interactions)
```

### Frustration Signals
- Rage clicks (3+ clicks in 1 second)
- Dead clicks (click with no response)
- Error clicks (click that triggers error)

## Monitoring Checklist

### Daily
- [ ] Review error rate dashboard (target: <1%)
- [ ] Check payment failure count
- [ ] Verify backup completion
- [ ] Review slow query log

### Weekly
- [ ] Analyze performance trends (latency, throughput)
- [ ] Review infrastructure scaling (CPU, memory)
- [ ] Check disk usage growth
- [ ] Review business metrics (DAU, MRR, churn)

### Monthly
- [ ] Generate uptime report (target: 99.9%)
- [ ] Review alert effectiveness (false positives?)
- [ ] Optimize slow queries (>100ms)
- [ ] Clean up old logs (reduce costs)

## Cost Optimization

**Current DataDog Costs**: ~$2,000/month
- Hosts: 10 x $15 = $150/month
- APM: 10 hosts x $31 = $310/month
- Logs: 500 GB ingested x $0.10 = $50/month (after 15-day retention drop-off)
- RUM: 100K sessions x $0.00125 = $125/month
- Infrastructure monitoring: $200/month

**Cost Control Measures**:
- Index only ERROR and CRITICAL logs (exclude INFO/DEBUG in production)
- Set log retention: INFO (15 days), ERROR (30 days), CRITICAL (90 days)
- Use log patterns to deduplicate repeated errors
- Limit custom metrics to <100 unique metrics

## Related Documentation
- [Architecture Documentation](./ARCHITECTURE.md)
- [ADR-010: DataDog for Monitoring](./adrs/010-datadog-monitoring.md)
- [Incident Response](./INCIDENT_RESPONSE.md)

---

**Last Updated**: 2025-11-18
**Maintained By**: DevOps & Engineering Teams
