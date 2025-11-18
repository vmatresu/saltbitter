# Deployment Runbook

**SaltBitter Platform Deployment Procedures**

## Overview

The SaltBitter platform uses a three-environment deployment strategy:
- **Development**: Local Docker Compose
- **Staging**: AWS ECS Fargate (auto-deploy from `develop` branch)
- **Production**: AWS ECS Fargate (manual approval from `main` branch)

## Prerequisites

- AWS CLI configured with appropriate credentials
- Docker installed locally
- GitHub Actions access (automatic deployments)
- DataDog API key (for monitoring)
- PagerDuty integration (for alerts)

## Deployment Environments

### Development (Local)

**Start Services:**
```bash
# Clone repository
git clone https://github.com/vmatresu/saltbitter.git
cd saltbitter

# Copy environment variables
cp .env.example .env

# Edit .env with local configuration
# Start all services
docker-compose up -d

# Check service health
docker-compose ps
curl http://localhost:8000/health
```

**Stop Services:**
```bash
docker-compose down
```

### Staging Environment

**Automatic Deployment:**
- Triggered on push to `develop` branch
- GitHub Actions runs tests and deploys automatically
- URL: https://staging-api.saltbitter.com

**Manual Deployment:**
```bash
# Trigger GitHub Actions workflow manually
gh workflow run deploy-staging.yml

# Or deploy via AWS ECS
aws ecs update-service \
  --cluster saltbitter-staging \
  --service saltbitter-api-staging \
  --force-new-deployment
```

### Production Environment

**Deployment Process:**
1. Merge PR to `main` branch
2. GitHub Actions builds and tests
3. Awaits manual approval
4. Deploys using blue/green strategy
5. Runs smoke tests
6. Completes deployment

**Manual Approval:**
```bash
# Approve deployment in GitHub Actions UI
# Or via CLI
gh run list --workflow=deploy-production.yml
gh run watch <run-id>
# Approve when prompted
```

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing in CI
- [ ] Code coverage ≥85%
- [ ] Security scans clean (Bandit, Dependabot)
- [ ] Database migrations tested in staging
- [ ] Feature flags configured (if applicable)
- [ ] Rollback plan documented
- [ ] Team notified in #deploys Slack channel

### During Deployment
- [ ] Monitor DataDog dashboards
- [ ] Watch error rates and latency
- [ ] Verify health check endpoints
- [ ] Test critical user flows (login, match generation, payments)

### Post-Deployment
- [ ] Smoke tests passing
- [ ] No spike in error rates
- [ ] Performance metrics within targets
- [ ] User-facing features working
- [ ] Update status page if needed
- [ ] Document deployment in changelog

## Database Migrations

**Test Migration in Staging:**
```bash
# SSH into staging ECS task
aws ecs execute-command \
  --cluster saltbitter-staging \
  --task <task-id> \
  --command "/bin/bash" \
  --interactive

# Inside container
cd /app/backend
alembic current
alembic upgrade head
alembic current  # Verify
```

**Run Migration in Production:**
```bash
# Production migrations run automatically during deployment
# But can be run manually if needed

# Get production task ID
aws ecs list-tasks --cluster saltbitter-prod --service saltbitter-api-prod

# Execute command
aws ecs execute-command \
  --cluster saltbitter-prod \
  --task <task-id> \
  --command "alembic upgrade head" \
  --interactive
```

**Rollback Migration:**
```bash
# Rollback one step
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision-id>
```

## Rollback Procedures

### Application Rollback (Blue/Green)

**Automatic Rollback:**
- If smoke tests fail, deployment automatically rolls back
- Previous task definition remains available

**Manual Rollback:**
```bash
# List recent task definitions
aws ecs list-task-definitions --family-prefix saltbitter-api-prod --max-items 5

# Update service to previous task definition
aws ecs update-service \
  --cluster saltbitter-prod \
  --service saltbitter-api-prod \
  --task-definition saltbitter-api-prod:123  # Previous version

# Monitor rollback
aws ecs describe-services \
  --cluster saltbitter-prod \
  --services saltbitter-api-prod
```

### Database Rollback

