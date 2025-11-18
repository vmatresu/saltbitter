# Disaster Recovery Plan

**Business Continuity and Disaster Recovery Procedures**

## Overview

**Recovery Objectives**:
- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 15 minutes

This means:
- We can restore service within 4 hours of catastrophic failure
- We can recover data to within 15 minutes of the incident

## Disaster Scenarios

### 1. Complete AWS Region Failure
**Likelihood**: Low (1-2 times per decade per region)
**Impact**: Complete service outage

**Recovery Plan**:
1. **Immediate** (0-30 min):
   - Declare SEV-1 incident
   - Notify all stakeholders
   - Update status page

2. **Preparation** (30 min - 2 hours):
   - Restore database from latest snapshot to new region
   - Deploy application to new region using Terraform
   - Update DNS to point to new region

3. **Verification** (2-4 hours):
   - Run smoke tests
   - Verify data integrity
   - Monitor for issues

**Prerequisites**:
- Cross-region RDS snapshots (daily)
- Terraform configurations version-controlled
- DNS with short TTL (5 minutes)

### 2. Database Corruption
**Likelihood**: Medium (rare but possible)
**Impact**: Data loss or integrity issues

**Recovery Plan**:
```bash
# 1. Stop all writes immediately
aws ecs update-service \
  --cluster saltbitter-prod \
  --service saltbitter-api-prod \
  --desired-count 0

# 2. Identify last known good snapshot
aws rds describe-db-snapshots \
  --db-instance-identifier saltbitter-prod \
  --query 'reverse(sort_by(DBSnapshots, &SnapshotCreateTime))[:10]'

# 3. Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier saltbitter-prod-restored \
  --db-snapshot-identifier rds:saltbitter-prod-2025-11-18-03-00

# 4. Point application to restored database
# Update environment variable DATABASE_URL

# 5. Restart application
aws ecs update-service \
  --cluster saltbitter-prod \
  --service saltbitter-api-prod \
  --desired-count 4
```

**Data Loss**: Up to 15 minutes (last backup)

### 3. Accidental Data Deletion
**Likelihood**: Medium
**Impact**: User data loss

**Recovery Plan**:
```bash
# Option 1: Point-in-Time Recovery (within 5 minutes)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier saltbitter-prod \
  --target-db-instance-identifier saltbitter-prod-pitr \
  --restore-time "2025-11-18T08:30:00Z"

# Option 2: Restore specific data from backup
pg_restore -d saltbitter_prod -t users backup.sql
```

### 4. Security Breach / Ransomware
**Likelihood**: Low-Medium
**Impact**: Data exposure, service disruption

**Recovery Plan**:
1. **Containment** (Immediate):
   - Isolate affected systems
   - Revoke all credentials and API keys
   - Block suspicious IP addresses

2. **Assessment** (0-2 hours):
   - Identify scope of breach
   - Determine if data was exfiltrated
   - Assess if backups are compromised

3. **Recovery** (2-8 hours):
   - Restore from clean backup (verified malware-free)
   - Rebuild infrastructure from scratch if needed
   - Rotate all secrets and credentials

4. **Notification** (Within 72 hours):
   - Notify affected users (GDPR requirement)
   - Notify data protection authority
   - Public disclosure if required

### 5. S3 Bucket Deletion
**Likelihood**: Low (requires explicit confirmation)
**Impact**: All user photos lost

**Recovery Plan**:
- **Immediate**: Enable S3 versioning (prevents permanent deletion)
- **If already deleted**: Restore from S3 backup bucket (if configured)
- **If no backup**: Photos are lost (notify users, apologize)

**Prevention**:
```bash
# Enable versioning
aws s3api put-bucket-versioning \
  --bucket saltbitter-photos \
  --versioning-configuration Status=Enabled

# Enable cross-region replication
aws s3api put-bucket-replication \
  --bucket saltbitter-photos \
  --replication-configuration file://replication-config.json
```

## Backup Strategy

### Database (PostgreSQL)
**Automated Backups**:
- Daily snapshots at 3:00 AM UTC (retained 7 days)
- Point-in-time recovery enabled (5-minute granularity)
- Cross-region snapshot copy (us-west-2 backup region)

**Manual Backups** (before major changes):
```bash
aws rds create-db-snapshot \
  --db-instance-identifier saltbitter-prod \
  --db-snapshot-identifier manual-pre-migration-2025-11-18
```

### Redis (ElastiCache)
**Automated Backups**:
- Daily RDB snapshots at 4:00 AM UTC (retained 5 days)
- AOF (Append-Only File) enabled for durability

### S3 (Photos)
**Strategy**:
- Versioning enabled (can recover deleted files)
- Cross-region replication to us-west-2
- Lifecycle policy: Archive to Glacier after 1 year

### Code and Configuration
**Git Repository**:
- Hosted on GitHub (redundant infrastructure)
- Local clones on team members' machines
- Terraform state stored in S3 with versioning

## Testing Disaster Recovery

### Quarterly DR Test
1. **Announce test** (scheduled maintenance window)
2. **Perform restore** from backup to staging environment
3. **Verify data integrity** (run automated checks)
4. **Test application functionality** (smoke tests)
5. **Document results** (time taken, issues found)

### Annual Full DR Drill
1. **Simulate complete region failure**
2. **Restore to different AWS region**
3. **Measure actual RTO** (compare to 4-hour target)
4. **Document and improve** recovery procedures

## Data Retention Policy

| Data Type | Retention Period | Backup Frequency |
|-----------|------------------|------------------|
| User data (active) | Indefinite | Daily + PITR |
| Deleted user data | 30 days (grace) | Daily |
| Database snapshots | 7 days | Daily |
| Application logs | 90 days | Real-time |
| Compliance logs | 7 years | Real-time |
| Financial records | 7 years | Daily |

## Contact Information

### Incident Response Team
- **Incident Commander**: On-call engineer (PagerDuty)
- **Database Admin**: DBA on-call (PagerDuty)
- **Security Lead**: security@saltbitter.com
- **CTO**: (phone number)

### External Contacts
- **AWS Support**: Premium support (phone)
- **DataDog Support**: support@datadoghq.com
- **Legal**: legal@saltbitter.com (for data breach)

## Related Documentation
- [Incident Response Playbook](./INCIDENT_RESPONSE.md)
- [Deployment Runbook](./DEPLOYMENT.md)
- [GDPR Compliance](./COMPLIANCE.md)

---

**Last Updated**: 2025-11-18
**Next DR Test**: 2026-02-18
**Maintained By**: DevOps & Security Teams
