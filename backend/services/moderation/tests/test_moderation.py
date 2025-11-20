"""Comprehensive tests for moderation service."""

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.moderation import (
    ModerationAction,
    ModerationAppeal,
    ModerationAuditLog,
    ModerationQueue,
    ModerationStatus,
    ReportReason,
    UserBlock,
    UserReport,
)
from database.models.user import User
from services.moderation.blocks import create_block, get_blocked_users, is_blocked, remove_block
from services.moderation.perspective import PerspectiveClient, TextScreenRequest
from services.moderation.rekognition import RekognitionClient
from services.moderation.reports import create_report, get_pending_reports, update_report_status
from services.moderation.review_queue import (
    add_to_queue,
    create_appeal,
    get_moderation_stats,
    get_pending_appeals,
    get_pending_queue,
    review_queue_item,
)
from services.moderation.schemas import PerspectiveScore, TextScreenResponse


# Fixtures
@pytest.fixture
async def test_users(db_session: AsyncSession) -> tuple[User, User, User]:
    """Create test users."""
    user1 = User(email="user1@example.com", password_hash="hash1")
    user2 = User(email="user2@example.com", password_hash="hash2")
    admin = User(email="admin@example.com", password_hash="hash3", subscription_tier="admin")

    db_session.add(user1)
    db_session.add(user2)
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)
    await db_session.refresh(admin)

    return user1, user2, admin


# Text screening tests
class TestTextScreening:
    """Tests for text content screening with Perspective API."""

    @patch("services.moderation.perspective.discovery.build")
    def test_perspective_client_initialization(self, mock_build: MagicMock) -> None:
        """Test Perspective API client initialization."""
        os.environ["PERSPECTIVE_API_KEY"] = "test-key"
        client = PerspectiveClient()
        assert client.client is not None
        mock_build.assert_called_once()

    def test_perspective_client_no_api_key(self) -> None:
        """Test that client raises error without API key."""
        if "PERSPECTIVE_API_KEY" in os.environ:
            del os.environ["PERSPECTIVE_API_KEY"]
        with pytest.raises(ValueError, match="PERSPECTIVE_API_KEY"):
            PerspectiveClient()

    @patch("services.moderation.perspective.discovery.build")
    def test_screen_text_auto_block(self, mock_build: MagicMock) -> None:
        """Test text screening with high toxicity (auto-block)."""
        os.environ["PERSPECTIVE_API_KEY"] = "test-key"

        # Mock API response
        mock_client = MagicMock()
        mock_analyze = MagicMock()
        mock_analyze.execute.return_value = {
            "attributeScores": {
                "TOXICITY": {
                    "summaryScore": {"value": 0.90},
                    "spanScores": [{"score": {"value": 0.90}}],
                }
            }
        }
        mock_client.comments.return_value.analyze.return_value = mock_analyze
        mock_build.return_value = mock_client

        client = PerspectiveClient()
        request = TextScreenRequest(text="Very toxic message", context_type="message")
        response = client.screen_text(request)

        assert response.auto_blocked is True
        assert response.allowed is False
        assert response.flagged is False
        assert response.overall_score >= 0.85

    @patch("services.moderation.perspective.discovery.build")
    def test_screen_text_manual_review(self, mock_build: MagicMock) -> None:
        """Test text screening with moderate toxicity (manual review)."""
        os.environ["PERSPECTIVE_API_KEY"] = "test-key"

        # Mock API response
        mock_client = MagicMock()
        mock_analyze = MagicMock()
        mock_analyze.execute.return_value = {
            "attributeScores": {
                "TOXICITY": {
                    "summaryScore": {"value": 0.75},
                    "spanScores": [{"score": {"value": 0.75}}],
                }
            }
        }
        mock_client.comments.return_value.analyze.return_value = mock_analyze
        mock_build.return_value = mock_client

        client = PerspectiveClient()
        request = TextScreenRequest(text="Somewhat problematic message", context_type="message")
        response = client.screen_text(request)

        assert response.flagged is True
        assert response.allowed is True
        assert response.auto_blocked is False
        assert 0.70 <= response.overall_score < 0.85

    @patch("services.moderation.perspective.discovery.build")
    def test_screen_text_allowed(self, mock_build: MagicMock) -> None:
        """Test text screening with low toxicity (allowed)."""
        os.environ["PERSPECTIVE_API_KEY"] = "test-key"

        # Mock API response
        mock_client = MagicMock()
        mock_analyze = MagicMock()
        mock_analyze.execute.return_value = {
            "attributeScores": {
                "TOXICITY": {
                    "summaryScore": {"value": 0.10},
                    "spanScores": [{"score": {"value": 0.10}}],
                }
            }
        }
        mock_client.comments.return_value.analyze.return_value = mock_analyze
        mock_build.return_value = mock_client

        client = PerspectiveClient()
        request = TextScreenRequest(text="Hello, how are you?", context_type="message")
        response = client.screen_text(request)

        assert response.allowed is True
        assert response.flagged is False
        assert response.auto_blocked is False
        assert response.overall_score < 0.70


