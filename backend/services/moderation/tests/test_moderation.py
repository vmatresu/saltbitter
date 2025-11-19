"""
Tests for moderation service.

Covers text screening, photo screening, user reports, blocking, and review queue.
"""

import pytest
from typing import Dict, Any
from uuid import uuid4

from backend.database.models.moderation import (
    ContentType,
    ModerationStatus,
    ReportReason,
)
from backend.services.moderation.perspective import PerspectiveAPIClient
from backend.services.moderation.rekognition import RekognitionClient


class TestPerspectiveAPIClient:
    """Tests for Perspective API client."""

    def test_should_auto_block_high_toxicity(self) -> None:
        """Test auto-block for high toxicity score."""
        client = PerspectiveAPIClient(api_key="test-key")
        scores = {"TOXICITY": 0.90, "THREAT": 0.10}
        assert client.should_auto_block(scores) is True

    def test_should_auto_block_low_toxicity(self) -> None:
        """Test no auto-block for low toxicity score."""
        client = PerspectiveAPIClient(api_key="test-key")
        scores = {"TOXICITY": 0.10, "THREAT": 0.05}
        assert client.should_auto_block(scores) is False

    def test_should_manual_review_medium_toxicity(self) -> None:
        """Test manual review for medium toxicity score."""
        client = PerspectiveAPIClient(api_key="test-key")
        scores = {"TOXICITY": 0.75, "THREAT": 0.05}
        assert client.should_manual_review(scores) is True

    def test_should_manual_review_low_toxicity(self) -> None:
        """Test no manual review for low toxicity."""
        client = PerspectiveAPIClient(api_key="test-key")
        scores = {"TOXICITY": 0.50, "THREAT": 0.05}
        assert client.should_manual_review(scores) is False

    def test_should_manual_review_false_when_auto_blocked(self) -> None:
        """Test manual review returns False when content is auto-blocked."""
        client = PerspectiveAPIClient(api_key="test-key")
        scores = {"TOXICITY": 0.95, "THREAT": 0.10}
        assert client.should_manual_review(scores) is False  # Auto-blocked, not reviewed

    def test_get_max_score(self) -> None:
        """Test getting maximum toxicity score."""
        client = PerspectiveAPIClient(api_key="test-key")
        scores = {"TOXICITY": 0.75, "THREAT": 0.90, "PROFANITY": 0.20}
        assert client.get_max_score(scores) == 0.90

    def test_get_max_score_empty(self) -> None:
        """Test max score with empty dictionary."""
        client = PerspectiveAPIClient(api_key="test-key")
        scores: Dict[str, float] = {}
        assert client.get_max_score(scores) == 0.0


class TestRekognitionClient:
    """Tests for AWS Rekognition client."""

    def test_should_auto_block_high_confidence_unsafe(self) -> None:
        """Test auto-block for high confidence unsafe content."""
        client = RekognitionClient()
        result = {
            "max_confidence": 90.0,
            "labels": {
                "Explicit Nudity": [{"label": "Nudity", "confidence": 90.0}]
            },
        }
        assert client.should_auto_block(result) is True

    def test_should_auto_block_high_confidence_safe(self) -> None:
        """Test no auto-block for high confidence safe content."""
        client = RekognitionClient()
        result = {
            "max_confidence": 95.0,
            "labels": {
                "Flowers": [{"label": "Rose", "confidence": 95.0}]
            },
        }
        assert client.should_auto_block(result) is False

    def test_should_manual_review_medium_confidence(self) -> None:
        """Test manual review for medium confidence unsafe content."""
        client = RekognitionClient()
        result = {
            "max_confidence": 75.0,
            "labels": {
                "Suggestive": [{"label": "Revealing Clothes", "confidence": 75.0}]
            },
        }
        assert client.should_manual_review(result) is True

    def test_should_manual_review_false_when_auto_blocked(self) -> None:
        """Test manual review returns False when auto-blocked."""
        client = RekognitionClient()
        result = {
            "max_confidence": 95.0,
            "labels": {
                "Violence": [{"label": "Graphic Violence", "confidence": 95.0}]
            },
        }
        assert client.should_manual_review(result) is False


