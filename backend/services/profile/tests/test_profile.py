"""
Comprehensive tests for profile service.

Tests cover:
- Profile retrieval (GET)
- Profile updates (PUT)
- Photo uploads with face detection (POST)
- Photo deletion (DELETE)
- Profile completeness calculation
- Location handling (PostGIS)
- Image validation
- S3 integration (mocked)
"""

import io
import os
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import Base, Profile, User
from backend.services.auth.security import create_access_token, hash_password
from backend.services.profile.routes import calculate_completeness_score
from backend.services.profile.storage import StorageService

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
        id=uuid4(),
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
def test_profile(db_session: Session, test_user: User) -> Profile:
    """Create a test profile."""
    profile = Profile(
        user_id=test_user.id,
        name="Test User",
        age=25,
        gender="male",
        bio="Test bio",
        photos=[],
        completeness_score=30.0,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Create authorization headers with access token."""
    token = create_access_token(data={"sub": str(test_user.id), "type": "access"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_client(db_session: Session):
    """Create a test client with database session override."""
    from backend.main import app
    from backend.services.profile.routes import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_storage_service():
    """Mock storage service for S3 operations."""
    with patch("backend.services.profile.routes.storage_service") as mock:
        mock.upload_photo = AsyncMock(return_value=("test-photo-id", "https://cdn.example.com/photo.jpg"))
        mock.delete_photo = AsyncMock(return_value=True)
        mock.detect_faces = AsyncMock(return_value=(True, 95.5))
        mock.get_photo_count = AsyncMock(return_value=0)
        yield mock


def create_test_image(width: int = 1000, height: int = 1000, format: str = "JPEG") -> bytes:
    """
    Create a test image as bytes.

    Args:
        width: Image width
        height: Image height
        format: Image format

    Returns:
        Image bytes
    """
    img = Image.new("RGB", (width, height), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes.read()


# ===== Utility Function Tests =====


class TestCalculateCompletenessScore:
    """Tests for profile completeness calculation."""

    def test_basic_profile_30_percent(self, test_profile: Profile):
        """Test basic profile with only required fields (30%)."""
        test_profile.bio = None
        test_profile.photos = []
        test_profile.location = None
        test_profile.looking_for_gender = None

        score = calculate_completeness_score(test_profile)
        assert score == 30.0

    def test_with_bio_50_percent(self, test_profile: Profile):
        """Test profile with bio (30% + 20% = 50%)."""
        test_profile.bio = "This is my bio"
        test_profile.photos = []
        test_profile.location = None

        score = calculate_completeness_score(test_profile)
        assert score == 50.0

    def test_with_location_65_percent(self, test_profile: Profile):
        """Test profile with bio and location (30% + 20% + 15% = 65%)."""
        test_profile.bio = "This is my bio"
        test_profile.photos = []
        test_profile.location = "SRID=4326;POINT(-122.4194 37.7749)"

        score = calculate_completeness_score(test_profile)
        assert score == 65.0

    def test_with_photos(self, test_profile: Profile):
        """Test profile with photos (5% per photo, max 25%)."""
        test_profile.bio = "Bio"
        test_profile.photos = [
            {"photo_id": "1", "url": "url1"},
            {"photo_id": "2", "url": "url2"},
            {"photo_id": "3", "url": "url3"},
        ]

        score = calculate_completeness_score(test_profile)
        # 30 (required) + 20 (bio) + 15 (3 photos * 5)
        assert score == 65.0

    def test_with_all_preferences(self, test_profile: Profile):
        """Test profile with all preferences (10%)."""
        test_profile.looking_for_gender = "female"
        test_profile.min_age = 21
        test_profile.max_age = 30
        test_profile.max_distance_km = 50

        score = calculate_completeness_score(test_profile)
        # 30 (required) + 10 (preferences)
        assert score == 40.0

    def test_complete_profile_100_percent(self, test_profile: Profile):
        """Test fully complete profile (100%)."""
        test_profile.bio = "Complete bio"
        test_profile.location = "SRID=4326;POINT(-122.4194 37.7749)"
        test_profile.photos = [{"photo_id": str(i), "url": f"url{i}"} for i in range(5)]
        test_profile.looking_for_gender = "female"
        test_profile.min_age = 21
        test_profile.max_age = 30
        test_profile.max_distance_km = 50

        score = calculate_completeness_score(test_profile)
        # 30 + 20 + 15 + 25 + 10 = 100
        assert score == 100.0


# ===== Profile API Tests =====


class TestGetProfile:
    """Tests for GET /api/profiles/{user_id}."""

    def test_get_profile_success(
        self, test_client: TestClient, test_profile: Profile, auth_headers: dict[str, str]
    ):
        """Test successful profile retrieval."""
        response = test_client.get(f"/api/profiles/{test_profile.user_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(test_profile.user_id)
        assert data["name"] == "Test User"
        assert data["age"] == 25
        assert data["gender"] == "male"
        assert data["bio"] == "Test bio"

    def test_get_profile_not_found(self, test_client: TestClient, auth_headers: dict[str, str]):
        """Test profile not found."""
        non_existent_id = uuid4()
        response = test_client.get(f"/api/profiles/{non_existent_id}", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_profile_unauthorized(self, test_client: TestClient, test_profile: Profile):
        """Test unauthorized access without token."""
        response = test_client.get(f"/api/profiles/{test_profile.user_id}")

        assert response.status_code == 422  # Missing header


class TestUpdateProfile:
    """Tests for PUT /api/profiles/{user_id}."""

    def test_update_profile_name(
        self,
        test_client: TestClient,
        test_profile: Profile,
        auth_headers: dict[str, str],
        db_session: Session,
    ):
        """Test updating profile name."""
        response = test_client.put(
            f"/api/profiles/{test_profile.user_id}",
            json={"name": "Updated Name"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

        # Verify in database
        db_session.refresh(test_profile)
        assert test_profile.name == "Updated Name"

    def test_update_profile_bio(
        self,
        test_client: TestClient,
        test_profile: Profile,
        auth_headers: dict[str, str],
        db_session: Session,
    ):
        """Test updating profile bio."""
        new_bio = "This is my updated bio with more details"
        response = test_client.put(
            f"/api/profiles/{test_profile.user_id}",
            json={"bio": new_bio},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == new_bio

    def test_update_profile_location(
        self,
        test_client: TestClient,
        test_profile: Profile,
        auth_headers: dict[str, str],
    ):
        """Test updating profile location."""
        response = test_client.put(
            f"/api/profiles/{test_profile.user_id}",
            json={"location": {"latitude": 37.7749, "longitude": -122.4194}},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["location"] is not None

    def test_update_profile_preferences(
        self,
        test_client: TestClient,
        test_profile: Profile,
        auth_headers: dict[str, str],
    ):
        """Test updating profile preferences."""
        response = test_client.put(
            f"/api/profiles/{test_profile.user_id}",
            json={"looking_for_gender": "female", "min_age": 21, "max_age": 30, "max_distance_km": 50},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["looking_for_gender"] == "female"
        assert data["min_age"] == 21
        assert data["max_age"] == 30
        assert data["max_distance_km"] == 50

    def test_update_profile_unauthorized(self, test_client: TestClient, test_profile: Profile):
        """Test updating profile without authorization."""
        response = test_client.put(
            f"/api/profiles/{test_profile.user_id}",
            json={"name": "Hacker"},
        )

        assert response.status_code == 422

    def test_update_profile_wrong_user(
        self,
        test_client: TestClient,
        test_profile: Profile,
        auth_headers: dict[str, str],
    ):
        """Test user cannot update another user's profile."""
        other_user_id = uuid4()
        response = test_client.put(
            f"/api/profiles/{other_user_id}",
            json={"name": "Unauthorized"},
            headers=auth_headers,
        )

        assert response.status_code == 403

    def test_update_completeness_score_recalculated(
        self,
        test_client: TestClient,
        test_profile: Profile,
        auth_headers: dict[str, str],
    ):
        """Test that completeness score is recalculated after update."""
        initial_response = test_client.get(f"/api/profiles/{test_profile.user_id}", headers=auth_headers)
        initial_score = initial_response.json()["completeness_score"]

        # Add bio to increase score
        response = test_client.put(
            f"/api/profiles/{test_profile.user_id}",
            json={"bio": "New bio to increase score"},
            headers=auth_headers,
        )

        new_score = response.json()["completeness_score"]
        assert new_score > initial_score


class TestPhotoUpload:
    """Tests for POST /api/profiles/{user_id}/photos."""

    def test_upload_photo_success(
        self,
        test_client: TestClient,
        test_profile: Profile,
        auth_headers: dict[str, str],
        mock_storage_service,
    ):
        """Test successful photo upload."""
        image_bytes = create_test_image()

        response = test_client.post(
            f"/api/profiles/{test_profile.user_id}/photos",
            files={"file": ("test.jpg", image_bytes, "image/jpeg")},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "photo_id" in data
        assert "url" in data
        assert data["face_detected"] is True

    def test_upload_photo_no_face_detected(
        self,
        test_client: TestClient,
        test_profile: Profile,
        auth_headers: dict[str, str],
        mock_storage_service,
    ):
        """Test photo upload fails when no face detected."""
        mock_storage_service.detect_faces = AsyncMock(return_value=(False, 0.0))
        image_bytes = create_test_image()

        response = test_client.post(
            f"/api/profiles/{test_profile.user_id}/photos",
            files={"file": ("test.jpg", image_bytes, "image/jpeg")},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "face" in response.json()["detail"].lower()

    def test_upload_photo_max_limit(
        self,
        test_client: TestClient,
        test_profile: Profile,
        auth_headers: dict[str, str],
        mock_storage_service,
        db_session: Session,
    ):
        """Test that uploading more than 6 photos fails."""
        # Add 6 photos to profile
        test_profile.photos = [{"photo_id": f"photo-{i}", "url": f"url-{i}"} for i in range(6)]
        db_session.commit()

        image_bytes = create_test_image()

        response = test_client.post(
            f"/api/profiles/{test_profile.user_id}/photos",
            files={"file": ("test.jpg", image_bytes, "image/jpeg")},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "maximum" in response.json()["detail"].lower()

    def test_upload_photo_unauthorized(
        self,
        test_client: TestClient,
        test_profile: Profile,
        mock_storage_service,
    ):
        """Test photo upload without authorization."""
        image_bytes = create_test_image()

        response = test_client.post(
            f"/api/profiles/{test_profile.user_id}/photos",
            files={"file": ("test.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 422


class TestPhotoDelete:
    """Tests for DELETE /api/profiles/{user_id}/photos/{photo_id}."""

    def test_delete_photo_success(
        self,
        test_client: TestClient,
        test_profile: Profile,
        auth_headers: dict[str, str],
        mock_storage_service,
        db_session: Session,
    ):
        """Test successful photo deletion."""
        # Add photo to profile
        photo_id = "test-photo-123"
        test_profile.photos = [{"photo_id": photo_id, "url": "https://example.com/photo.jpg"}]
        db_session.commit()

        response = test_client.delete(
            f"/api/profiles/{test_profile.user_id}/photos/{photo_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_photo_id"] == photo_id

        # Verify photo removed from database
        db_session.refresh(test_profile)
        assert len(test_profile.photos) == 0

    def test_delete_photo_not_found(
        self,
        test_client: TestClient,
        test_profile: Profile,
        auth_headers: dict[str, str],
        mock_storage_service,
    ):
        """Test deleting non-existent photo."""
        response = test_client.delete(
            f"/api/profiles/{test_profile.user_id}/photos/non-existent-id",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_delete_photo_reorders_remaining(
        self,
        test_client: TestClient,
        test_profile: Profile,
        auth_headers: dict[str, str],
        mock_storage_service,
        db_session: Session,
    ):
        """Test that remaining photos are reordered after deletion."""
        # Add multiple photos
        test_profile.photos = [
            {"photo_id": "photo-1", "url": "url-1", "order": 0},
            {"photo_id": "photo-2", "url": "url-2", "order": 1},
            {"photo_id": "photo-3", "url": "url-3", "order": 2},
        ]
        db_session.commit()

        # Delete middle photo
        response = test_client.delete(
            f"/api/profiles/{test_profile.user_id}/photos/photo-2",
            headers=auth_headers,
        )

        assert response.status_code == 200

        # Verify reordering
        db_session.refresh(test_profile)
        assert len(test_profile.photos) == 2
        assert test_profile.photos[0]["order"] == 0
        assert test_profile.photos[1]["order"] == 1


# ===== Storage Service Tests =====


class TestStorageService:
    """Tests for StorageService."""

    def test_validate_image_success(self):
        """Test successful image validation."""
        storage = StorageService()
        image_bytes = create_test_image(1000, 1000)

        is_valid, error = storage.validate_image(image_bytes, "test.jpg")

        assert is_valid is True
        assert error is None

    def test_validate_image_too_small(self):
        """Test image validation fails for small images."""
        storage = StorageService()
        image_bytes = create_test_image(500, 500)  # Below 800x800 minimum

        is_valid, error = storage.validate_image(image_bytes, "test.jpg")

        assert is_valid is False
        assert "dimensions" in error.lower()

    def test_validate_image_too_large(self):
        """Test image validation fails for large files."""
        storage = StorageService()
        # Create a large byte array (>10MB)
        large_bytes = b"x" * (11 * 1024 * 1024)

        is_valid, error = storage.validate_image(large_bytes, "test.jpg")

        assert is_valid is False
        assert "size" in error.lower()

    def test_validate_image_invalid_format(self):
        """Test image validation fails for invalid format."""
        storage = StorageService()
        invalid_bytes = b"not an image"

        is_valid, error = storage.validate_image(invalid_bytes, "test.txt")

        assert is_valid is False
        assert "invalid" in error.lower()