# Photo screening tests
class TestPhotoScreening:
    """Tests for photo content screening with AWS Rekognition."""

    def test_rekognition_client_no_credentials(self) -> None:
        """Test that client raises error without AWS credentials."""
        if "AWS_ACCESS_KEY_ID" in os.environ:
            del os.environ["AWS_ACCESS_KEY_ID"]
        if "AWS_SECRET_ACCESS_KEY" in os.environ:
            del os.environ["AWS_SECRET_ACCESS_KEY"]

        with pytest.raises(ValueError, match="AWS credentials"):
            RekognitionClient()

    @patch("services.moderation.rekognition.boto3.client")
    def test_screen_photo_inappropriate(self, mock_boto: MagicMock) -> None:
        """Test photo screening with inappropriate content."""
        os.environ["AWS_ACCESS_KEY_ID"] = "test-key"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "test-secret"

        # Mock Rekognition response
        mock_client = MagicMock()
        mock_client.detect_moderation_labels.return_value = {
            "ModerationLabels": [
                {"Name": "Explicit Nudity", "Confidence": 95.0, "ParentName": "Nudity"}
            ]
        }
        mock_boto.return_value = mock_client

        client = RekognitionClient()
        response = client.screen_photo(b"fake_image_bytes")

        assert response.flagged is True
        assert response.allowed is False
        assert "Explicit Nudity" in response.moderation_labels
        assert response.confidence >= 75.0

    @patch("services.moderation.rekognition.boto3.client")
    def test_screen_photo_allowed(self, mock_boto: MagicMock) -> None:
        """Test photo screening with appropriate content."""
        os.environ["AWS_ACCESS_KEY_ID"] = "test-key"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "test-secret"

        # Mock Rekognition response
        mock_client = MagicMock()
        mock_client.detect_moderation_labels.return_value = {"ModerationLabels": []}
        mock_boto.return_value = mock_client

        client = RekognitionClient()
        response = client.screen_photo(b"fake_image_bytes")

        assert response.allowed is True
        assert response.flagged is False
        assert len(response.moderation_labels) == 0


# User blocking tests
class TestUserBlocking:
    """Tests for user blocking functionality."""

    @pytest.mark.asyncio
    async def test_create_block(self, db_session: AsyncSession, test_users: tuple[User, User, User]) -> None:
        """Test creating a user block."""
        user1, user2, _ = test_users

        block = await create_block(db_session, user1.id, user2.id, "Test reason")

        assert block.blocker_id == user1.id
        assert block.blocked_id == user2.id
        assert block.reason == "Test reason"

        # Verify audit log created
        audit_logs = await db_session.execute(select(ModerationAuditLog))
        assert len(audit_logs.scalars().all()) > 0

    @pytest.mark.asyncio
    async def test_create_block_self(self, db_session: AsyncSession, test_users: tuple[User, User, User]) -> None:
        """Test that blocking oneself raises error."""
        user1, _, _ = test_users

        with pytest.raises(ValueError, match="Cannot block yourself"):
            await create_block(db_session, user1.id, user1.id)

    @pytest.mark.asyncio
    async def test_create_duplicate_block(
        self, db_session: AsyncSession, test_users: tuple[User, User, User]
    ) -> None:
        """Test that duplicate blocks raise error."""
        user1, user2, _ = test_users

        await create_block(db_session, user1.id, user2.id)

        with pytest.raises(ValueError, match="already blocked"):
            await create_block(db_session, user1.id, user2.id)

    @pytest.mark.asyncio
    async def test_remove_block(self, db_session: AsyncSession, test_users: tuple[User, User, User]) -> None:
        """Test removing a user block."""
        user1, user2, _ = test_users

        await create_block(db_session, user1.id, user2.id)
        success = await remove_block(db_session, user1.id, user2.id)

        assert success is True

        # Verify block removed
        blocks = await db_session.execute(select(UserBlock))
        assert len(blocks.scalars().all()) == 0

    @pytest.mark.asyncio
    async def test_is_blocked(self, db_session: AsyncSession, test_users: tuple[User, User, User]) -> None:
        """Test checking if users are blocked."""
        user1, user2, _ = test_users

        # Initially not blocked
        assert await is_blocked(db_session, user1.id, user2.id) is False

        # After blocking
        await create_block(db_session, user1.id, user2.id)
        assert await is_blocked(db_session, user1.id, user2.id) is True
        assert await is_blocked(db_session, user2.id, user1.id) is True  # Bidirectional

    @pytest.mark.asyncio
    async def test_get_blocked_users(
        self, db_session: AsyncSession, test_users: tuple[User, User, User]
    ) -> None:
        """Test getting list of blocked users."""
        user1, user2, admin = test_users

        await create_block(db_session, user1.id, user2.id)
        await create_block(db_session, user1.id, admin.id)

        blocked = await get_blocked_users(db_session, user1.id)

        assert len(blocked) == 2
        assert user2.id in blocked
        assert admin.id in blocked