class TestModerationEndpoints:
    """Tests for moderation API endpoints."""

    @pytest.fixture
    def mock_user(self) -> Dict[str, Any]:
        """Create a mock user."""
        return {
            "id": uuid4(),
            "email": "test@example.com",
            "subscription_tier": "free",
        }

    @pytest.fixture
    def mock_perspective_scores(self) -> Dict[str, float]:
        """Mock Perspective API scores."""
        return {
            "TOXICITY": 0.10,
            "SEVERE_TOXICITY": 0.05,
            "IDENTITY_ATTACK": 0.02,
            "THREAT": 0.01,
            "SEXUALLY_EXPLICIT": 0.01,
            "PROFANITY": 0.05,
        }

    def test_text_screen_request_validation(self, mock_user: Dict[str, Any]) -> None:
        """Test text screen request validates correctly."""
        from backend.services.moderation.schemas import TextScreenRequest

        request = TextScreenRequest(
            text="Hello, this is a test message",
            content_type=ContentType.MESSAGE,
            user_id=mock_user["id"],
        )

        assert request.text == "Hello, this is a test message"
        assert request.content_type == ContentType.MESSAGE
        assert request.user_id == mock_user["id"]

    def test_text_screen_request_empty_text_fails(self, mock_user: Dict[str, Any]) -> None:
        """Test that empty text fails validation."""
        from pydantic import ValidationError
        from backend.services.moderation.schemas import TextScreenRequest

        with pytest.raises(ValidationError):
            TextScreenRequest(
                text="",
                content_type=ContentType.MESSAGE,
                user_id=mock_user["id"],
            )

    def test_block_user_request_validation(self, mock_user: Dict[str, Any]) -> None:
        """Test block user request validates correctly."""
        from backend.services.moderation.schemas import BlockUserRequest

        blocked_user_id = uuid4()
        request = BlockUserRequest(
            blocked_user_id=blocked_user_id,
            reason="Unwanted contact",
        )

        assert request.blocked_user_id == blocked_user_id
        assert request.reason == "Unwanted contact"

    def test_create_report_request_validation(self, mock_user: Dict[str, Any]) -> None:
        """Test create report request validates correctly."""
        from backend.services.moderation.schemas import CreateReportRequest

        reported_user_id = uuid4()
        request = CreateReportRequest(
            reported_user_id=reported_user_id,
            reason=ReportReason.HARASSMENT,
            description="User is harassing me",
        )

        assert request.reported_user_id == reported_user_id
        assert request.reason == ReportReason.HARASSMENT
        assert request.description == "User is harassing me"

    def test_review_decision_request_validation(self) -> None:
        """Test review decision request validates correctly."""
        from backend.services.moderation.schemas import ReviewDecisionRequest

        request = ReviewDecisionRequest(
            approved=True,
            notes="Content is acceptable",
        )

        assert request.approved is True
        assert request.notes == "Content is acceptable"

    def test_create_appeal_request_validation(self, mock_user: Dict[str, Any]) -> None:
        """Test create appeal request validates correctly."""
        from backend.services.moderation.schemas import CreateAppealRequest

        record_id = uuid4()
        request = CreateAppealRequest(
            moderation_record_id=record_id,
            appeal_text="This was a mistake, my message was not harmful",
        )

        assert request.moderation_record_id == record_id
        assert len(request.appeal_text) >= 10

    def test_create_appeal_request_too_short_fails(self) -> None:
        """Test that appeal text too short fails validation."""
        from pydantic import ValidationError
        from backend.services.moderation.schemas import CreateAppealRequest

        with pytest.raises(ValidationError):
            CreateAppealRequest(
                moderation_record_id=uuid4(),
                appeal_text="short",  # Too short, min is 10 chars
            )


