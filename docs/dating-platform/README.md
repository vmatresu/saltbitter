# SaltBitter: Psychology-Informed Dating Platform
## Complete Product Specification & Implementation Guide

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Platform Overview](#platform-overview)
3. [Core Documents](#core-documents)
4. [Technical Architecture](#technical-architecture)
5. [Implementation Roadmap](#implementation-roadmap)
6. [Development Setup](#development-setup)
7. [Testing & Quality Assurance](#testing--quality-assurance)
8. [Deployment & Operations](#deployment--operations)
9. [Team Structure](#team-structure)
10. [Success Metrics](#success-metrics)

---

## Executive Summary

**SaltBitter** is an ethical, psychology-informed dating platform that prioritizes user well-being over engagement metrics. Built on attachment theory research and transparent AI use, it addresses the documented mental health crisis in modern dating apps.

### Market Opportunity

- **$5.6B** global dating app market (2025)
- **20% CAGR** projected through 2030
- **71%** of singles report dating app fatigue
- **2.51x** higher psychological distress among heavy Tinder users
- **Zero** major competitors using attachment theory matching

### Competitive Advantages

1. **Attachment Theory Matching** (40% algorithm weight)
2. **Transparent AI** (EU AI Act & California SB 243 compliant)
3. **Ethical Monetization** (no pay-to-win, no dark patterns)
4. **Community Focus** (events, forums, therapy partnerships)
5. **Psychology Expertise** (built by psychologists for users)

### Financial Summary

| Metric | Year 1 | Year 2 | Year 5 |
|--------|--------|--------|--------|
| **Active Users** | 144,500 | 420,000 | 2.5M |
| **Conversion Rate** | 10.3% | 12% | 15% |
| **ARR** | $2.3M | $8.2M | $45M |
| **LTV/CAC** | 11.6:1 | 15:1 | 20:1 |
| **Break-Even** | Month 16 | Profitable | Profitable |

---

## Platform Overview

### Mission Statement

> "Help people build healthier relationships through psychology-informed matching, transparent AI tools, and a supportive community—without exploiting loneliness or addiction."

### Core Value Propositions

#### For Users
- **Understand yourself**: Free attachment assessment with personalized insights
- **Find compatible partners**: Matching algorithm weighted toward attachment compatibility
- **Build confidence**: AI practice companions for conversation skills (clearly labeled)
- **Date safely**: Photo verification, in-app video calls, integrated safety features
- **Grow together**: Community events, workshops, mental health resources

#### For Stakeholders
- **Ethical by design**: No dark patterns, transparent AI, privacy-first
- **Regulatory compliant**: EU AI Act, GDPR, CCPA, California SB 243
- **Sustainable business**: 10%+ conversion, $30+ LTV, <$3 CAC
- **Defensible moat**: Data network effects, therapist partnerships, community

---

## Core Documents

All specifications are located in `/docs/dating-platform/`:

### 1. [AI Transparency Flows](01-AI-TRANSPARENCY-FLOWS.md)
**What it covers**:
- User onboarding with AI disclosure
- AI profile encounter flows (🤖 badge, disclosure modals)
- AI conversation interfaces with real-time coaching
- Human match discovery (prioritized over AI)
- Opt-in/opt-out mechanisms
- Algorithmic transparency pages
- Paid feature transparency
- Data privacy & AI training disclosure

**Key deliverables**:
- 8 detailed user flow diagrams
- Compliance mapping to EU AI Act Article 52
- Code implementation examples
- UI/UX specifications

---

### 2. [Attachment Assessment Framework](02-ATTACHMENT-ASSESSMENT.md)
**What it covers**:
- 25-question validated assessment (ECR-R based)
- Scoring algorithm for anxiety & avoidance dimensions
- Four attachment styles: Secure, Anxious, Avoidant, Fearful
- Personalized insights and coaching recommendations
- Compatibility matrix for matching
- Psychometric validation plan

**Key deliverables**:
- Complete question set with scoring weights
- Python scoring implementation
- User-facing results page design
- Coaching recommendations by style pairing
- Non-pathologizing language guidelines

---

### 3. [Matching Algorithm](03-MATCHING-ALGORITHM.md)
**What it covers**:
- Multi-factor compatibility scoring:
  - **40%**: Attachment compatibility
  - **20%**: Shared interests & values
  - **15%**: Geographic proximity
  - **15%**: Communication style match
  - **10%**: Activity level alignment
- Ethical adjustments & fairness mechanisms
- Anti-pattern detection (e.g., anxious-avoidant trap)
- Transparency & auditability logs

**Key deliverables**:
- Complete pseudocode for matching engine
- Compatibility matrix with research citations
- Fairness adjustment algorithms
- Bias prevention mechanisms
- Performance metrics (47% match-to-conversation, 35% in-person dates)

---

### 4. [Premium Tiers & Monetization](04-PREMIUM-TIERS-MONETIZATION.md)
**What it covers**:
- 3-tier structure: Free, Premium ($12.99), Elite ($29.99)
- Feature comparison matrix (28 features)
- Ethical microtransaction pricing ($1.99-$19.99)
- Event-based revenue (workshops, speed dating)
- Dynamic pricing (ethical implementation)
- Revenue projections & unit economics

**Key deliverables**:
- Complete feature matrix
- Pricing strategy with rationale
- Revenue projections ($2.3M Year 1 ARR)
- LTV/CAC analysis (11.6:1 at Month 12)
- Customer retention modeling (55% annual retention)

---

### 5. [Compliance Checklist](05-COMPLIANCE-CHECKLIST.md)
**What it covers**:
- EU AI Act (Article 52 transparency obligations)
- California SB 243 (AI disclosure & opt-out)
- GDPR (special category data = psychological assessment)
- CCPA (California privacy rights)
- Data retention & deletion schedules
- Incident response & breach notification

**Key deliverables**:
- Quarterly compliance audit checklist
- Automated compliance testing (CI/CD integration)
- Data retention policy enforcement scripts
- Breach notification templates
- DPO (Data Protection Officer) responsibilities

**Penalties for non-compliance**:
- EU AI Act: €35M or 7% of global turnover
- GDPR: €20M or 4% of global turnover
- California SB 243: $2,500 per violation

---

### 6. [Revenue Projections](06-REVENUE-PROJECTIONS.md)
**What it covers**:
- Month-by-month breakdown (Months 1-12)
- User growth modeling (500 → 144,500 users)
- Revenue stream breakdown:
  - Subscriptions: 70% of revenue
  - Microtransactions: 24%
  - Events: 6%
- Cost structure & burn rate analysis
- Break-even analysis (Month 16)
- Sensitivity scenarios (best/base/worst case)

**Key deliverables**:
- Detailed P&L projections
- CAC/LTV cohort analysis
- Funding requirements ($2.5M seed round)
- Use of funds breakdown
- KPI dashboard specifications

---

### 7. [Ethical Design Audit](07-ETHICAL-DESIGN-AUDIT.md)
**What it covers**:
- 7-pillar framework:
  1. AI Transparency & Honesty
  2. Addiction Prevention & Mental Health
  3. Fair Monetization (No Pay-to-Win)
  4. Privacy & Data Minimization
  5. Algorithmic Fairness & Non-Discrimination
  6. Safety & Harm Prevention
  7. Vulnerable User Protection
- Dark pattern detection
- Automated ethical testing (CI/CD)
- Quarterly audit protocol
- Public transparency reporting

**Key deliverables**:
- Comprehensive audit scorecard (0-100 scale)
- Audit report template
- Automated test suite (`tests/ethical/`)
- User feedback integration plan
- Third-party validation protocol

---

## Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  • Web App (PWA)                                        │
│  • iOS App (React Native)                              │
│  • Android App (React Native)                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              API Gateway (FastAPI)                       │
│  • Authentication (JWT)                                 │
│  • Rate Limiting                                        │
│  • Request Validation                                   │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐   ┌──────────────┐
│   User       │   │   Matching   │
│   Service    │   │   Service    │
└──────┬───────┘   └──────┬───────┘
       │                  │
       ▼                  ▼
┌──────────────┐   ┌──────────────┐
│  PostgreSQL  │   │  Redis Cache │
│  (Primary)   │   │  (Sessions)  │
└──────────────┘   └──────────────┘
       │
       ▼
┌──────────────────────────────────┐
│       AI Services                │
│  • OpenAI GPT-4 (coaching)      │
│  • Custom NLP (moderation)      │
│  • Embeddings (interest match)  │
└──────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│    Storage & CDN                 │
│  • AWS S3 (photos)               │
│  • CloudFront (CDN)              │
└──────────────────────────────────┘
```

### Tech Stack

#### Backend
```yaml
Language: Python 3.11+
Framework: FastAPI
Database: PostgreSQL 15 (primary), Redis 7 (cache/sessions)
ORM: SQLAlchemy 2.0
Task Queue: Celery + Redis
Testing: pytest, pytest-cov, pytest-asyncio
Linting: Ruff, Black
Type Checking: MyPy (strict mode)
Security: Bandit, Safety
```

#### Frontend
```yaml
Web: React 18 + TypeScript
Mobile: React Native + Expo
State Management: Redux Toolkit
API Client: RTK Query
UI Library: Material-UI (customized)
Testing: Jest, React Testing Library, Playwright (E2E)
```

#### Infrastructure
```yaml
Cloud: AWS (multi-region)
Compute: ECS Fargate (containers)
Database: RDS PostgreSQL (Multi-AZ)
Cache: ElastiCache Redis
Storage: S3 + CloudFront
Monitoring: DataDog
Logging: CloudWatch + ELK Stack
CI/CD: GitHub Actions
IaC: Terraform
```

#### AI/ML
```yaml
LLM: OpenAI GPT-4 (AI coaching, icebreakers)
Embeddings: sentence-transformers (interest matching)
Moderation: Perspective API + custom models
Image Recognition: AWS Rekognition (photo verification)
```

### Database Schema (Simplified)

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP,
    subscription_tier VARCHAR(20) DEFAULT 'free',
    location GEOGRAPHY(POINT),
    CONSTRAINT valid_tier CHECK (subscription_tier IN ('free', 'premium', 'elite'))
);

-- Attachment Assessment
CREATE TABLE attachment_assessments (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    anxiety_score FLOAT NOT NULL CHECK (anxiety_score BETWEEN 1 AND 5),
    avoidance_score FLOAT NOT NULL CHECK (avoidance_score BETWEEN 1 AND 5),
    attachment_style VARCHAR(50) NOT NULL,
    completed_at TIMESTAMP DEFAULT NOW(),
    consent_given BOOLEAN DEFAULT FALSE  -- GDPR Article 9 compliance
);

-- Matches
CREATE TABLE matches (
    id UUID PRIMARY KEY,
    user_a_id UUID REFERENCES users(id),
    user_b_id UUID REFERENCES users(id),
    compatibility_score FLOAT CHECK (compatibility_score BETWEEN 0 AND 100),
    created_at TIMESTAMP DEFAULT NOW(),
    conversation_started BOOLEAN DEFAULT FALSE,
    UNIQUE(user_a_id, user_b_id)
);

-- AI Interactions (for transparency logs)
CREATE TABLE ai_interactions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    ai_type VARCHAR(50) NOT NULL,  -- 'practice_companion', 'icebreaker', 'coaching'
    disclosure_shown BOOLEAN DEFAULT TRUE,
    user_acknowledged BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Compliance Logs (GDPR/CCPA)
CREATE TABLE consent_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    consent_type VARCHAR(50) NOT NULL,  -- 'attachment_assessment', 'marketing', 'ai_training'
    granted BOOLEAN NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## Implementation Roadmap

### Phase 1: Foundation (Months 1-2)

#### Week 1-2: Infrastructure Setup
- [ ] AWS account setup (dev, staging, prod environments)
- [ ] Terraform infrastructure as code
- [ ] CI/CD pipelines (GitHub Actions)
- [ ] Database schema migrations (Alembic)
- [ ] Authentication system (JWT + refresh tokens)

#### Week 3-4: Core Features
- [ ] User registration & onboarding flow
- [ ] Profile creation & editing
- [ ] Photo upload & verification system
- [ ] Basic matching algorithm (v1.0)

#### Week 5-6: Attachment Assessment
- [ ] 25-question assessment UI
- [ ] Scoring algorithm implementation
- [ ] Results page with insights
- [ ] GDPR explicit consent flow

#### Week 7-8: Compliance & Testing
- [ ] EU AI Act disclosure implementation
- [ ] GDPR data export functionality
- [ ] Privacy policy & terms of service
- [ ] Security audit (penetration testing)

**Deliverables**:
- ✅ MVP with core matching
- ✅ Attachment assessment live
- ✅ Compliant with GDPR/CCPA
- ✅ Security-hardened infrastructure

---

### Phase 2: AI Features (Months 3-4)

#### Week 9-10: AI Practice Companions
- [ ] OpenAI GPT-4 integration
- [ ] AI profile creation (with 🤖 badges)
- [ ] Conversation interface
- [ ] Session summary & coaching feedback

#### Week 11-12: AI Transparency
- [ ] AI disclosure modals (onboarding)
- [ ] Opt-in/opt-out settings
- [ ] California SB 243 compliance
- [ ] AI interaction logging

#### Week 13-14: Communication Coaching
- [ ] Real-time tone analysis
- [ ] Suggestion generation
- [ ] Attachment-informed coaching
- [ ] Premium feature gating

#### Week 15-16: Testing & Optimization
- [ ] A/B testing framework
- [ ] AI feature engagement tracking
- [ ] Ethical audit (Pillar 1: AI Transparency)
- [ ] User feedback loops

**Deliverables**:
- ✅ AI practice companions live
- ✅ EU AI Act & SB 243 compliant
- ✅ Communication coaching (Premium)
- ✅ Ethical audit score >85/100

---

### Phase 3: Monetization (Months 5-6)

#### Week 17-18: Subscription System
- [ ] Stripe integration
- [ ] Premium tier features (unlimited matches)
- [ ] Elite tier features (AI coaching)
- [ ] Subscription management UI

#### Week 19-20: Microtransactions
- [ ] Profile boosts (with outcome transparency)
- [ ] Super likes
- [ ] AI icebreakers
- [ ] Spending safeguards ($50/$100 warnings)

#### Week 21-22: Events Platform
- [ ] Event listings (local & virtual)
- [ ] RSVP & ticketing system
- [ ] Calendar integration
- [ ] Post-event feedback

#### Week 23-24: Revenue Optimization
- [ ] A/B test pricing ($9.99 vs $12.99)
- [ ] Conversion funnel optimization
- [ ] Referral program launch
- [ ] Ethical audit (Pillar 3: Fair Monetization)

**Deliverables**:
- ✅ Monetization live (3 tiers)
- ✅ $5k MRR by Month 6
- ✅ LTV/CAC >3:1
- ✅ Events platform operational

---

### Phase 4: Growth & Scale (Months 7-12)

#### Months 7-8: Marketing & Acquisition
- [ ] Content marketing engine (SEO blog)
- [ ] Influencer partnerships (therapy influencers)
- [ ] PR strategy (launch press kit)
- [ ] Paid ads (Facebook, Google, TikTok)

#### Months 9-10: Community Building
- [ ] Forums & group chats
- [ ] User-generated content (success stories)
- [ ] Therapist partnership program
- [ ] Ambassador program (power users)

#### Months 11-12: Platform Maturity
- [ ] Video dating launch
- [ ] Advanced analytics dashboard
- [ ] Match success tracking (6-month relationships)
- [ ] Year-end optimization sprint

**Deliverables**:
- ✅ 144,500 active users
- ✅ $189k MRR
- ✅ 10.3% conversion rate
- ✅ Break-even trajectory by Month 16

---

## Development Setup

### Prerequisites

```bash
# Install dependencies
- Python 3.11+
- Node.js 18+
- PostgreSQL 15
- Redis 7
- Docker & Docker Compose
```

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/yourusername/saltbitter.git
cd saltbitter

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Environment variables
cp .env.example .env
# Edit .env with your settings:
# - DATABASE_URL=postgresql://localhost/saltbitter_dev
# - REDIS_URL=redis://localhost:6379
# - OPENAI_API_KEY=sk-...
# - JWT_SECRET_KEY=... (generate with `openssl rand -hex 32`)

# 4. Database migrations
alembic upgrade head

# 5. Run backend
uvicorn app.main:app --reload

# 6. Frontend setup (new terminal)
cd ../frontend
npm install
npm run dev

# 7. Run tests
pytest tests/ --cov=app --cov-report=html
npm test

# 8. Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Docker Development

```bash
# Quick start with Docker Compose
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# View logs
docker-compose logs -f

# Run tests
docker-compose exec backend pytest
docker-compose exec frontend npm test
```

---

## Testing & Quality Assurance

### Test Coverage Requirements

| Component | Coverage Target | Current |
|-----------|----------------|---------|
| **Backend** | ≥80% | - |
| **Frontend** | ≥70% | - |
| **Critical Paths** | 100% | - |

### Test Pyramid

```
┌─────────────────────────────────────┐
│        E2E Tests (5%)               │  ← Playwright: Complete user journeys
├─────────────────────────────────────┤
│     Integration Tests (25%)         │  ← API tests, DB integration
├─────────────────────────────────────┤
│       Unit Tests (70%)              │  ← Fast, isolated component tests
└─────────────────────────────────────┘
```

### Critical Test Scenarios

#### 1. Attachment Assessment Flow
```python
def test_attachment_assessment_with_consent():
    """Critical: GDPR Article 9 compliance"""
    user = create_user()

    # Should fail without explicit consent
    with pytest.raises(GDPRViolationError):
        start_assessment(user)

    # Grant consent
    user.give_consent("attachment_assessment")

    # Should now work
    assessment = start_assessment(user)
    assert assessment is not None
    assert assessment.consent_given == True
```

#### 2. AI Transparency
```python
def test_ai_disclosure_always_visible():
    """Critical: EU AI Act Article 52 compliance"""
    ai_profile = get_ai_profile()
    rendered_html = render_profile(ai_profile)

    assert "🤖" in rendered_html or "AI Practice Companion" in rendered_html
    assert "data-ai-disclosure" in rendered_html
```

#### 3. Fair Matching Algorithm
```python
def test_no_pay_to_win():
    """Critical: Ethical monetization"""
    free_user = create_user(tier="free")
    premium_user = create_user(tier="premium")

    free_matches = generate_matches(free_user)
    premium_matches = generate_matches(premium_user)

    # Same matching algorithm
    avg_free_score = mean([m.compatibility_score for m in free_matches[:10]])
    avg_premium_score = mean([m.compatibility_score for m in premium_matches[:10]])

    # <5% difference allowed
    assert abs(avg_free_score - avg_premium_score) < 5
```

### Quality Gates (CI/CD)

```yaml
# Required checks before merge to main:
- [ ] All tests pass (pytest, jest)
- [ ] Code coverage ≥80% (backend), ≥70% (frontend)
- [ ] No linting errors (Ruff, ESLint)
- [ ] No type errors (MyPy, TypeScript)
- [ ] Security scan passes (Bandit, npm audit)
- [ ] Ethical tests pass (dark pattern detection)
- [ ] Performance benchmarks met (API <200ms p95)
```

---

## Deployment & Operations

### Environments

| Environment | Purpose | Branch | Auto-Deploy |
|-------------|---------|--------|-------------|
| **Development** | Local testing | feature/* | No |
| **Staging** | Pre-production testing | develop | Yes (on push) |
| **Production** | Live users | main | Manual (requires approval) |

### Deployment Process

```bash
# 1. Feature development
git checkout -b feature/attachment-assessment
# ... make changes ...
git push origin feature/attachment-assessment

# 2. Pull request to develop
# - Automated tests run
# - Code review required (2 approvals)
# - Ethical audit checks pass

# 3. Merge to develop → Auto-deploy to Staging
git checkout develop
git merge feature/attachment-assessment
git push origin develop
# GitHub Actions deploys to staging

# 4. Staging validation
# - QA team tests on staging
# - Ethical audit review
# - Performance benchmarks

# 5. Promote to production
git checkout main
git merge develop
git tag v1.2.0
git push origin main --tags
# Manual approval required → Deploy to production
```

### Monitoring & Alerts

```yaml
# DataDog dashboards
- API Response Times (p50, p95, p99)
- Database Query Performance
- Error Rates (by endpoint)
- User Engagement Metrics
- Revenue Metrics (MRR, conversions)

# Alert thresholds
- Error rate >1%: Page on-call engineer
- API p95 >500ms: Slack alert
- Database CPU >80%: Auto-scale + alert
- Payment failures >5%: Page engineering + finance
```

### Disaster Recovery

**RTO (Recovery Time Objective)**: 4 hours
**RPO (Recovery Point Objective)**: 15 minutes

```yaml
Backup Strategy:
  Database:
    - Continuous replication (Multi-AZ RDS)
    - Daily snapshots (30-day retention)
    - Transaction log backups (every 15 min)

  Files (S3):
    - Cross-region replication (enabled)
    - Versioning (enabled)
    - Lifecycle policies (glacier after 90 days)

  Disaster Recovery Plan:
    - Documented runbook: docs/operations/disaster-recovery.md
    - Quarterly DR drills
    - Incident commander on-call rotation
```

---

## Team Structure

### Launch Team (Months 1-6)

```
CEO / Co-Founder
├─ CTO (Co-Founder)
│   ├─ Backend Engineer (2 FTE)
│   ├─ Frontend Engineer (1 FTE)
│   └─ DevOps Engineer (0.5 FTE, contractor)
│
├─ Head of Product
│   ├─ Product Designer (1 FTE)
│   └─ UX Researcher (0.5 FTE)
│
├─ Head of Marketing
│   ├─ Growth Marketer (1 FTE)
│   └─ Content Creator (0.5 FTE)
│
└─ Chief Psychology Officer (Clinical Psychologist)
    ├─ Attachment Theory Expert (1 FTE)
    └─ AI Ethics Advisor (0.5 FTE, consultant)
```

**Total Headcount**: 9-10 FTE (including contractors)

### Year 1 Hiring Plan

| Role | Start Month | Why |
|------|-------------|-----|
| **Backend Engineer #3** | Month 4 | Scaling infrastructure |
| **Frontend Engineer #2** | Month 4 | Mobile app development |
| **Customer Support Lead** | Month 6 | User growth (10k+ users) |
| **Data Analyst** | Month 7 | Analytics, A/B testing |
| **Community Manager** | Month 8 | Events, forums moderation |
| **Security Engineer** | Month 9 | Compliance, penetration testing |

---

## Success Metrics

### North Star Metric

**"6-Month Relationship Rate"**: % of users in relationships ≥6 months

**Target**: 22% (vs 8-12% industry average)

### Primary KPIs (Weekly Dashboard)

| Category | Metric | Month 1 | Month 6 | Month 12 | Target |
|----------|--------|---------|---------|----------|--------|
| **Growth** | Active Users | 500 | 38,600 | 144,500 | 100k+ |
| **Engagement** | DAU/MAU | 50% | 57% | 66% | >60% |
| **Monetization** | Conversion Rate | 3% | 7.6% | 10.3% | >10% |
| **Retention** | Monthly Churn | 15% | 7% | 4.7% | <5% |
| **Revenue** | MRR | $228 | $36k | $189k | >$150k |
| **Unit Economics** | CAC | $5.50 | $3.20 | $2.80 | <$3.00 |
| **Unit Economics** | LTV | $8.80 | $18.60 | $32.50 | >$30 |
| **Unit Economics** | LTV/CAC | 1.6:1 | 5.8:1 | 11.6:1 | >3:1 |
| **Success** | Match→Conversation | 30% | 42% | 47% | >40% |
| **Success** | First Date Rate | 20% | 30% | 35% | >30% |
| **Success** | 6-Month Relationship | 10% | 18% | 22% | >20% |

### Secondary KPIs (Monthly Review)

- **Net Promoter Score (NPS)**: Target >50
- **Attachment Assessment Completion**: Target >85%
- **AI Feature Engagement**: Target >30%
- **Event Attendance Rate**: Target >60%
- **Ethical Audit Score**: Target >85/100

---

## Risk Register

### Critical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Regulatory (EU AI Act penalties)** | Catastrophic | Low | Legal review, compliance checklist, quarterly audits |
| **Data breach (psychological data)** | Catastrophic | Low | Encryption, security audits, incident response plan |
| **Poor product-market fit** | High | Medium | Beta testing, user interviews, rapid iteration |
| **Low conversion (<7%)** | High | Medium | Aggressive A/B testing, pricing experiments |
| **Competitor (Hinge) copies features** | Medium | High | Deepen moat (therapist network, community events) |
| **Funding shortfall** | High | Low | Raise $2.5M (18-month runway), monitor burn rate |

---

## Getting Help

### Documentation

- **Product Specs**: `/docs/dating-platform/`
- **API Docs**: `http://localhost:8000/docs` (Swagger)
- **Architecture Decision Records**: `/docs/adr/`
- **Runbooks**: `/docs/operations/`

### Support Channels

- **Engineering**: Slack #engineering
- **Product Questions**: Slack #product
- **Compliance/Legal**: compliance@saltbitter.com
- **Ethics Review**: ethics@saltbitter.com

### Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Code style guidelines
- Pull request process
- Ethical review requirements
- Testing standards

---

## Appendix

### Key Research Citations

1. **Attachment Theory**: Hazan & Shaver (1987) - "Romantic love conceptualized as an attachment process"
2. **ECR-R Scale**: Fraley, Waller, & Brennan (2000) - Psychometric validation
3. **Dating App Mental Health**: Timmermans & De Caluwé (2017) - Tinder psychological distress study
4. **Algorithm Fairness**: Barocas & Selbst (2016) - "Big Data's Disparate Impact"
5. **Dark Patterns**: Mathur et al. (2019) - "Dark Patterns at Scale"

### Legal Resources

- **EU AI Act**: [https://artificialintelligenceact.eu](https://artificialintelligenceact.eu)
- **GDPR**: [https://gdpr-info.eu](https://gdpr-info.eu)
- **California SB 243**: [https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240SB243](https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240SB243)
- **CCPA**: [https://oag.ca.gov/privacy/ccpa](https://oag.ca.gov/privacy/ccpa)

### Industry Benchmarks

| Metric | Industry Average | SaltBitter Target | Source |
|--------|------------------|-------------------|--------|
| Conversion Rate | 3-8% | 10%+ | App Annie, 2024 |
| Annual Retention | 20-30% | 55% | Mobile Action, 2024 |
| Match→Date Rate | 15-20% | 30%+ | Internal Tinder data (leaked) |
| CAC | $8-15 | <$3 | Sensor Tower, 2024 |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-17 | Product Team | Initial comprehensive specification |

---

## License & Confidentiality

**⚠️ CONFIDENTIAL**: This document contains proprietary business information. Do not distribute outside authorized personnel.

**Copyright © 2025 SaltBitter, Inc. All rights reserved.**

---

## Next Steps

### For Developers
1. Read [Technical Architecture](#technical-architecture)
2. Set up [Development Environment](#development-setup)
3. Review [03-MATCHING-ALGORITHM.md](03-MATCHING-ALGORITHM.md)
4. Start with onboarding flow implementation

### For Product Team
1. Review all 7 core documents
2. Conduct user interviews (attachment theory validation)
3. Create high-fidelity mockups (Figma)
4. Plan Beta launch (Month 1)

### For Marketing
1. Review [06-REVENUE-PROJECTIONS.md](06-REVENUE-PROJECTIONS.md)
2. Draft positioning: "The dating app designed by psychologists"
3. Identify influencer partners (therapy influencers)
4. Plan PR strategy (launch press kit)

### For Leadership
1. Finalize seed funding ($2.5M raise)
2. Hire Data Protection Officer (DPO)
3. Secure legal counsel (EU privacy lawyer)
4. Set up advisory board (clinical psychologists)

---

**Ready to build the most ethical, psychology-informed dating platform? Let's start.**

🚀 **SaltBitter: Dating, reimagined with psychology and integrity.**