# User reporting tests
class TestUserReporting:
    """Tests for user reporting system."""

    @pytest.mark.asyncio
    async def test_create_report(self, db_session: AsyncSession, test_users: tuple[User, User, User]) -> None:
        """Test creating a user report."""
        user1, user2, _ = test_users

        report = await create_report(
            db=db_session,
            reporter_id=user1.id,
            reported_user_id=user2.id,
            content_type="profile",
            reason=ReportReason.HARASSMENT,
            description="This user is harassing me",
        )

        assert report.reporter_id == user1.id
        assert report.reported_user_id == user2.id
        assert report.reason == ReportReason.HARASSMENT
        assert report.status == ModerationStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_report_self(
        self, db_session: AsyncSession, test_users: tuple[User, User, User]
    ) -> None:
        """Test that reporting oneself raises error."""
        user1, _, _ = test_users

        with pytest.raises(ValueError, match="Cannot report yourself"):
            await create_report(
                db=db_session,
                reporter_id=user1.id,
                reported_user_id=user1.id,
                content_type="profile",
                reason=ReportReason.SPAM,
                description="Test",
            )

    @pytest.mark.asyncio
    async def test_get_pending_reports(
        self, db_session: AsyncSession, test_users: tuple[User, User, User]
    ) -> None:
        """Test getting pending reports."""
        user1, user2, _ = test_users

        await create_report(
            db=db_session,
            reporter_id=user1.id,
            reported_user_id=user2.id,
            content_type="message",
            reason=ReportReason.SPAM,
            description="Spam message",
        )

        pending = await get_pending_reports(db_session)

        assert len(pending) == 1
        assert pending[0].status == ModerationStatus.PENDING

    @pytest.mark.asyncio
    async def test_update_report_status(
        self, db_session: AsyncSession, test_users: tuple[User, User, User]
    ) -> None:
        """Test updating report status after review."""
        user1, user2, admin = test_users

        report = await create_report(
            db=db_session,
            reporter_id=user1.id,
            reported_user_id=user2.id,
            content_type="profile",
            reason=ReportReason.FAKE_PROFILE,
            description="Fake profile",
        )

        updated = await update_report_status(
            db=db_session,
            report_id=report.id,
            moderator_id=admin.id,
            action=ModerationAction.APPROVED,
            notes="Confirmed fake profile",
        )

        assert updated.status == ModerationStatus.APPROVED
        assert updated.reviewed_by == admin.id
        assert updated.action_taken == ModerationAction.APPROVED


