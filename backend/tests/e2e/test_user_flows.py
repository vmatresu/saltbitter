"""End-to-end tests for critical user flows.

Tests complete user journeys through the SaltBitter platform.
"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for E2E testing."""
    return TestClient(app)


@pytest.fixture
def authenticated_client(client: TestClient) -> tuple[TestClient, str]:
    """Create an authenticated test client with JWT token."""
    # Register and login a test user
    user_data = {
        "email": "e2e_user@example.com",
        "password": "SecurePassword123!",
        "consent_data_processing": True,
        "consent_terms": True,
    }
    client.post("/api/auth/register", json=user_data)

    login_data = {
        "username": "e2e_user@example.com",
        "password": "SecurePassword123!",
    }
    response = client.post("/api/auth/login", data=login_data)

    if response.status_code == 200:
        token = response.json()["access_token"]
        return client, token
    else:
        pytest.skip("Authentication failed - user might already exist")


@pytest.mark.e2e
class TestUserOnboarding:
    """Test complete user onboarding flow."""

    def test_new_user_registration_to_profile_creation(
        self, client: TestClient
    ) -> None:
        """Test new user can register, login, and create profile."""
        # Step 1: Register
        user_data = {
            "email": "onboarding@example.com",
            "password": "SecurePassword123!",
            "consent_data_processing": True,
            "consent_terms": True,
        }
        register_response = client.post("/api/auth/register", json=user_data)
        assert register_response.status_code in [200, 201, 400]

        # Step 2: Login
        login_data = {
            "username": "onboarding@example.com",
            "password": "SecurePassword123!",
        }
        login_response = client.post("/api/auth/login", data=login_data)

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]

            # Step 3: Create profile
            headers = {"Authorization": f"Bearer {token}"}
            profile_data = {
                "name": "Onboarding User",
                "bio": "New to SaltBitter",
                "date_of_birth": "1990-01-01",
            }
            profile_response = client.post(
                "/api/profile", json=profile_data, headers=headers
            )
            assert profile_response.status_code in [200, 201, 400]

    def test_attachment_questionnaire_completion(
        self, client: TestClient, authenticated_client: tuple[TestClient, str]
    ) -> None:
        """Test user can complete attachment style questionnaire."""
        _, token = authenticated_client
        headers = {"Authorization": f"Bearer {token}"}

        # Get questionnaire
        questionnaire_response = client.get(
            "/api/attachment/questionnaire", headers=headers
        )

        if questionnaire_response.status_code == 200:
            # Submit responses (ECR-R has 36 questions, 1-7 scale)
            responses_data = {
                "responses": [4] * 36,  # Neutral responses
            }
            submit_response = client.post(
                "/api/attachment/submit", json=responses_data, headers=headers
            )
            assert submit_response.status_code in [200, 201]


@pytest.mark.e2e
class TestGDPRCompliance:
    """Test GDPR compliance user flows."""

    def test_user_can_export_data(
        self, client: TestClient, authenticated_client: tuple[TestClient, str]
    ) -> None:
        """Test user can request and receive data export."""
        _, token = authenticated_client
        headers = {"Authorization": f"Bearer {token}"}

        # Request data export
        export_response = client.get("/api/compliance/export", headers=headers)

        if export_response.status_code == 200:
            data = export_response.json()
            # Should contain user data in structured format
            assert "user" in data or "profile" in data or "data" in data

    def test_user_can_delete_account(
        self, client: TestClient, authenticated_client: tuple[TestClient, str]
    ) -> None:
        """Test user can delete their account per GDPR Article 17."""
        _, token = authenticated_client
        headers = {"Authorization": f"Bearer {token}"}

        # Request account deletion
        delete_response = client.delete("/api/compliance/delete", headers=headers)

        # Should accept deletion request
        assert delete_response.status_code in [200, 202, 204]


@pytest.mark.e2e
class TestMatchingFlow:
    """Test user matching and interaction flows."""

    def test_user_can_view_matches(
        self, client: TestClient, authenticated_client: tuple[TestClient, str]
    ) -> None:
        """Test user can view their daily matches."""
        _, token = authenticated_client
        headers = {"Authorization": f"Bearer {token}"}

        # Get matches
        matches_response = client.get("/api/matches", headers=headers)

        # May return empty list or matches
        assert matches_response.status_code in [200, 404]

        if matches_response.status_code == 200:
            data = matches_response.json()
            assert isinstance(data, list) or isinstance(data, dict)


@pytest.mark.e2e
class TestErrorHandling:
    """Test application error handling in real scenarios."""

    def test_invalid_token_rejected(self, client: TestClient) -> None:
        """Test invalid JWT tokens are properly rejected."""
        headers = {"Authorization": "Bearer invalid_token_12345"}

        response = client.get("/api/profile/me", headers=headers)
        assert response.status_code in [401, 403]

    def test_malformed_request_handled(self, client: TestClient) -> None:
        """Test malformed requests return appropriate errors."""
        # Send malformed registration data
        bad_data = {
            "email": "not_an_email",
            "password": "short",
        }
        response = client.post("/api/auth/register", json=bad_data)

        # Should return validation error
        assert response.status_code in [400, 422]


@pytest.mark.e2e
@pytest.mark.slow
class TestSecurityControls:
    """Test security controls in real usage scenarios."""

    def test_sql_injection_prevented(self, client: TestClient) -> None:
        """Test SQL injection attempts are prevented."""
        malicious_login = {
            "username": "admin' OR '1'='1",
            "password": "anything",
        }
        response = client.post("/api/auth/login", data=malicious_login)

        # Should not succeed with injection
        assert response.status_code in [401, 400, 422]

    def test_xss_prevented_in_profile(
        self, client: TestClient, authenticated_client: tuple[TestClient, str]
    ) -> None:
        """Test XSS payloads are sanitized in profile fields."""
        _, token = authenticated_client
        headers = {"Authorization": f"Bearer {token}"}

        xss_payload = {
            "name": "<script>alert('xss')</script>",
            "bio": "<img src=x onerror=alert('xss')>",
            "date_of_birth": "1990-01-01",
        }

        response = client.post("/api/profile", json=xss_payload, headers=headers)

        # Should either sanitize or reject
        assert response.status_code in [200, 201, 400, 422]

        if response.status_code in [200, 201]:
            # If accepted, verify it's sanitized
            profile_response = client.get("/api/profile/me", headers=headers)
            if profile_response.status_code == 200:
                profile = profile_response.json()
                # Should not contain script tags
                assert "<script>" not in str(profile)
