"""Moderation models for content safety and user blocking."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class ModerationStatus(str, Enum):
    """Status of moderation review."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_BLOCKED = "auto_blocked"


class ContentType(str, Enum):
    """Type of content being moderated."""

    MESSAGE = "message"
    PHOTO = "photo"
    PROFILE_BIO = "profile_bio"


class ReportReason(str, Enum):
    """Reason for reporting content or user."""

    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    SPAM = "spam"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    FAKE_PROFILE = "fake_profile"
    UNDERAGE = "underage"
    OTHER = "other"


class ModerationRecord(Base):
    """
    Record of content moderation screening.

    Stores screening results from Perspective API or Rekognition
    for audit trail and review queue.
    """

    __tablename__ = "moderation_records"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Content information
    content_type: Mapped[ContentType] = mapped_column(String(50), nullable=False, index=True)
    content_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # ID of message/photo/etc
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_url: Mapped[str | None] = mapped_column(String(512), nullable=True)  # For photos

    # Moderation scores (Perspective API)
    toxicity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    severe_toxicity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    identity_attack_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    threat_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sexually_explicit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    profanity_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # AWS Rekognition scores (for photos)
    rekognition_labels: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rekognition_moderation: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Review status
    status: Mapped[ModerationStatus] = mapped_column(
        String(50), default=ModerationStatus.PENDING, nullable=False, index=True
    )
    max_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, index=True
    )  # Highest toxicity score
    flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Review data
    reviewed_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        """String representation of ModerationRecord."""
        return f"<ModerationRecord(id={self.id}, type={self.content_type}, status={self.status}, flagged={self.flagged})>"


class UserReport(Base):
    """
    User report for inappropriate content or behavior.

    Allows users to report other users or content.
    """

    __tablename__ = "user_reports"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Reporter and reported user
    reporter_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    reported_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Report details
    reason: Mapped[ReportReason] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[ContentType | None] = mapped_column(String(50), nullable=True)
    content_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Review status
    status: Mapped[ModerationStatus] = mapped_column(
        String(50), default=ModerationStatus.PENDING, nullable=False, index=True
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Action taken
    action_taken: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        """String representation of UserReport."""
        return f"<UserReport(id={self.id}, reason={self.reason}, status={self.status})>"


class UserBlock(Base):
    """
    User blocking relationship.

    When user_id blocks blocked_user_id, they cannot see each other.
    """

    __tablename__ = "user_blocks"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Blocking relationship
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    blocked_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Optional context
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """String representation of UserBlock."""
        return f"<UserBlock(id={self.id}, user={self.user_id}, blocked={self.blocked_user_id})>"


class ModerationAppeal(Base):
    """
    Appeal for moderation decision.

    Users can appeal auto-blocked or rejected content.
    """

    __tablename__ = "moderation_appeals"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Reference to original moderation record or report
    moderation_record_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    user_report_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # User appealing
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Appeal details
    appeal_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Review status
    status: Mapped[ModerationStatus] = mapped_column(
        String(50), default=ModerationStatus.PENDING, nullable=False, index=True
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Decision
    appeal_granted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        """String representation of ModerationAppeal."""
        return f"<ModerationAppeal(id={self.id}, user={self.user_id}, status={self.status})>"
