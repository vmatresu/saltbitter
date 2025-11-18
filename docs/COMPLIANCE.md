# GDPR Compliance Documentation

**Data Protection and Privacy Compliance for SaltBitter**

## Overview

SaltBitter is fully compliant with:
- **GDPR** (General Data Protection Regulation, EU)
- **EU AI Act** (Article 52, transparency requirements)
- **California SB 243** (AI disclosure and opt-out requirements)

## GDPR Rights Implementation

### 1. Right to Access (Article 15)
**Endpoint**: `GET /api/compliance/data-export`

**Implementation**:
- User requests data export via settings or API
- System compiles all user data (profile, messages, matches, payments)
- Data exported as JSON or CSV
- Delivered via email within 48 hours (SLA)

**What's Included**:
- Personal information (name, email, DOB)
- Profile data (bio, photos, interests)
- Attachment assessment results
- Match history and compatibility scores
- Message history
- Subscription and payment records
- Consent logs
- AI interaction logs

### 2. Right to Rectification (Article 16)
**Endpoint**: `PUT /api/profiles/me`

Users can update their profile data at any time through the app or API.

### 3. Right to Erasure ("Right to be Forgotten", Article 17)
**Endpoint**: `DELETE /api/compliance/data-deletion`

**Implementation**:
- User requests account deletion
- 30-day grace period for account recovery
- After 30 days, all user data permanently deleted:
  - User account and profile
  - Messages (marked as "deleted user")
  - Match records (anonymized)
  - Subscription canceled
  - Photos removed from S3
- Compliance logs retained for 7 years (legal requirement)

**Exceptions** (data NOT deleted):
- Aggregated analytics (anonymized)
- Financial records (7-year retention for tax purposes)
- Abuse reports and safety records

### 4. Right to Restrict Processing (Article 18)
**Endpoint**: `POST /api/settings/restrict-processing`

Users can restrict how their data is used (e.g., no marketing emails, no AI features).

### 5. Right to Data Portability (Article 20)
Data export provided in machine-readable format (JSON).

