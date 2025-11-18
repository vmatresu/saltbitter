# Incident Response Playbook

**Procedures for handling production incidents**

## Severity Levels

### SEV-1 (Critical)
- **Impact**: Complete service outage, data breach, payment processing down
- **Response Time**: Immediate (page on-call)
- **Communication**: Status page, email to all users

### SEV-2 (High)
- **Impact**: Major feature unavailable, significant performance degradation
- **Response Time**: Within 30 minutes
- **Communication**: Status page, Slack to team

### SEV-3 (Medium)
- **Impact**: Minor feature degradation, isolated user impact
- **Response Time**: Within 2 hours (business hours)
- **Communication**: Internal Slack only

### SEV-4 (Low)
- **Impact**: Cosmetic issues, no user impact
- **Response Time**: Next business day
- **Communication**: GitHub issue

## Incident Response Workflow

### 1. Detection
**How incidents are detected**:
- DataDog alerts trigger PagerDuty
- User reports (support@saltbitter.com)
- Team member observation
- Automated health checks

### 2. Triage (5 minutes)
**Incident Commander Actions**:
1. Acknowledge alert in PagerDuty
2. Assess severity (SEV-1 through SEV-4)
3. Create incident channel in Slack: `#incident-YYYY-MM-DD-description`
4. Update status page: https://status.saltbitter.com
5. Notify relevant stakeholders

**Triage Questions**:
- What is the impact? (users affected, features down)
- What is the scope? (all users, specific region, specific feature)
- When did it start?
- Is it escalating or stable?

### 3. Investigation (30-60 minutes)
**Check in order**:

1. **DataDog Dashboard**
   - Error rate spike?
   - Latency spike?
   - Traffic pattern anomaly?

2. **Service Health**
   ```bash
   # Check ECS services
   aws ecs describe-services --cluster saltbitter-prod --services saltbitter-api-prod
   
   # Check RDS
   aws rds describe-db-instances --db-instance-identifier saltbitter-prod
   
   # Check Redis
   aws elasticache describe-cache-clusters --cache-cluster-id saltbitter-prod
   ```

3. **Logs**
   - DataDog: Filter by `status:error` and `@timestamp:[now-1h TO now]`
   - Look for error spikes or new error types

4. **Recent Changes**
   ```bash
   # Check recent deployments
   git log --oneline -10
   
   # Check GitHub Actions
   gh run list --limit 5
   ```

5. **External Dependencies**
   - Stripe status: https://status.stripe.com
   - AWS status: https://status.aws.amazon.com
   - OpenAI status: https://status.openai.com

### 4. Communication
**Update cadence by severity**:
- SEV-1: Every 30 minutes
- SEV-2: Every hour
- SEV-3: Every 4 hours

**Status Page Template**:
```
[2025-11-18 08:00 UTC] Investigating
We are investigating reports of intermittent errors on the platform.

[2025-11-18 08:30 UTC] Identified
We have identified the issue as a database connection pool exhaustion.
Our team is working on a fix.

[2025-11-18 09:00 UTC] Monitoring
A fix has been deployed. We are monitoring the situation.

[2025-11-18 09:30 UTC] Resolved
The issue has been resolved. All services are operating normally.
```

### 5. Mitigation
**Common incident types and mitigations**:

**Database Connection Exhaustion**:
```bash
# Increase connection pool size
aws rds modify-db-instance \
  --db-instance-identifier saltbitter-prod \
  --max-connections 200 \
  --apply-immediately
```

**High Error Rate**:
```bash
# Rollback to previous deployment
aws ecs update-service \
  --cluster saltbitter-prod \
  --service saltbitter-api-prod \
  --task-definition saltbitter-api-prod:previous
```

**Memory Leak**:
```bash
# Restart ECS tasks
aws ecs update-service \
  --cluster saltbitter-prod \
  --service saltbitter-api-prod \
  --force-new-deployment
```

**Redis Cache Full**:
```bash
# Clear Redis cache (use carefully!)
redis-cli -h saltbitter-prod.cache.amazonaws.com FLUSHDB

# Or increase cache size
aws elasticache modify-cache-cluster \
  --cache-cluster-id saltbitter-prod \
  --cache-node-type cache.r7g.xlarge
```

### 6. Resolution
**When to mark resolved**:
- Root cause identified and fixed
- Monitoring shows normal metrics for 30+ minutes
- No new error reports from users

**Resolution checklist**:
- [ ] Incident resolved in production
- [ ] Status page updated to "Resolved"
- [ ] Stakeholders notified
- [ ] Incident channel archived
- [ ] Post-mortem scheduled within 48 hours

### 7. Post-Mortem
**Within 48 hours, document**:
- Timeline of events
- Root cause analysis
- Impact assessment (users affected, revenue impact)
- What went well
- What could be improved
- Action items (with owners and deadlines)

**Post-Mortem Template**: See `docs/postmortems/template.md`

## Escalation Paths

### On-Call Rotation
1. **Primary On-Call**: Paged first
2. **Secondary On-Call**: If primary doesn't respond in 5 minutes
3. **Engineering Manager**: If secondary doesn't respond in 5 minutes
4. **CTO**: For SEV-1 lasting >2 hours

### Contact Information
- **On-Call Engineer**: PagerDuty
- **Engineering Manager**: Slack DM
- **CTO**: +1-XXX-XXX-XXXX (phone)
- **Security Team**: security@saltbitter.com
- **Legal (data breach)**: legal@saltbitter.com

## Common Incident Scenarios

### Scenario 1: Database Outage
**Symptoms**: All API requests failing with 500 errors

**Investigation**:
```bash
# Check RDS status
aws rds describe-db-instances --db-instance-identifier saltbitter-prod

# Check connectivity
psql $DATABASE_URL -c "SELECT 1"
```

**Mitigation**:
- If RDS down: Wait for AWS to restore (Multi-AZ should auto-failover)
- If connection pool exhausted: Restart application or increase connections

### Scenario 2: Payment Processing Failure
**Symptoms**: Users reporting failed payments, Stripe webhooks failing

**Investigation**:
- Check Stripe Dashboard: https://dashboard.stripe.com
- Check webhook endpoint health: `/webhooks/stripe`
- Review recent payment error logs

**Mitigation**:
- If Stripe down: Wait for Stripe, notify users via status page
- If webhook endpoint failing: Fix and replay failed webhooks

### Scenario 3: Memory Leak
**Symptoms**: Gradual increase in memory usage, eventually OOM kills

**Investigation**:
- DataDog: Check memory usage over time
- Identify which service/endpoint is leaking

**Mitigation**:
- Short-term: Restart affected services
- Long-term: Profile application, find and fix leak

## Tools & Resources

- **DataDog**: https://app.datadoghq.com
- **AWS Console**: https://console.aws.amazon.com
- **Status Page**: https://status.saltbitter.com
- **PagerDuty**: https://saltbitter.pagerduty.com
- **GitHub Actions**: https://github.com/vmatresu/saltbitter/actions

## Related Documentation
- [Deployment Runbook](./DEPLOYMENT.md)
- [Monitoring Documentation](./MONITORING.md)
- [Disaster Recovery](./DISASTER_RECOVERY.md)

---

**Last Updated**: 2025-11-18
**Maintained By**: DevOps & Engineering Teams
