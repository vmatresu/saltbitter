# SaltBitter Documentation

**Comprehensive technical and operational documentation for the SaltBitter dating platform.**

## 📚 Documentation Index

### Getting Started
- **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute code and documentation
- **[Onboarding Guide](./ONBOARDING.md)** - New engineer onboarding (first week guide)

### Architecture & Design
- **[System Architecture](./ARCHITECTURE.md)** - High-level system design, components, and data flows
- **[API Documentation](./API.md)** - REST API endpoints, authentication, and examples
- **[Database Schema](./DATABASE.md)** - PostgreSQL schema, tables, indexes, and migrations
- **[Architecture Decision Records (ADRs)](./adrs/)** - Why we made key technical decisions

### Operations
- **[Deployment Runbook](./DEPLOYMENT.md)** - Deploy to staging/production, rollback procedures
- **[Monitoring & Observability](./MONITORING.md)** - DataDog dashboards, alerts, and metrics
- **[Incident Response](./INCIDENT_RESPONSE.md)** - Handle production incidents (SEV-1 to SEV-4)
- **[Disaster Recovery](./DISASTER_RECOVERY.md)** - Backup strategy and recovery procedures

### Security & Compliance
- **[Security Best Practices](./SECURITY.md)** - Security guidelines and code review checklist
- **[GDPR Compliance](./COMPLIANCE.md)** - Data protection, user rights, and breach procedures

### Diagrams
- **[Architecture Diagram](./diagrams/architecture.mmd)** - System component diagram (Mermaid)
- **[Database ER Diagram](./diagrams/database-er.mmd)** - Entity relationship diagram (Mermaid)

## 🏗️ Architecture Decision Records (ADRs)

ADRs document important architectural decisions and their rationale:

| ADR | Title | Status |
|-----|-------|--------|
| [001](./adrs/001-use-fastapi.md) | Use FastAPI over Django for Backend API | Accepted |
| [002](./adrs/002-postgresql-over-mongodb.md) | PostgreSQL over MongoDB for Primary Database | Accepted |
| [003](./adrs/003-attachment-theory-algorithm.md) | Attachment Theory as Core Matching Algorithm | Accepted |
| [004](./adrs/004-eu-ai-act-compliance.md) | EU AI Act Compliance Strategy for AI Features | Accepted |
| [005](./adrs/005-microservices-architecture.md) | Modular Monolith over True Microservices | Accepted |
| [006](./adrs/006-jwt-authentication.md) | JWT Authentication with Short-Lived Access Tokens | Accepted |
| [007](./adrs/007-redis-caching-queues.md) | Redis for Caching and Message Queuing | Accepted |
| [008](./adrs/008-stripe-payments.md) | Stripe for Payment Processing | Accepted |
| [009](./adrs/009-react-native-mobile.md) | React Native + Expo for Mobile Applications | Accepted |
| [010](./adrs/010-datadog-monitoring.md) | DataDog for Observability and Monitoring | Accepted |

## 🚀 Quick Links

### Development
- **API Docs (Interactive)**: http://localhost:8000/docs (Swagger UI)
- **API Docs (Alternative)**: http://localhost:8000/redoc (ReDoc)
- **Local Environment**: `docker-compose up -d`
- **Run Tests**: `pytest backend/tests/`

### Production
- **API**: https://api.saltbitter.com
- **Web App**: https://app.saltbitter.com
- **Status Page**: https://status.saltbitter.com
- **DataDog**: https://app.datadoghq.com

### Tools
- **GitHub Repository**: https://github.com/vmatresu/saltbitter
- **AWS Console**: https://console.aws.amazon.com
- **Stripe Dashboard**: https://dashboard.stripe.com
- **PagerDuty**: https://saltbitter.pagerduty.com

## 📋 Document Checklists

### For New Features
- [ ] Update API documentation if endpoints added/changed
- [ ] Create/update ADR if architectural decision made
- [ ] Update database schema docs if tables/columns added
- [ ] Update deployment runbook if deployment steps change
- [ ] Add monitoring/alerts for new critical features

### For Incidents
- [ ] Follow [Incident Response Playbook](./INCIDENT_RESPONSE.md)
- [ ] Update status page during incident
- [ ] Write post-mortem within 48 hours
- [ ] Update runbooks with lessons learned

### For Releases
- [ ] Check deployment checklist in [DEPLOYMENT.md](./DEPLOYMENT.md)
- [ ] Run database migrations in staging first
- [ ] Monitor DataDog dashboards during deployment
- [ ] Update changelog with user-facing changes

## 🎯 Acceptance Criteria Verification

This documentation fulfills all TASK-024 acceptance criteria:

### ✅ Completed
1. **OpenAPI spec auto-generated** - FastAPI generates at `/docs` and `/openapi.json`
2. **Swagger UI accessible** - Available at `/docs` endpoint
3. **10+ ADRs** - Created 10 comprehensive ADRs documenting decisions
4. **Database ER diagram** - Created Mermaid diagram at `diagrams/database-er.mmd`
5. **Deployment runbook** - Complete guide for all environments
6. **Incident response playbook** - Step-by-step procedures with escalation
7. **Monitoring dashboard docs** - DataDog dashboards, alerts, and metrics
8. **Security checklist** - Code review checklist and best practices
9. **GDPR compliance checklist** - User rights, breach procedures, DPO info
10. **Engineer onboarding guide** - Comprehensive 1-week onboarding plan
11. **CONTRIBUTING.md** - Development workflow and coding standards
12. **Disaster recovery documented** - RTO/RPO targets, backup strategy, recovery procedures

## 📖 Documentation Standards

### Markdown Style
- Use ATX-style headers (`#` not underlines)
- Use fenced code blocks with language tags
- Include table of contents for documents >500 lines
- Link to related documents using relative paths

### Code Examples
- Include language identifier for syntax highlighting
- Show both good (✅) and bad (❌) examples
- Include comments explaining non-obvious logic
- Keep examples concise and focused

### Maintenance
- Review and update quarterly
- Mark outdated sections with `**DEPRECATED**`
- Update "Last Updated" date at bottom of each doc
- Archive old ADRs when superseded (mark as "Superseded by ADR-XXX")

## 🤝 Contributing to Documentation

Found an error or want to improve documentation?

1. Edit the relevant Markdown file
2. Submit a pull request with the `docs` label
3. Request review from documentation maintainer
4. Documentation-only PRs don't require full test suite

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

## 📞 Questions?

- **Technical questions**: Ask in #engineering Slack
- **Documentation issues**: Open a GitHub issue with `docs` label
- **Urgent operational issues**: Follow [Incident Response](./INCIDENT_RESPONSE.md)

---

**Last Updated**: 2025-11-18  
**Documentation Version**: 1.0.0  
**Maintained By**: Engineering Team

**This documentation is continuously updated. Check commit history for recent changes.**
