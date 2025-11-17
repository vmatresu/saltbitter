"""
Comprehensive tests for authentication service.

Tests cover:
- Password hashing and verification
- JWT token creation and validation
- User registration
- User login
- Token refresh
- Logout
- Password reset
- Email verification
- Rate limiting
"""

import os
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import Base, RefreshToken, User
from backend.services.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_email_verification_token,
    generate_password_reset_token,
    hash_password,
    hash_token_for_storage,
    verify_email_verification_token,
    verify_password,
    verify_password_reset_token,
    verify_token_type,
)


# Test database configuration
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/saltbitter_test")


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPassword123"),
        verified=True,
        subscription_tier="free",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_client(db_session: Session):
    """Create a test client with database session override."""
    from backend.main import app
    from backend.services.auth.routes import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ===== Security Utilities Tests =====


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_password_success(self):
        """Test password verification with correct password."""
        password = "TestPassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_password_hash_is_unique(self):
        """Test that same password produces different hashes (salt is random)."""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Tests for JWT token creation and validation."""

    def test_create_access_token(self):
        """Test access token creation."""
        user_id = str(uuid4())
        token = create_access_token(data={"sub": user_id})

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = decode_token(token)
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = str(uuid4())
        token = create_refresh_token(data={"sub": user_id})

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = decode_token(token)
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_verify_token_type_access(self):
        """Test token type verification for access token."""
        user_id = str(uuid4())
        token = create_access_token(data={"sub": user_id})

        assert verify_token_type(token, "access") is True
        assert verify_token_type(token, "refresh") is False

    def test_verify_token_type_refresh(self):
        """Test token type verification for refresh token."""
        user_id = str(uuid4())
        token = create_refresh_token(data={"sub": user_id})

        assert verify_token_type(token, "refresh") is True
        assert verify_token_type(token, "access") is False

    def test_token_expiration(self):
        """Test that tokens expire correctly."""
        user_id = str(uuid4())
        # Create token that expires immediately
        expired_token = create_access_token(
            data={"sub": user_id}, expires_delta=timedelta(seconds=-1)
        )

        # Decoding should raise an error
        with pytest.raises(Exception):
            decode_token(expired_token)

    def test_generate_password_reset_token(self):
        """Test password reset token generation."""
        user_id = uuid4()
        token = generate_password_reset_token(user_id)

        assert isinstance(token, str)

        # Verify token
        verified_user_id = verify_password_reset_token(token)
        assert verified_user_id == user_id

    def test_generate_email_verification_token(self):
        """Test email verification token generation."""
        user_id = uuid4()
        token = generate_email_verification_token(user_id)

        assert isinstance(token, str)

        # Verify token
        verified_user_id = verify_email_verification_token(token)
        assert verified_user_id == user_id

    def test_hash_token_for_storage(self):
        """Test token hashing for storage."""
        token = "sample_token_123"
        hashed = hash_token_for_storage(token)

        assert hashed != token
        assert len(hashed) == 64  # SHA-256 produces 64-char hex string
        # Same token should produce same hash
        assert hash_token_for_storage(token) == hashed


# ===== Registration Tests =====


class TestUserRegistration:
    """Tests for user registration endpoint."""

    def test_register_success(self, test_client: TestClient):
        """Test successful user registration."""
        response = test_client.post(
            "/api/auth/register",
            json={"email": "newuser@example.com", "password": "SecurePass123"},
        )

        assert response.status_code == 201
        data = response.json()

        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["verified"] is False
        assert data["tokens"]["token_type"] == "bearer"
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

    def test_register_duplicate_email(self, test_client: TestClient, test_user: User):
        """Test registration with duplicate email."""
        response = test_client.post(
            "/api/auth/register",
            json={"email": test_user.email, "password": "SecurePass123"},
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_weak_password(self, test_client: TestClient):
        """Test registration with weak password."""
        # No uppercase
        response = test_client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "weakpass123"},
        )
        assert response.status_code == 422

        # No lowercase
        response = test_client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "WEAKPASS123"},
        )
        assert response.status_code == 422

        # No digit
        response = test_client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "WeakPassword"},
        )
        assert response.status_code == 422

    def test_register_invalid_email(self, test_client: TestClient):
        """Test registration with invalid email."""
        response = test_client.post(
            "/api/auth/register",
            json={"email": "not-an-email", "password": "SecurePass123"},
        )

        assert response.status_code == 422


# ===== Login Tests =====


class TestUserLogin:
    """Tests for user login endpoint."""

    def test_login_success(self, test_client: TestClient, test_user: User):
        """Test successful login."""
        response = test_client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == test_user.email
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

    def test_login_wrong_password(self, test_client: TestClient, test_user: User):
        """Test login with wrong password."""
        response = test_client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "WrongPassword123"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, test_client: TestClient):
        """Test login with non-existent user."""
        response = test_client.post(
            "/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "AnyPassword123"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()


# ===== Token Refresh Tests =====


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    def test_refresh_token_success(self, test_client: TestClient, test_user: User, db_session: Session):
        """Test successful token refresh."""
        # Create refresh token
        refresh_token = create_refresh_token(data={"sub": str(test_user.id)})
        token_hash = hash_token_for_storage(refresh_token)

        # Store in database
        refresh_token_record = RefreshToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=7),
            revoked=False,
        )
        db_session.add(refresh_token_record)
        db_session.commit()

        # Refresh token
        response = test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, test_client: TestClient):
        """Test refresh with invalid token."""
        response = test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == 401

    def test_refresh_token_revoked(self, test_client: TestClient, test_user: User, db_session: Session):
        """Test refresh with revoked token."""
        # Create and revoke refresh token
        refresh_token = create_refresh_token(data={"sub": str(test_user.id)})
        token_hash = hash_token_for_storage(refresh_token)

        refresh_token_record = RefreshToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=7),
            revoked=True,  # Already revoked
        )
        db_session.add(refresh_token_record)
        db_session.commit()

        # Try to refresh
        response = test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 401


# ===== Logout Tests =====


class TestLogout:
    """Tests for logout endpoint."""

    def test_logout_success(self, test_client: TestClient, test_user: User, db_session: Session):
        """Test successful logout."""
        # Create tokens
        access_token = create_access_token(data={"sub": str(test_user.id)})
        refresh_token = create_refresh_token(data={"sub": str(test_user.id)})
        token_hash = hash_token_for_storage(refresh_token)

        # Store refresh token
        refresh_token_record = RefreshToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=7),
            revoked=False,
        )
        db_session.add(refresh_token_record)
        db_session.commit()

        # Logout
        response = test_client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

        # Verify token is revoked
        db_session.refresh(refresh_token_record)
        assert refresh_token_record.revoked is True


# ===== Password Reset Tests =====


class TestPasswordReset:
    """Tests for password reset endpoints."""

    def test_request_password_reset(self, test_client: TestClient, test_user: User):
        """Test password reset request."""
        response = test_client.post(
            "/api/auth/reset-password",
            json={"email": test_user.email},
        )

        assert response.status_code == 200
        assert "email" in response.json()["message"].lower()

    def test_confirm_password_reset(self, test_client: TestClient, test_user: User, db_session: Session):
        """Test password reset confirmation."""
        # Generate reset token
        reset_token = generate_password_reset_token(test_user.id)

        # Reset password
        response = test_client.post(
            "/api/auth/reset-password/confirm",
            json={"token": reset_token, "new_password": "NewSecurePass123"},
        )

        assert response.status_code == 200
        assert "reset successfully" in response.json()["message"].lower()

        # Verify new password works
        db_session.refresh(test_user)
        assert verify_password("NewSecurePass123", test_user.password_hash) is True


# ===== Email Verification Tests =====


class TestEmailVerification:
    """Tests for email verification endpoint."""

    def test_verify_email_success(self, test_client: TestClient, db_session: Session):
        """Test successful email verification."""
        # Create unverified user
        user = User(
            email="unverified@example.com",
            password_hash=hash_password("TestPassword123"),
            verified=False,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Generate verification token
        verification_token = generate_email_verification_token(user.id)

        # Verify email
        response = test_client.post(
            "/api/auth/verify-email",
            json={"token": verification_token},
        )

        assert response.status_code == 200
        assert "verified successfully" in response.json()["message"].lower()

        # Verify user is now verified
        db_session.refresh(user)
        assert user.verified is True


# ===== Integration Tests =====


class TestAuthenticationFlows:
    """Integration tests for complete authentication flows."""

    def test_complete_registration_and_login_flow(self, test_client: TestClient):
        """Test complete flow: register -> login."""
        # Register
        register_response = test_client.post(
            "/api/auth/register",
            json={"email": "flowtest@example.com", "password": "FlowTest123"},
        )
        assert register_response.status_code == 201

        # Login
        login_response = test_client.post(
            "/api/auth/login",
            json={"email": "flowtest@example.com", "password": "FlowTest123"},
        )
        assert login_response.status_code == 200

    def test_complete_token_refresh_flow(self, test_client: TestClient, test_user: User, db_session: Session):
        """Test complete flow: login -> refresh -> logout."""
        # Login
        login_response = test_client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123"},
        )
        assert login_response.status_code == 200
        tokens = login_response.json()["tokens"]

        # Refresh
        refresh_response = test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()

        # Logout with new refresh token
        logout_response = test_client.post(
            "/api/auth/logout",
            json={"refresh_token": new_tokens["refresh_token"]},
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
        )
        assert logout_response.status_code == 200