class TestModerationModels:
    """Tests for moderation database models."""

    def test_moderation_record_creation(self) -> None:
        """Test creating a moderation record."""
        from backend.database.models.moderation import ModerationRecord

        user_id = uuid4()
        record = ModerationRecord(
            content_type=ContentType.MESSAGE,
            user_id=user_id,
            content_text="Test message",
            toxicity_score=0.10,
            max_score=0.10,
            flagged=False,
            status=ModerationStatus.APPROVED,
        )

        assert record.content_type == ContentType.MESSAGE
        assert record.user_id == user_id
        assert record.content_text == "Test message"
        assert record.toxicity_score == 0.10
        assert record.flagged is False
        assert record.status == ModerationStatus.APPROVED

    def test_user_report_creation(self) -> None:
        """Test creating a user report."""
        from backend.database.models.moderation import UserReport

        reporter_id = uuid4()
        reported_user_id = uuid4()

        report = UserReport(
            reporter_id=reporter_id,
            reported_user_id=reported_user_id,
            reason=ReportReason.HARASSMENT,
            description="User is sending unwanted messages",
            status=ModerationStatus.PENDING,
        )

        assert report.reporter_id == reporter_id
        assert report.reported_user_id == reported_user_id
        assert report.reason == ReportReason.HARASSMENT
        assert report.status == ModerationStatus.PENDING

    def test_user_block_creation(self) -> None:
        """Test creating a user block."""
        from backend.database.models.moderation import UserBlock

        user_id = uuid4()
        blocked_user_id = uuid4()

        block = UserBlock(
            user_id=user_id,
            blocked_user_id=blocked_user_id,
            reason="Unwanted contact",
        )

        assert block.user_id == user_id
        assert block.blocked_user_id == blocked_user_id
        assert block.reason == "Unwanted contact"

    def test_moderation_appeal_creation(self) -> None:
        """Test creating a moderation appeal."""
        from backend.database.models.moderation import ModerationAppeal

        user_id = uuid4()
        record_id = uuid4()

        appeal = ModerationAppeal(
            moderation_record_id=record_id,
            user_id=user_id,
            appeal_text="This was a false positive, my message was appropriate",
            status=ModerationStatus.PENDING,
        )

        assert appeal.moderation_record_id == record_id
        assert appeal.user_id == user_id
        assert appeal.status == ModerationStatus.PENDING
        assert len(appeal.appeal_text) > 0


class TestModerationWorkflow:
    """Tests for end-to-end moderation workflows."""

    def test_toxicity_screening_workflow(self) -> None:
        """Test complete toxicity screening workflow."""
        from backend.services.moderation.perspective import PerspectiveAPIClient

        client = PerspectiveAPIClient(api_key="test-key")

        # Low toxicity - should pass
        low_scores = {"TOXICITY": 0.10, "THREAT": 0.05, "PROFANITY": 0.02}
        assert not client.should_auto_block(low_scores)
        assert not client.should_manual_review(low_scores)

        # Medium toxicity - should review
        medium_scores = {"TOXICITY": 0.75, "THREAT": 0.10, "PROFANITY": 0.05}
        assert not client.should_auto_block(medium_scores)
        assert client.should_manual_review(medium_scores)

        # High toxicity - should block
        high_scores = {"TOXICITY": 0.90, "THREAT": 0.85, "PROFANITY": 0.70}
        assert client.should_auto_block(high_scores)
        assert not client.should_manual_review(high_scores)  # Blocked, not reviewed

    def test_photo_moderation_workflow(self) -> None:
        """Test complete photo moderation workflow."""
        from backend.services.moderation.rekognition import RekognitionClient

        client = RekognitionClient()

        # Safe content
        safe_result = {
            "max_confidence": 95.0,
            "labels": {"Nature": [{"label": "Tree", "confidence": 95.0}]},
        }
        assert not client.should_auto_block(safe_result)
        assert not client.should_manual_review(safe_result)

        # Questionable content - review
        questionable_result = {
            "max_confidence": 75.0,
            "labels": {"Suggestive": [{"label": "Revealing Clothes", "confidence": 75.0}]},
        }
        assert not client.should_auto_block(questionable_result)
        assert client.should_manual_review(questionable_result)

        # Unsafe content - block
        unsafe_result = {
            "max_confidence": 90.0,
            "labels": {"Explicit Nudity": [{"label": "Nudity", "confidence": 90.0}]},
        }
        assert client.should_auto_block(unsafe_result)
        assert not client.should_manual_review(unsafe_result)  # Blocked, not reviewed