**Option 1: Revert Migration**
```bash
alembic downgrade -1
```

**Option 2: Restore from Snapshot** (destructive, last resort)
```bash
# Find recent snapshot
aws rds describe-db-snapshots \
  --db-instance-identifier saltbitter-prod \
  --query 'reverse(sort_by(DBSnapshots, &SnapshotCreateTime))[:5]'

# Restore (creates new instance)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier saltbitter-prod-restored \
  --db-snapshot-identifier <snapshot-id>

# Update connection strings (requires downtime)
```

## Configuration Management

### Environment Variables

**Staging:**
```bash
# Update via AWS Systems Manager Parameter Store
aws ssm put-parameter \
  --name /saltbitter/staging/DATABASE_URL \
  --value "postgresql://..." \
  --type SecureString \
  --overwrite
```

**Production:**
```bash
# Update via AWS Secrets Manager
aws secretsmanager update-secret \
  --secret-id saltbitter/prod/app-secrets \
  --secret-string '{"DATABASE_URL":"postgresql://..."}'

# Restart service to pick up new secrets
aws ecs update-service \
  --cluster saltbitter-prod \
  --service saltbitter-api-prod \
  --force-new-deployment
```

## Monitoring During Deployment

### Key Metrics to Watch

**DataDog Dashboard: Deployment**
- Error rate (target: <1%)
- API latency p95 (target: <200ms)
- Request rate (should remain stable)
- Database connections (should not spike)
- Memory usage (should remain <80%)

**Alerts During Deployment:**
- Temporarily silence non-critical alerts
- Keep critical alerts active (error rate >5%, database down)

### Smoke Tests

**Automated (runs in CI/CD):**
```bash
# Run smoke tests
cd tests/smoke
pytest test_smoke.py -v

# Tests include:
# - Health check endpoint
# - Authentication flow
# - Profile creation
# - Match generation
# - Payment processing (test mode)
```

**Manual Verification:**
```bash
# Health check
curl https://api.saltbitter.com/health

# Authentication
curl -X POST https://api.saltbitter.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Get matches (with valid token)
curl https://api.saltbitter.com/api/matches \
  -H "Authorization: Bearer <token>"
```

## Troubleshooting

### Deployment Stuck

```bash
# Check ECS service events
aws ecs describe-services \
  --cluster saltbitter-prod \
  --services saltbitter-api-prod \
  --query 'services[0].events[:10]'

# Check task logs
aws logs tail /ecs/saltbitter-prod --follow
```

### Health Check Failing

```bash
# Check ECS target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>

# SSH into task and debug
aws ecs execute-command \
  --cluster saltbitter-prod \
  --task <task-id> \
  --command "/bin/bash" \
  --interactive

# Check application logs
tail -f /var/log/app.log
```

### Database Connection Issues

```bash
# Verify RDS is accessible
aws rds describe-db-instances \
  --db-instance-identifier saltbitter-prod \
  --query 'DBInstances[0].[DBInstanceStatus,Endpoint.Address]'

# Test connection from ECS task
psql $DATABASE_URL -c "SELECT 1"
```

## Emergency Procedures

### Complete Rollback (Last Resort)

1. **Roll back application** to previous task definition
2. **Roll back database** migration (if applicable)
3. **Clear Redis cache** to prevent stale data issues
4. **Notify team** in #incidents Slack channel
5. **Update status page** with incident details
6. **Schedule post-mortem** within 24 hours

### Hotfix Deployment

```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug-fix

# Make fix and commit
git commit -m "hotfix: Fix critical payment processing bug"

# Push and create PR
git push origin hotfix/critical-bug-fix
gh pr create --base main --title "[HOTFIX] Fix payment bug"

# Fast-track approval and merge
# Deployment will trigger automatically
```

## Related Documentation
- [Architecture Documentation](./ARCHITECTURE.md)
- [Database Documentation](./DATABASE.md)
- [Incident Response](./INCIDENT_RESPONSE.md)
- [Disaster Recovery](./DISASTER_RECOVERY.md)

---

**Last Updated**: 2025-11-18
**Maintained By**: DevOps Team