# Review queue tests
class TestReviewQueue:
    """Tests for moderation review queue."""

    @pytest.mark.asyncio
    async def test_add_to_queue(self, db_session: AsyncSession, test_users: tuple[User, User, User]) -> None:
        """Test adding content to moderation queue."""
        user1, _, _ = test_users

        item = await add_to_queue(
            db=db_session,
            content_type="message",
            content_id=uuid4(),
            user_id=user1.id,
            overall_score=0.80,
            content_text="Flagged message",
            perspective_scores={"TOXICITY": 0.80},
        )

        assert item.user_id == user1.id
        assert item.status == ModerationStatus.PENDING
        assert item.overall_score == 0.80

    @pytest.mark.asyncio
    async def test_get_pending_queue(
        self, db_session: AsyncSession, test_users: tuple[User, User, User]
    ) -> None:
        """Test getting pending queue items."""
        user1, _, _ = test_users

        # Add multiple items
        await add_to_queue(
            db=db_session,
            content_type="message",
            content_id=uuid4(),
            user_id=user1.id,
            overall_score=0.75,
        )
        await add_to_queue(
            db=db_session,
            content_type="message",
            content_id=uuid4(),
            user_id=user1.id,
            overall_score=0.90,
        )

        pending = await get_pending_queue(db_session)

        assert len(pending) == 2
        # Should be ordered by score descending
        assert pending[0].overall_score >= pending[1].overall_score

    @pytest.mark.asyncio
    async def test_review_queue_item(
        self, db_session: AsyncSession, test_users: tuple[User, User, User]
    ) -> None:
        """Test reviewing a queue item."""
        user1, _, admin = test_users

        item = await add_to_queue(
            db=db_session,
            content_type="message",
            content_id=uuid4(),
            user_id=user1.id,
            overall_score=0.80,
        )

        reviewed = await review_queue_item(
            db=db_session,
            item_id=item.id,
            moderator_id=admin.id,
            action=ModerationAction.CONTENT_REMOVED,
            notes="Content violated guidelines",
        )

        assert reviewed.status == ModerationStatus.REJECTED
        assert reviewed.reviewed_by == admin.id
        assert reviewed.action_taken == ModerationAction.CONTENT_REMOVED

    @pytest.mark.asyncio
    async def test_get_moderation_stats(
        self, db_session: AsyncSession, test_users: tuple[User, User, User]
    ) -> None:
        """Test getting moderation statistics."""
        user1, _, _ = test_users

        # Add some queue items
        await add_to_queue(
            db=db_session,
            content_type="message",
            content_id=uuid4(),
            user_id=user1.id,
            overall_score=0.75,
        )

        stats = await get_moderation_stats(db_session)

        assert "pending_queue_items" in stats
        assert "auto_blocked_today" in stats
        assert "manual_reviews_today" in stats
        assert stats["pending_queue_items"] >= 1


# Appeal tests
class TestAppeals:
    """Tests for moderation appeals."""

    @pytest.mark.asyncio
    async def test_create_appeal(self, db_session: AsyncSession, test_users: tuple[User, User, User]) -> None:
        """Test creating an appeal."""
        user1, _, _ = test_users

        # Create a queue item first
        item = await add_to_queue(
            db=db_session,
            content_type="message",
            content_id=uuid4(),
            user_id=user1.id,
            overall_score=0.90,
        )

        # Create appeal
        appeal = await create_appeal(
            db=db_session,
            user_id=user1.id,
            moderation_queue_id=item.id,
            reason="This was a false positive",
            additional_context="I was using sarcasm",
        )

        assert appeal.user_id == user1.id
        assert appeal.moderation_queue_id == item.id
        assert appeal.status == ModerationStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_pending_appeals(
        self, db_session: AsyncSession, test_users: tuple[User, User, User]
    ) -> None:
        """Test getting pending appeals."""
        user1, _, _ = test_users

        item = await add_to_queue(
            db=db_session,
            content_type="message",
            content_id=uuid4(),
            user_id=user1.id,
            overall_score=0.90,
        )

        await create_appeal(
            db=db_session, user_id=user1.id, moderation_queue_id=item.id, reason="Appeal reason"
        )

        pending = await get_pending_appeals(db_session)

        assert len(pending) == 1
        assert pending[0].status == ModerationStatus.PENDING


# Integration tests
class TestModerationIntegration:
    """Integration tests for complete moderation workflows."""

    @pytest.mark.asyncio
    async def test_full_moderation_workflow(
        self, db_session: AsyncSession, test_users: tuple[User, User, User]
    ) -> None:
        """Test complete moderation workflow from flagging to review."""
        user1, _, admin = test_users

        # 1. Content flagged and added to queue
        item = await add_to_queue(
            db=db_session,
            content_type="message",
            content_id=uuid4(),
            user_id=user1.id,
            overall_score=0.78,
            content_text="Problematic message",
        )

        # 2. Verify in pending queue
        pending = await get_pending_queue(db_session)
        assert len(pending) == 1

        # 3. Moderator reviews and takes action
        reviewed = await review_queue_item(
            db=db_session,
            item_id=item.id,
            moderator_id=admin.id,
            action=ModerationAction.CONTENT_REMOVED,
        )

        # 4. Verify no longer in pending queue
        pending_after = await get_pending_queue(db_session)
        assert len(pending_after) == 0

        # 5. Verify audit log created
        audit_logs = await db_session.execute(
            select(ModerationAuditLog).where(ModerationAuditLog.content_id == item.content_id)
        )
        logs = audit_logs.scalars().all()
        assert len(logs) >= 2  # One for flagging, one for review
