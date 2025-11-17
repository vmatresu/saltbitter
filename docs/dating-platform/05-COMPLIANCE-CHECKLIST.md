# Regulatory Compliance Checklist
## EU AI Act + California SB 243 + GDPR/CCPA

---

## Executive Summary

SaltBitter operates in a highly regulated space at the intersection of:
- **AI-powered systems** (EU AI Act, California SB 243)
- **Personal data processing** (GDPR, CCPA)
- **Social/Dating platforms** (EU Digital Services Act, consumer protection laws)

**Risk Classification**:
- EU AI Act: **Limited Risk** (requires transparency obligations)
- California SB 243: **Covered** (AI-generated content must be disclosed)

**Penalties for Non-Compliance**:
- EU AI Act: Up to €35M or 7% of global annual turnover (whichever is higher)
- GDPR: Up to €20M or 4% of global annual turnover
- California SB 243: $2,500 per violation
- CCPA: $7,500 per intentional violation

---

## 1. EU AI Act Compliance

### Classification: Limited-Risk AI System

SaltBitter's AI features qualify as **limited risk** under Article 52:
- AI-generated content (icebreakers, coaching)
- Interaction with humans where AI might be perceived as human (AI practice companions)
- Does NOT qualify as High-Risk (not critical infrastructure, no biometric identification)

### Article 52: Transparency Obligations for Limited-Risk Systems

#### ✅ Requirement 1: Inform Users They're Interacting with AI

**Legal Text** (Article 52(1)):
> "Providers shall ensure that AI systems intended to interact with natural persons are designed and developed in such a way that natural persons are informed that they are interacting with an AI system."

**SaltBitter Implementation**:

| Feature | Disclosure Method | Status | Evidence Location |
|---------|-------------------|--------|-------------------|
| AI Practice Companions | 🤖 Badge on profile + "This is an AI" modal | ✅ Compliant | `01-AI-TRANSPARENCY-FLOWS.md`, Section 2 |
| AI-Generated Icebreakers | "AI-Generated" label above message + info icon | ✅ Compliant | `01-AI-TRANSPARENCY-FLOWS.md`, Section 4 |
| AI Communication Coaching | "💡 AI Coaching Feedback" header + persistent badge | ✅ Compliant | `01-AI-TRANSPARENCY-FLOWS.md`, Section 3 |
| Compatibility Matching Algorithm | Transparency page: "How matching works" | ✅ Compliant | `03-MATCHING-ALGORITHM.md`, Section 6 |

**Code Implementation Checkpoints**:
```python
# Example enforcement in codebase
class AIProfile(Profile):
    def render(self):
        # REQUIRED: AI badge must always be visible
        assert self.display_ai_badge == True, "EU AI Act Article 52 violation"
        return f"<div class='ai-profile-badge'>🤖 AI Practice Companion</div>"

# Unit test requirement
def test_ai_disclosure_always_visible():
    """Ensure AI disclosure cannot be accidentally removed"""
    ai_profile = AIProfile()
    rendered_html = ai_profile.render()
    assert "AI Practice Companion" in rendered_html
    assert "🤖" in rendered_html
```

---

#### ✅ Requirement 2: Clear, Understandable Language

**Legal Text** (Article 52(1)):
> "Information shall be provided in clear and accessible language."

**SaltBitter Implementation**:
- ✅ Plain language: "This is an AI Practice Companion" (NOT "ML-powered conversational agent")
- ✅ Localization: Translated into all supported languages
- ✅ Accessible: WCAG 2.1 AA compliance for visual/screen reader users
- ✅ Reading level: 8th-grade reading level maximum (Flesch-Kincaid score >60)

**Testing Protocol**:
```bash
# Automated readability check in CI/CD
python scripts/check_ai_disclosures.py --max-grade-level 8
```

---

#### ✅ Requirement 3: Machine-Readable Disclosure

**Legal Text** (Recital 132):
> "Machine-readable disclosure should be provided where technically feasible."

