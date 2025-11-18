# Contributing to SaltBitter

Thank you for your interest in contributing to SaltBitter! This document provides guidelines for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Assume good intentions
- No harassment, discrimination, or inappropriate behavior

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Local Setup
```bash
# Clone repository
git clone https://github.com/vmatresu/saltbitter.git
cd saltbitter

# Backend setup
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend/web
npm install

# Start services
cd ../..
docker-compose up -d

# Run tests
pytest backend/tests/
cd frontend/web && npm test
```

## Development Workflow

### 1. Create a Branch
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

**Branch Naming**:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Adding/improving tests

### 2. Make Changes
- Write code following our [coding standards](#coding-standards)
- Add tests for new functionality
- Update documentation if needed
- Run linters and tests locally

### 3. Commit Changes
```bash
git add .
git commit -m "feat: Add user profile photo upload"
```

**Commit Message Format**:
```
<type>: <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### 4. Push and Create PR
```bash
git push origin feature/your-feature-name
gh pr create --base develop --title "feat: Add user profile photo upload"
```

## Pull Request Process

### PR Template
```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests passing locally
- [ ] Coverage ≥85%
```

### Review Process
1. Create PR targeting `develop` branch
2. Automated checks run (tests, linting, security scans)
3. Request review from 1-2 team members
4. Address feedback and update PR
5. Maintainer approves and merges

### Merge Requirements
- ✅ All CI checks passing
- ✅ At least 1 approval from maintainer
- ✅ No merge conflicts
- ✅ Branch up to date with develop

## Coding Standards

### Python (Backend)

**Style Guide**: PEP 8 via Black formatter

```python
# Use type hints
def create_user(email: str, password: str) -> User:
    """Create a new user account.
    
    Args:
        email: User's email address
        password: Plain text password (will be hashed)
        
    Returns:
        Created user object
        
    Raises:
        ValueError: If email already exists
    """
    pass

# Use descriptive variable names
user_email = "test@example.com"  # Good
ue = "test@example.com"  # Bad

# Use Pydantic for validation
class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8)

# Use dependency injection
async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> User:
    pass
```

**Tools**:
```bash
black backend/           # Auto-format
ruff check backend/      # Lint
mypy backend/ --strict   # Type check
bandit -r backend/       # Security scan
```

### TypeScript (Frontend)

**Style Guide**: Airbnb style via ESLint

```typescript
// Use TypeScript interfaces
interface User {
  id: string;
  email: string;
  name: string;
}

// Use React functional components with hooks
const ProfileCard: React.FC<{ user: User }> = ({ user }) => {
  const [loading, setLoading] = useState(false);
  
  return (
    <div className="profile-card">
      <h2>{user.name}</h2>
      <p>{user.email}</p>
    </div>
  );
};

// Use async/await, not .then()
const fetchUser = async (id: string): Promise<User> => {
  const response = await apiClient.get(`/users/${id}`);
  return response.data;
};
```

**Tools**:
```bash
npm run lint          # ESLint
npm run format        # Prettier
tsc --noEmit          # Type check
```

## Testing Requirements

### Backend Tests

**Coverage Requirement**: ≥85%

```python
# Unit test example
def test_create_user():
    user = create_user("test@example.com", "password123")
    assert user.email == "test@example.com"
    assert user.password_hash != "password123"  # Hashed

# Integration test example
async def test_login_endpoint(client: TestClient):
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
```

**Run tests**:
```bash
pytest backend/tests/ -v
pytest --cov=backend --cov-report=html
```

### Frontend Tests

**Coverage Requirement**: ≥70%

```typescript
// Component test
describe('ProfileCard', () => {
  it('renders user name and email', () => {
    const user = { id: '1', name: 'Alex', email: 'alex@example.com' };
    render(<ProfileCard user={user} />);
    expect(screen.getByText('Alex')).toBeInTheDocument();
    expect(screen.getByText('alex@example.com')).toBeInTheDocument();
  });
});
```

**Run tests**:
```bash
npm test
npm test -- --coverage
```

## Documentation

### Code Documentation

**Python**: Google-style docstrings
```python
def calculate_compatibility(user_a: User, user_b: User) -> float:
    """Calculate compatibility score between two users.
    
    The score is calculated using:
    - Attachment style (40%)
    - Shared interests (25%)
    - Values alignment (20%)
    - Demographics (15%)
    
    Args:
        user_a: First user
        user_b: Second user
        
    Returns:
        Compatibility score between 0.0 and 1.0
        
    Example:
        >>> user_a = User(id='1', attachment_style='secure')
        >>> user_b = User(id='2', attachment_style='secure')
        >>> calculate_compatibility(user_a, user_b)
        0.87
    """
    pass
```

**TypeScript**: JSDoc
```typescript
/**
 * Fetch user profile from API
 * @param userId - UUID of user to fetch
 * @returns User profile object
 * @throws {ApiError} If user not found or network error
 */
async function fetchUserProfile(userId: string): Promise<UserProfile> {
  // ...
}
```

### README and Docs

- Update `README.md` for user-facing changes
- Update API docs if endpoints change
- Add/update ADRs for architectural decisions
- Update runbooks for operational changes

## Security

- Never commit secrets, API keys, or passwords
- Run `bandit` before submitting PR
- Follow [Security Best Practices](./docs/SECURITY.md)
- Report security issues to security@saltbitter.com (not public issues)

## Questions?

- **General**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Security**: Email security@saltbitter.com
- **Urgent**: Slack #engineering (for team members)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to SaltBitter! 🎉
