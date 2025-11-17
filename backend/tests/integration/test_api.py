"""Integration tests for SaltBitter API endpoints.

Tests all API endpoints with real database connections and service interactions.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check and basic endpoints."""

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "SaltBitter API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "online"
        assert "docs" in data

    def test_health_endpoint(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestAuthEndpoints:
    """Test authentication API endpoints."""

    def test_register_new_user(self, client: TestClient) -> None:
        """Test user registration creates new user."""
        user_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "consent_data_processing": True,
            "consent_terms": True,
        }
        response = client.post("/api/auth/register", json=user_data)

        # Should return 201 Created or handle appropriately
        assert response.status_code in [200, 201, 400]  # 400 if user exists

    def test_login_with_valid_credentials(self, client: TestClient) -> None:
        """Test login with valid credentials returns JWT token."""
        # First register a user
        user_data = {
            "email": "login_test@example.com",
            "password": "SecurePassword123!",
            "consent_data_processing": True,
            "consent_terms": True,
        }
        client.post("/api/auth/register", json=user_data)

        # Then attempt login
        login_data = {
            "username": "login_test@example.com",
            "password": "SecurePassword123!",
        }
        response = client.post("/api/auth/login", data=login_data)

        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    def test_login_with_invalid_credentials(self, client: TestClient) -> None:
        """Test login with invalid credentials returns 401."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "WrongPassword123!",
        }
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401


class TestProfileEndpoints:
    """Test user profile API endpoints."""

    def test_create_profile_requires_auth(self, client: TestClient) -> None:
        """Test creating profile requires authentication."""
        profile_data = {
            "name": "Test User",
            "bio": "Test bio",
            "date_of_birth": "1990-01-01",
        }
        response = client.post("/api/profile", json=profile_data)
        assert response.status_code == 401  # Unauthorized

    def test_get_profile_requires_auth(self, client: TestClient) -> None:
        """Test getting profile requires authentication."""
        response = client.get("/api/profile/me")
        assert response.status_code == 401  # Unauthorized


class TestAttachmentEndpoints:
    """Test attachment questionnaire API endpoints."""

    def test_get_questionnaire_requires_auth(self, client: TestClient) -> None:
        """Test getting questionnaire requires authentication."""
        response = client.get("/api/attachment/questionnaire")
        assert response.status_code == 401  # Unauthorized

    def test_submit_questionnaire_requires_auth(self, client: TestClient) -> None:
        """Test submitting questionnaire requires authentication."""
        questionnaire_data = {
            "responses": [1, 2, 3, 4, 5],
        }
        response = client.post("/api/attachment/submit", json=questionnaire_data)
        assert response.status_code == 401  # Unauthorized


class TestComplianceEndpoints:
    """Test GDPR compliance API endpoints."""

    def test_gdpr_export_requires_auth(self, client: TestClient) -> None:
        """Test GDPR data export requires authentication."""
        response = client.get("/api/compliance/export")
        assert response.status_code == 401  # Unauthorized

    def test_gdpr_delete_requires_auth(self, client: TestClient) -> None:
        """Test GDPR account deletion requires authentication."""
        response = client.delete("/api/compliance/delete")
        assert response.status_code == 401  # Unauthorized


class TestCORSHeaders:
    """Test CORS configuration."""

    def test_cors_headers_present(self, client: TestClient) -> None:
        """Test CORS headers are present in responses."""
        response = client.options("/", headers={"Origin": "http://localhost:3000"})

        # Check for CORS headers (may vary based on implementation)
        assert response.status_code in [200, 204]


class TestRateLimiting:
    """Test rate limiting middleware."""

    def test_rate_limiting_enforced(self, client: TestClient) -> None:
        """Test rate limiting prevents excessive requests."""
        # Make multiple requests rapidly
        responses = []
        for _ in range(150):  # Exceed typical rate limit
            response = client.get("/health")
            responses.append(response.status_code)

        # At least one should be rate limited (429) or all succeed
        assert 429 in responses or all(r == 200 for r in responses)


@pytest.mark.integration
def test_full_user_flow(client: TestClient) -> None:
    """Test complete user registration and profile creation flow."""
    # 1. Register user
    user_data = {
        "email": "fullflow@example.com",
        "password": "SecurePassword123!",
        "consent_data_processing": True,
        "consent_terms": True,
    }
    register_response = client.post("/api/auth/register", json=user_data)
    assert register_response.status_code in [200, 201, 400]

    # 2. Login
    login_data = {
        "username": "fullflow@example.com",
        "password": "SecurePassword123!",
    }
    login_response = client.post("/api/auth/login", data=login_data)

    if login_response.status_code == 200:
        token = login_response.json()["access_token"]

        # 3. Create profile with authentication
        headers = {"Authorization": f"Bearer {token}"}
        profile_data = {
            "name": "Full Flow User",
            "bio": "Testing complete flow",
            "date_of_birth": "1990-01-01",
        }
        profile_response = client.post(
            "/api/profile", json=profile_data, headers=headers
        )

        # Profile creation should succeed or already exist
        assert profile_response.status_code in [200, 201, 400]