**SaltBitter Implementation**:
```json
// AI Profile API Response
{
  "user_id": "ai_companion_001",
  "type": "ai_system",
  "ai_disclosure": {
    "is_ai": true,
    "purpose": "communication_practice",
    "capabilities": ["conversation", "feedback", "coaching"],
    "limitations": ["not_real_person", "no_emotional_connection", "training_only"],
    "transparency_url": "https://saltbitter.com/ai-transparency",
    "disclosure_version": "1.0",
    "last_updated": "2025-11-17"
  }
}
```

---

### Article 50: Log-Keeping Requirements

**Legal Text**:
> "High-risk AI systems shall be designed and developed with capabilities enabling the automatic recording of events ('logs') over the lifetime of the system."

**SaltBitter Status**: ⚠️ **Partially Applicable** (we're Limited Risk, not High Risk)

**Implementation (Best Practice, Not Strictly Required)**:
```python
# Log all AI interactions for transparency and auditing
def log_ai_interaction(user_id, ai_system, action, outcome):
    log_entry = {
        "timestamp": datetime.utcnow(),
        "user_id": user_id,
        "ai_system": ai_system,  # "practice_companion", "icebreaker_generator"
        "action": action,  # "conversation", "feedback_provided"
        "outcome": outcome,
        "disclosure_shown": True,  # Track that user was informed
        "user_acknowledged": True,  # Track user consent
    }
    analytics_db.insert("ai_interaction_logs", log_entry)
    # Retain for 6 months for audit purposes
```

---

### Article 13: Transparency & User Information

**Legal Text**:
> "Providers shall provide clear and accessible information to users."

**SaltBitter Implementation**:

✅ **AI Transparency Page** (`/ai-transparency`):
- How AI is used (matching, coaching, practice companions)
- What data AI systems process
- Limitations and risks of AI
- User rights and opt-out options
- Contact for questions: ai-questions@saltbitter.com

✅ **In-App Help Center**:
- "What is an AI Practice Companion?"
- "How does the matching algorithm work?"
- "Can I opt out of AI features?"

---

## 2. California SB 243 Compliance

### Overview: Artificial Intelligence Training Data Transparency

**Effective Date**: January 1, 2026
**Applicability**: Any company using AI to interact with California residents

### Section 1770(a): Disclosure Requirements

#### ✅ Requirement 1: Disclose Use of Generative AI

**Legal Text** (Section 1770(a)(1)):
> "A covered provider shall disclose to a customer that the covered provider is using generative artificial intelligence."

**SaltBitter Implementation**:

| AI Feature | California Disclosure | Status |
|------------|----------------------|--------|
| AI Practice Companions | "Powered by generative AI" in profile modal | ✅ Compliant |
| AI Icebreakers | "AI-generated conversation starter" label | ✅ Compliant |
| Communication Coaching | "AI analysis" badge on feedback | ✅ Compliant |

**Geolocation-Based Disclosure** (California users only):
```python
def render_ai_feature(feature, user):
    disclosure = generate_disclosure(feature)

    # Enhanced disclosure for California users (SB 243 compliance)
    if user.location.state == "California":
        disclosure += "\n\n[California residents: This feature uses generative AI. "
        disclosure += "Learn more: saltbitter.com/ai-ca]"

    return disclosure
```

---

#### ✅ Requirement 2: Provide Opt-Out Mechanism

**Legal Text** (Section 1770(b)):
> "A covered provider shall provide a customer with the option to opt out of interacting with generative artificial intelligence."

**SaltBitter Implementation**:

✅ **Settings > AI Features** (`/settings/ai-preferences`):
```
┌───────────────────────────────────────────────────┐
│  California Residents: AI Opt-Out Options         │
│                                                    │
│  ☐ Opt out of ALL AI features                    │
│  ☐ Opt out of AI Practice Companions only        │
│  ☐ Opt out of AI-generated icebreakers only      │
│  ☐ Opt out of AI communication coaching only     │
│                                                    │
│  [Save Preferences]                               │
└───────────────────────────────────────────────────┘
```

**Technical Implementation**:
```python
class CaliforniaComplianceMiddleware:
    """Enforce SB 243 opt-out preferences"""

    def process_request(self, user, ai_feature):
        if user.location.state == "California":
            # Check opt-out preferences
            if user.preferences.ai_opt_out_all:
                return {
                    "allowed": False,
                    "reason": "User opted out of AI (CA SB 243)",
                    "fallback": "human_alternative"
                }

            if ai_feature in user.preferences.ai_opt_out_features:
                return {
                    "allowed": False,
                    "reason": f"User opted out of {ai_feature}",
                    "fallback": "non_ai_alternative"
                }

        return {"allowed": True}
```

---

#### ✅ Requirement 3: Transparency About Data Usage

**Legal Text** (Section 1770(c)):
> "Disclose how customer data is used to train AI systems."

**SaltBitter Implementation**:

✅ **Data Usage Transparency Page** (`/ai-data-usage`):

```markdown
# How Your Data Is Used with AI

## Data We Collect
- Attachment assessment responses
- Conversation patterns (anonymized)
- Swipe/match behavior (aggregate only)

## How AI Uses Your Data

### 1. Matching Algorithm
- Uses: Attachment scores, preferences, interests
- Training: Aggregate patterns only (individual data NOT used for training)
- Retention: Active account + 30 days

### 2. AI Practice Companions
- Uses: Conversation content during session
- Training: NOT used for training AI models
- Retention: Deleted immediately after session ends

### 3. Communication Coaching
- Uses: Message tone and content analysis
- Training: Anonymized patterns only (opt-out available)
- Retention: 90 days for your personal insights

## California Residents
✅ You can opt out of AI training: [Opt Out]
✅ Request deletion of all AI-related data: [Delete AI Data]
✅ Download your AI interaction data: [Download]
```

**Technical Implementation**:
```python
# Data minimization for AI training
class AITrainingDataPolicy:
    """Enforce SB 243 data usage transparency"""

    @staticmethod
    def can_use_for_training(data_type, user):
        # Check user's training opt-out status
        if user.location.state == "California" and user.preferences.ai_training_opt_out:
            return False

        # Define what data types can be used for training
        allowed_for_training = {
            "aggregate_swipe_patterns": True,
            "anonymized_conversation_tones": True,
            "individual_messages": False,  # NEVER use individual messages
            "attachment_scores": False,  # Sensitive psychological data
            "practice_companion_conversations": False,  # Explicitly not for training
        }

        return allowed_for_training.get(data_type, False)
```

---

## 3. GDPR Compliance (EU Data Protection)

### Applicability
SaltBitter processes personal data of EU residents → **GDPR applies**

### Article 6: Lawful Basis for Processing

| Data Processing Activity | Lawful Basis | Documentation |
|-------------------------|--------------|---------------|
| Profile creation & matching | Consent + Contract (service delivery) | Terms of Service acceptance |
| Attachment assessment | Explicit consent (special category data) | Separate consent checkbox |
| AI Practice Companion data | Legitimate interest (service improvement) | Legitimate Interest Assessment |
| Marketing communications | Consent (opt-in required) | Email preference center |
| Analytics & product improvement | Legitimate interest | LIA + Privacy Policy |

---

### Article 9: Special Category Data (Sensitive Data)

**⚠️ HIGH RISK**: Attachment assessment involves **psychological data** = Special Category under GDPR

**Legal Text** (Article 9(1)):
> "Processing of personal data revealing...health...shall be prohibited."

**Exception** (Article 9(2)(a)):
> "Processing is lawful if the data subject has given explicit consent."

**SaltBitter Implementation**:

✅ **Explicit Consent for Attachment Assessment**:
```
┌───────────────────────────────────────────────────┐
│  Attachment Assessment: Your Consent              │
│                                                    │
│  This assessment collects psychological data      │
│  about your relationship patterns.                │
│                                                    │
│  By continuing, you explicitly consent to:        │
│  ☑ Processing your psychological data            │
│  ☑ Using data for matching compatibility         │
│  ☑ Storing data securely on EU servers           │
│                                                    │
│  You can withdraw consent anytime in Settings.   │
│                                                    │
│  [ I Consent & Understand ]  [ Cancel ]          │
└───────────────────────────────────────────────────┘
```

**Code Enforcement**:
```python
def start_attachment_assessment(user):
    # CRITICAL: Explicit consent required before special category processing
    if not user.consents.attachment_assessment_explicit:
        raise GDPRViolationError(
            "Article 9: Explicit consent required for psychological data"
        )

    # Log consent for audit trail
    log_consent_event(user.id, "attachment_assessment", timestamp=datetime.utcnow())

    # Proceed with assessment
    return render_assessment_questions()
```

---

### Article 15-22: Data Subject Rights

| Right | Implementation | Response Time |
|-------|---------------|---------------|
| **Right to Access** (Art. 15) | Settings > Download My Data | Instant download |
| **Right to Rectification** (Art. 16) | Profile editing, retake assessment | Instant |
| **Right to Erasure** (Art. 17) | Settings > Delete Account | 30 days (with grace period) |
| **Right to Data Portability** (Art. 20) | JSON export of all data | Instant download |
| **Right to Object** (Art. 21) | Opt-out of AI features, marketing | Instant |
| **Automated Decision-Making** (Art. 22) | User can request human review of matches | 48 hours |

**Technical Implementation**:
```python
# GDPR Subject Access Request (SAR) handler
def generate_gdpr_export(user_id):
    """Generate complete GDPR-compliant data export"""

    export_data = {
        "personal_data": {
            "profile": get_profile_data(user_id),
            "photos": get_photo_metadata(user_id),
            "location_history": get_location_data(user_id),
        },
        "sensitive_data": {
            "attachment_assessment": get_attachment_data(user_id),
            "consent_records": get_consent_history(user_id),
        },
        "behavioral_data": {
            "matches": get_match_history(user_id),
            "conversations": get_message_metadata(user_id),  # Metadata only, not content
            "swipe_history": get_swipe_data(user_id),
        },
        "ai_interaction_data": {
            "practice_companion_sessions": get_ai_session_metadata(user_id),
            "coaching_feedback": get_coaching_history(user_id),
        },
        "algorithmic_data": {
            "compatibility_scores": get_compatibility_history(user_id),
            "match_explanations": get_match_reasoning(user_id),
        },
        "metadata": {
            "export_date": datetime.utcnow(),
            "export_version": "1.0",
            "retention_schedule": get_retention_schedule(),
        }
    }

    return export_data
```

---

### Article 25: Data Protection by Design & Default

✅ **Privacy-Preserving Architecture**:
```python
# Example: Matching algorithm uses hashed/anonymized data
class PrivacyPreservingMatcher:
    """GDPR Article 25 compliant matching"""

    def calculate_compatibility(self, user_a, user_b):
        # Use derived scores, not raw psychological data
        compatibility = {
            "attachment": self.compare_attachment_styles(
                user_a.attachment_category,  # "Secure" not raw scores
                user_b.attachment_category
            ),
            "interests": self.compare_interests(
                user_a.interest_embeddings,  # Vectorized, not raw text
                user_b.interest_embeddings
            ),
        }

        # Log only aggregate scores, not individual data
        log_match_calculation(user_a.id, user_b.id, compatibility["total"])

        return compatibility
```

---

## 4. CCPA Compliance (California Privacy Rights)

### Applicability
SaltBitter serves California residents → **CCPA applies**

### Consumer Rights Under CCPA

| Right | Implementation | Verification Required |
|-------|---------------|----------------------|
| **Right to Know** (§1798.100) | Settings > My Data | Email verification |
| **Right to Delete** (§1798.105) | Settings > Delete Account | Email + password confirmation |
| **Right to Opt-Out of Sale** (§1798.120) | ✅ We don't sell data | N/A |
| **Right to Non-Discrimination** (§1798.125) | ✅ No service degradation for exercising rights | N/A |

**"Do Not Sell My Personal Information" Notice**:
```
California residents: We do NOT sell your personal information.
We do not share your data with third parties for monetary consideration.

Your data is used only for:
- Providing the SaltBitter service
- Improving matching algorithms
- Safety and security

Learn more: [CCPA Privacy Policy]
```

---

## 5. Dating-Specific Regulations

### FTC Endorsement Guidelines (AI-Generated Content)

**Applicability**: AI-generated icebreakers could be considered "endorsements" if not disclosed

✅ **Compliance**:
- All AI-generated content clearly labeled
- No deceptive "human-written" misrepresentation
- Transparent about AI limitations

---

### State Catfishing/Deception Laws

Multiple states have laws against online impersonation and deceptive dating practices:
- **Texas** (Penal Code §33.07): Online impersonation
- **New York** (SB S4253A): Dating app safety
- **California** (Penal Code §528.5): False personation

✅ **SaltBitter Compliance**:
- AI profiles explicitly labeled (no deception)
- Photo verification system
- Reporting tools for impersonation
- No AI profiles that mimic real humans

---

## 6. Compliance Monitoring & Audit Framework

### Quarterly Compliance Audits

**Q1 2026 Audit Checklist**:

#### AI Transparency (EU AI Act + CA SB 243)
- [ ] All AI profiles display badge (automated test)
- [ ] All AI-generated content labeled (code review)
- [ ] Opt-out mechanisms functional (manual test)
- [ ] Disclosure language <8th grade reading level (automated check)
- [ ] California-specific disclosures shown to CA users (geolocation test)

#### GDPR (Data Protection)
- [ ] Consent logs intact and auditable (database check)
- [ ] Data retention schedules enforced (automated cleanup scripts)
- [ ] Subject access requests processed within 30 days (ticket review)
- [ ] Special category data has explicit consent (database integrity check)
- [ ] Data minimization principles applied (privacy review)

#### CCPA (California Privacy Rights)
- [ ] "Do Not Sell" notice on homepage (visual check)
- [ ] Data export function working (manual test)
- [ ] Account deletion functional (manual test)
- [ ] No service discrimination for rights exercise (A/B test check)

#### Security & Safety
- [ ] Encryption at rest and in transit (security scan)
- [ ] Access controls on sensitive data (IAM audit)
- [ ] Incident response plan updated (annual review)
- [ ] Vulnerability scans completed (quarterly penetration test)

---

### Automated Compliance Testing

```python
# tests/compliance/test_eu_ai_act.py
def test_ai_disclosure_always_visible():
    """EU AI Act Article 52: AI disclosure must be visible"""
    ai_profile = AIProfile.objects.first()
    rendered_html = ai_profile.render()

    assert "AI Practice Companion" in rendered_html
    assert "🤖" in rendered_html or "AI" in rendered_html

def test_ai_disclosure_cannot_be_hidden():
    """Ensure no code path allows hiding AI disclosure"""
    ai_profile = AIProfile.objects.first()
    ai_profile.hide_ai_badge = True  # Try to hide it
    ai_profile.save()

    # Render should still show badge (model validation prevents hiding)
    rendered_html = ai_profile.render()
    assert "AI Practice Companion" in rendered_html

# tests/compliance/test_california_sb243.py
def test_california_users_see_ai_opt_out():
    """SB 243: California users must have opt-out option"""
    ca_user = create_user(state="California")
    settings_page = render_settings(ca_user)

    assert "Opt out of AI" in settings_page
    assert "California residents" in settings_page

def test_opt_out_prevents_ai_features():
    """SB 243: Opt-out must be honored"""
    ca_user = create_user(state="California")
    ca_user.preferences.ai_opt_out_all = True
    ca_user.save()

    # Try to show AI feature
    can_show_ai = check_ai_feature_permission(ca_user, "practice_companion")
    assert can_show_ai == False

# tests/compliance/test_gdpr.py
def test_special_category_consent_required():
    """GDPR Article 9: Explicit consent for psychological data"""
    user = create_user()

    # Try to start assessment without consent
    with pytest.raises(GDPRViolationError):
        start_attachment_assessment(user)

    # Grant consent
    user.consents.attachment_assessment_explicit = True
    user.save()

    # Should now work
    assessment = start_attachment_assessment(user)
    assert assessment is not None

def test_gdpr_export_includes_all_data():
    """GDPR Article 15: Subject access request completeness"""
    user = create_user_with_full_data()
    export = generate_gdpr_export(user.id)

    required_sections = [
        "personal_data",
        "sensitive_data",
        "behavioral_data",
        "ai_interaction_data",
        "algorithmic_data"
    ]

    for section in required_sections:
        assert section in export
        assert export[section] is not None
```

---

## 7. Data Retention & Deletion Schedule

### Retention Policy (GDPR Article 5(1)(e): Storage Limitation)

| Data Type | Retention Period | Reason | Auto-Delete |
|-----------|-----------------|--------|-------------|
| **Active User Profile** | Account lifetime + 30 days | Service delivery | ✅ Yes |
| **Attachment Assessment** | Account lifetime + 30 days | Matching algorithm | ✅ Yes |
| **AI Practice Sessions** | Session duration only | Privacy by design | ✅ Immediate |
| **Message Metadata** | 2 years | Safety investigations | ✅ Yes |
| **Match History** | Account lifetime + 1 year | Analytics | ✅ Yes |
| **Consent Logs** | 7 years | Legal requirement (proof of consent) | ✅ Yes |
| **Security Logs** | 2 years | Incident response | ✅ Yes |
| **Aggregate Analytics** | Indefinite | De-identified, no privacy risk | N/A |

**Automated Deletion Script** (runs daily):
```python
# scripts/data_retention_cleanup.py
def enforce_data_retention_policy():
    """GDPR Article 5(1)(e) compliance: Automatic data deletion"""

    today = datetime.utcnow()

    # Delete AI practice session data immediately after session ends
    AISession.objects.filter(
        status="completed",
        ended_at__lt=today - timedelta(minutes=5)
    ).delete()

    # Delete deleted account data after 30-day grace period
    User.objects.filter(
        status="deleted",
        deleted_at__lt=today - timedelta(days=30)
    ).delete_permanently()

    # Delete message metadata after 2 years
    MessageMetadata.objects.filter(
        created_at__lt=today - timedelta(days=730)
    ).delete()

    # Anonymize match history after account deletion + 1 year
    Match.objects.filter(
        user__status="deleted",
        user__deleted_at__lt=today - timedelta(days=365)
    ).anonymize()  # Keep aggregate stats, remove identifiers

    logging.info("Data retention policy enforced successfully")
```

---

## 8. Incident Response & Breach Notification

### GDPR Article 33: Breach Notification (72 hours)

**Incident Response Plan**:

1. **Detection** (Automated monitoring)
   - Real-time alerts for unauthorized access
   - Daily security scans
   - User reports via security@saltbitter.com

2. **Assessment** (Within 4 hours)
   - Determine scope: What data was accessed?
   - Classify severity: High (special category data), Medium (personal data), Low (public data)
   - Identify affected users

3. **Containment** (Within 8 hours)
   - Patch vulnerability
   - Revoke compromised credentials
   - Lock affected accounts

4. **Notification** (Within 72 hours)
   - **To Supervisory Authority** (GDPR): If high risk to users
   - **To Affected Users** (GDPR): If high risk, direct notification
   - **To California AG** (CCPA): If >500 CA residents affected

**Breach Notification Template** (GDPR Compliant):
```
Subject: Important Security Notice - SaltBitter Data Incident

Dear [User],

We are writing to inform you of a data security incident that may have affected your account.

WHAT HAPPENED:
On [date], we discovered that [description of incident].

WHAT DATA WAS AFFECTED:
[Specific data types: profile information, messages, etc.]

WHAT WE'RE DOING:
- [Immediate actions taken]
- [Long-term improvements]

WHAT YOU SHOULD DO:
- Change your password immediately
- Enable two-factor authentication
- Monitor your account for suspicious activity

YOUR RIGHTS:
- You can request more information: privacy@saltbitter.com
- You can file a complaint with your data protection authority
- You can request account deletion

We sincerely apologize for this incident and are committed to protecting your data.

Sincerely,
SaltBitter Security Team

---
This notification is required under GDPR Article 34 / CCPA § 1798.150
```

---

## 9. Cross-Border Data Transfers

### GDPR Chapter V: International Transfers

**Challenge**: SaltBitter may use US-based cloud providers (AWS, Google Cloud) for EU user data

**Solutions**:

✅ **Option 1: EU-Only Data Residency** (Recommended)
- Host all EU user data on EU servers (AWS eu-west-1, Google europe-west1)
- No data transfers outside EU
- Simplest compliance path

✅ **Option 2: Standard Contractual Clauses (SCCs)**
- If using US providers, sign EU-approved SCCs
- Document transfer impact assessment (TIA)
- Ensure US provider has adequate safeguards

⚠️ **Invalidated**: Privacy Shield was struck down (Schrems II ruling)

**SaltBitter Implementation**:
```python
# Data residency enforcement
class DataResidencyRouter:
    """Ensure EU data stays in EU (GDPR Chapter V compliance)"""

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'users':
            user = hints.get('instance')
            if user and user.region == 'EU':
                return 'eu_database'  # AWS RDS in eu-west-1
        return 'default'

    def db_for_write(self, model, **hints):
        # Same logic: EU users → EU database
        if model._meta.app_label == 'users':
            user = hints.get('instance')
            if user and user.region == 'EU':
                return 'eu_database'
        return 'default'
```

---

## 10. Compliance Roles & Responsibilities

### Data Protection Officer (DPO) - GDPR Article 37

**Requirement**: Companies processing special category data on a large scale must appoint a DPO

**SaltBitter**: ⚠️ **DPO Required** (psychological data = special category, >10,000 users = large scale)

**Responsibilities**:
- Monitor GDPR compliance
- Advise on Data Protection Impact Assessments (DPIAs)
- Act as contact point for data protection authorities
- Handle data subject requests

**Contact**: dpo@saltbitter.com

---

### Compliance Team Structure

```
CEO / Legal Counsel
    │
    ├─ Data Protection Officer (DPO)
    │   ├─ Privacy Engineer (technical implementation)
    │   ├─ Compliance Analyst (audits, documentation)
    │   └─ Data Subject Rights Coordinator (user requests)
    │
    ├─ Chief Information Security Officer (CISO)
    │   ├─ Security Engineers (infrastructure, encryption)
    │   └─ Incident Response Team (breaches, forensics)
    │
    └─ Product & Engineering
        ├─ Privacy-by-Design Lead (feature reviews)
        └─ QA Compliance Tester (automated compliance tests)
```

---

## 11. Compliance Roadmap

### Pre-Launch (Before Public Release)
- [x] Conduct Data Protection Impact Assessment (DPIA)
- [x] Draft Terms of Service + Privacy Policy
- [x] Implement AI disclosure badges
- [x] Build GDPR export functionality
- [ ] Legal review by EU privacy lawyer
- [ ] Penetration testing by third-party security firm
- [ ] Appoint Data Protection Officer (DPO)

### Month 1-3 (Soft Launch)
- [ ] Monitor compliance in production
- [ ] Test incident response plan (tabletop exercise)
- [ ] User feedback on privacy controls
- [ ] First quarterly compliance audit

### Month 4-6 (Scaling)
- [ ] Annual penetration test
- [ ] Review data retention schedules
- [ ] Update privacy policy based on new features
- [ ] Train customer support on GDPR/CCPA rights

### Ongoing (Quarterly)
- [ ] Compliance audits (automated + manual)
- [ ] Review consent logs for integrity
- [ ] Security vulnerability scans
- [ ] Update compliance documentation

---

## 12. Compliance Resources & Contacts

### Regulatory Authorities

**EU (GDPR)**:
- Lead Supervisory Authority (if main office in Ireland): Data Protection Commission (DPC)
- Contact: [https://www.dataprotection.ie](https://www.dataprotection.ie)

**California (CCPA / SB 243)**:
- California Privacy Protection Agency (CPPA)
- Contact: [https://cppa.ca.gov](https://cppa.ca.gov)

### Internal Contacts

- **Privacy Questions**: privacy@saltbitter.com
- **Data Protection Officer**: dpo@saltbitter.com
- **Security Incidents**: security@saltbitter.com
- **Data Subject Requests**: rights@saltbitter.com

### External Legal Counsel

- **EU Privacy Lawyer**: [TBD - hire before EU launch]
- **US Privacy Lawyer**: [TBD]

---

## Compliance Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **CEO** | [Name] | __________ | ___/___/___ |
| **Data Protection Officer** | [Name] | __________ | ___/___/___ |
| **Chief Legal Officer** | [Name] | __________ | ___/___/___ |
| **Chief Product Officer** | [Name] | __________ | ___/___/___ |

**Next Review Date**: Q1 2026 (before EU AI Act full enforcement)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-17
**Compliance Status**: ✅ Ready for Legal Review
**Audit Trail**: Stored in compliance-docs/ repository
