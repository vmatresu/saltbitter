# Security Best Practices & Code Review Checklist

**Security Guidelines for SaltBitter Platform**

## Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Minimum necessary permissions
3. **Fail Securely**: Errors should not expose sensitive information
4. **Security by Design**: Security considerations from the start
5. **Audit Everything**: Comprehensive logging of security events

## Authentication & Authorization

### ✅ DO
- Use bcrypt for password hashing (12+ rounds)
- Implement rate limiting on auth endpoints (10 req/min per IP)
- Use JWT with short expiration (15 minutes for access tokens)
- Store refresh tokens hashed in database (SHA-256)
- Implement account lockout after 5 failed login attempts
- Require email verification before account activation

### ❌ DON'T
- Store passwords in plain text or with weak hashing (MD5, SHA1)
- Use predictable session IDs
- Expose user IDs in URLs (use UUIDs, not sequential integers)
- Allow unlimited login attempts
- Share JWT secret keys across environments

### Code Review Checklist
```python
# ✅ Good: Password properly hashed
import bcrypt
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))

# ❌ Bad: Weak hashing
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()  # NO!
```

## Input Validation

### ✅ DO
- Validate all user inputs with Pydantic schemas
- Sanitize HTML inputs to prevent XSS
- Use parameterized queries (SQLAlchemy ORM)
- Validate file uploads (type, size, content)
- Implement allow-lists for user-generated content

### ❌ DON'T
- Trust user input without validation
- Construct SQL queries with string concatenation
- Allow arbitrary file uploads without scanning
- Use `eval()` or `exec()` on user input
- Expose internal error details to users

### Code Review Checklist
```python
# ✅ Good: Parameterized query (SQLAlchemy)
user = db.query(User).filter(User.email == email).first()

# ❌ Bad: SQL injection risk
query = f"SELECT * FROM users WHERE email = '{email}'"  # NO!
db.execute(query)

# ✅ Good: Input validation
from pydantic import BaseModel, EmailStr, constr

class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=100)

# ❌ Bad: No validation
def create_user(email: str, password: str):  # No validation!
    pass
```

## API Security