### 6. Right to Object (Article 21)
Users can object to:
- Marketing emails (opt-out link in all emails)
- AI features (opt-out in settings)
- Profiling for targeted advertising (we don't do this)

## Consent Management

### Types of Consent

1. **Essential** (no opt-out):
   - Terms of Service
   - Privacy Policy
   - Security and fraud prevention

2. **Optional** (opt-in required):
   - AI practice companions
   - AI relationship coaching
   - Marketing emails
   - Push notifications

### Consent Logging
All consent actions logged in `consent_logs` table:
```sql
{
  "user_id": "uuid",
  "consent_type": "ai_features",
  "granted": true,
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "timestamp": "2025-11-18T08:00:00Z"
}
```

## Data Breach Notification (Article 33-34)

### Breach Detection
- Automated monitoring (DataDog security alerts)
- Database access logs (CloudTrail)
- Anomaly detection (unusual data access patterns)

### Breach Response Timeline
1. **Detection**: Immediately upon discovery
2. **Assessment**: Within 2 hours (severity, impact, affected users)
3. **Containment**: Within 4 hours (stop breach, revoke credentials)
4. **Authority Notification**: Within 72 hours (notify data protection authority)
5. **User Notification**: Within 72 hours (if high risk to users)
6. **Post-Mortem**: Within 7 days (root cause, prevention measures)

### Notification Template
```
Subject: Important Security Notice

Dear [User],

We are writing to inform you of a data security incident that may have affected your SaltBitter account.

What Happened:
On [date], we discovered [description of breach].

What Information Was Involved:
[List of affected data types: email, profile data, etc.]

What We're Doing:
- [Containment measures]
- [Investigation steps]
- [Prevention measures]

What You Should Do:
- Change your password immediately
- Enable two-factor authentication
- Monitor your accounts for suspicious activity

Contact Us:
security@saltbitter.com or call +1-XXX-XXX-XXXX

We sincerely apologize for this incident.

SaltBitter Security Team
```

## Data Protection Officer (DPO)

**DPO Contact**: dpo@saltbitter.com
**Responsibilities**:
- Monitor GDPR compliance
- Advise on data protection impact assessments
- Cooperate with supervisory authorities
- Point of contact for data subjects

## Data Processing Records (Article 30)

### Categories of Data
1. **Identity Data**: Name, email, date of birth
2. **Profile Data**: Bio, photos, interests, location
3. **Behavioral Data**: Matches liked/passed, messages sent
4. **Financial Data**: Subscription tier, payment records (stored by Stripe)
5. **Technical Data**: IP address, device info, usage logs
6. **Sensitive Data**: Attachment style assessment (special category under GDPR)

### Legal Basis for Processing
- **Contract**: To provide dating platform services (GDPR Art. 6(1)(b))
- **Consent**: For AI features, marketing (GDPR Art. 6(1)(a))
- **Legitimate Interest**: Fraud prevention, security (GDPR Art. 6(1)(f))
- **Legal Obligation**: Financial records, breach notification (GDPR Art. 6(1)(c))

### Data Retention
- Active accounts: Indefinite
- Deleted accounts: 30-day grace period, then permanent deletion
- Financial records: 7 years (legal requirement)
- Compliance logs: 7 years
- Application logs: 90 days

## Third-Party Data Processors

All third-party processors have signed Data Processing Agreements (DPAs):

| Processor | Purpose | Data Shared | DPA Signed |
|-----------|---------|-------------|------------|
| AWS | Infrastructure hosting | All user data | ✅ Yes |
| Stripe | Payment processing | Email, payment info | ✅ Yes |
| OpenAI | AI features (optional) | Messages to AI (if opted in) | ✅ Yes |
| DataDog | Monitoring | Logs (no PII) | ✅ Yes |
| AWS SES | Transactional emails | Email addresses | ✅ Yes |

## Privacy by Design

### Principles Implemented
1. **Data Minimization**: Only collect necessary data
2. **Purpose Limitation**: Use data only for stated purposes
3. **Storage Limitation**: Delete data when no longer needed
4. **Integrity & Confidentiality**: Encryption in transit and at rest
5. **Accountability**: Comprehensive audit logs

### Technical Measures
- Encryption: TLS 1.3 (transit), AES-256 (rest)
- Access Control: Role-based access, least privilege
- Pseudonymization: UUIDs instead of sequential IDs
- Logging: All data access logged

## Compliance Checklist

### Before Launch
- [ ] Privacy Policy published and accessible
- [ ] Terms of Service published
- [ ] Cookie banner implemented (if using cookies)
- [ ] Consent mechanisms functional
- [ ] Data export API tested
- [ ] Data deletion API tested
- [ ] DPO appointed and contact published
- [ ] DPAs signed with all processors
- [ ] Breach notification procedures documented
- [ ] Staff trained on GDPR procedures

### Ongoing (Monthly)
- [ ] Review consent logs for anomalies
- [ ] Audit third-party processor compliance
- [ ] Review data retention policies
- [ ] Update privacy policy if services change

### Quarterly
- [ ] Generate compliance report
- [ ] Review data export requests (response time)
- [ ] Review data deletion requests (response time)
- [ ] Test breach notification procedures

## User Rights Request Handling

### Data Export Request
1. User submits request via API or settings
2. System queues export job (Celery task)
3. Export generated within 48 hours
4. User notified via email with download link
5. Link expires after 7 days

### Data Deletion Request
1. User submits request
2. 30-day grace period begins
3. User can cancel during grace period
4. After 30 days, automated deletion job runs
5. User receives confirmation email

### Response Time SLAs
- Data export: 48 hours
- Data deletion: 30 days (with grace period)
- Consent withdrawal: Immediate
- Privacy inquiry: 72 hours

---

**Last Updated**: 2025-11-18
**DPO Contact**: dpo@saltbitter.com
**Maintained By**: Legal & Compliance Team