### ✅ DO
- Implement rate limiting (100 req/min per user)
- Use CORS with explicit origin whitelist
- Require authentication for sensitive endpoints
- Return 401 for auth failures, not 403 (don't reveal user existence)
- Log all authentication and authorization failures

### ❌ DON'T
- Allow CORS from all origins (`*`)
- Expose detailed error messages in production
- Use GET requests for state-changing operations
- Return different error messages for "user not found" vs "wrong password"

### CORS Configuration
```python
# ✅ Good: Explicit origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://saltbitter.com", "https://app.saltbitter.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"]
)

# ❌ Bad: Allow all
allow_origins=["*"]  # NO!
```

## Data Protection

### ✅ DO
- Encrypt data in transit (TLS 1.3)
- Encrypt data at rest (AES-256 for RDS, S3)
- Use AWS Secrets Manager for API keys and credentials
- Implement data retention policies (delete old data)
- Anonymize or pseudonymize PII in logs

### ❌ DON'T
- Log passwords, tokens, or credit card numbers
- Store API keys in code or version control
- Use HTTP for any communication
- Keep user data indefinitely without consent
- Share database credentials across environments

### Logging Security
```python
# ✅ Good: Sanitized logging
logger.info(f"User logged in: user_id={user.id}")

# ❌ Bad: Logging sensitive data
logger.info(f"Login: {email}, password={password}")  # NO!
logger.debug(f"JWT token: {access_token}")  # NO!
```

## File Upload Security

### ✅ DO
- Validate file extensions (allow-list: .jpg, .png, .pdf)
- Validate MIME types
- Limit file size (5MB for photos)
- Scan uploads with antivirus (AWS Rekognition for images)
- Store files outside web root (S3, not public directory)
- Generate random filenames (don't trust user-provided names)

### ❌ DON'T
- Allow executable file uploads (.exe, .sh, .py)
- Trust user-provided file extensions
- Store uploads in publicly accessible directories
- Use user-provided filenames without sanitization

### File Upload Implementation
```python
# ✅ Good: Secure file upload
import uuid
from pathlib import Path

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def upload_photo(file: UploadFile):
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")

    # Validate size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    if size > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")

    # Generate secure filename
    filename = f"{uuid.uuid4()}{ext}"

    # Upload to S3 (not public web directory)
    s3_client.upload_fileobj(file.file, BUCKET, filename)

    return f"https://cdn.saltbitter.com/photos/{filename}"
```

## Third-Party Dependencies

### ✅ DO
- Regularly update dependencies (weekly Dependabot PRs)
- Use virtual environments (venv, pipenv)
- Pin dependency versions in requirements.txt
- Run security scans (Bandit for Python, npm audit for JS)
- Review Dependabot security alerts immediately

### ❌ DON'T
- Use outdated or unmaintained packages
- Install packages without checking provenance
- Ignore Dependabot security alerts
- Use `pip install` without version pinning

### Dependency Management
```bash
# ✅ Good: Pinned versions
fastapi==0.104.1
pydantic==2.5.0

# ❌ Bad: Unpinned
fastapi  # Could install any version!

# Run security scans
bandit -r backend/
npm audit --production
```

## Secrets Management

### ✅ DO
- Use AWS Secrets Manager or SSM Parameter Store
- Rotate secrets regularly (90 days)
- Use different secrets per environment
- Audit secret access (CloudTrail)
- Revoke secrets immediately if compromised

### ❌ DON'T
- Commit secrets to Git (use .gitignore)
- Share secrets via Slack, email, or unencrypted channels
- Use default or weak secrets (e.g., "admin"/"password")
- Hard-code API keys in source code

### Secrets in Code
```python
# ✅ Good: Load from environment/Secrets Manager
import os
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
DATABASE_URL = get_secret("saltbitter/prod/database-url")

# ❌ Bad: Hard-coded
STRIPE_API_KEY = "sk_live_abc123..."  # NO!
```

## Code Review Security Checklist

### For Every Pull Request
- [ ] No secrets or API keys in code
- [ ] Input validation on all endpoints
- [ ] Authentication required for sensitive operations
- [ ] Authorization checks for user-specific data
- [ ] SQL queries use ORM or parameterized queries
- [ ] File uploads validated (type, size)
- [ ] Error messages don't expose internal details
- [ ] Logging doesn't include PII or secrets
- [ ] Rate limiting on public endpoints
- [ ] HTTPS enforced for all connections
- [ ] Dependencies up to date (no critical vulnerabilities)
- [ ] Security scans passing (Bandit, npm audit)

## Incident Response

### If Security Issue Discovered
1. **Assess severity** (critical/high/medium/low)
2. **Contain the issue** (deploy fix or disable feature)
3. **Notify stakeholders** (CTO, security team, legal if data breach)
4. **Document in incident log**
5. **Post-mortem within 48 hours**
6. **Update security practices** to prevent recurrence

### Security Contacts
- **Security Team**: security@saltbitter.com
- **On-Call Engineer**: PagerDuty
- **Legal**: legal@saltbitter.com (for data breaches)

## Compliance

### GDPR Requirements
- Obtain explicit consent for data processing
- Provide data export (48-hour SLA)
- Provide data deletion (30-day grace period)
- Notify users of breaches within 72 hours
- Appoint Data Protection Officer (DPO)

### OWASP Top 10 (2021)
1. ✅ Broken Access Control → Use FastAPI dependencies for auth
2. ✅ Cryptographic Failures → TLS 1.3, AES-256, bcrypt
3. ✅ Injection → SQLAlchemy ORM, Pydantic validation
4. ✅ Insecure Design → Security reviews in architecture phase
5. ✅ Security Misconfiguration → IaC with Terraform, reviewed configs
6. ✅ Vulnerable Components → Dependabot, regular updates
7. ✅ Identification & Auth Failures → JWT, rate limiting, bcrypt
8. ✅ Software & Data Integrity → Signed releases, checksums
9. ✅ Security Logging Failures → Comprehensive DataDog logging
10. ✅ Server-Side Request Forgery → No user-controlled URLs

## Security Tools

### Development
- **Bandit**: Python security linter
- **ruff**: Python linter (includes security rules)
- **mypy**: Type checker (prevents type-related bugs)
- **npm audit**: JavaScript dependency scanner

### CI/CD
- **Dependabot**: Automated dependency updates
- **GitHub Code Scanning**: SAST (static analysis)
- **Trivy**: Container image scanning

### Production
- **AWS WAF**: Web application firewall
- **AWS Shield**: DDoS protection
- **DataDog Security Monitoring**: Runtime security

---

**Last Updated**: 2025-11-18
**Maintained By**: Security Team & Engineering
