"""Moderation models for content safety and user reporting."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class ModerationStatus(str, Enum):
    """Moderation review status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPEALED = "appealed"


class ModerationAction(str, Enum):
    """Type of moderation action taken."""

    AUTO_BLOCKED = "auto_blocked"
    MANUAL_REVIEW = "manual_review"
    APPROVED = "approved"
    USER_BLOCKED = "user_blocked"
    CONTENT_REMOVED = "content_removed"
    APPEAL_GRANTED = "appeal_granted"
    APPEAL_DENIED = "appeal_denied"


class ReportReason(str, Enum):
    """Reasons for reporting content or users."""

    HARASSMENT = "harassment"
    SPAM = "spam"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    FAKE_PROFILE = "fake_profile"
    UNDERAGE = "underage"
    SCAM = "scam"
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    OTHER = "other"


class ModerationQueue(Base):
    """
    Moderation queue for flagged content requiring manual review.

    Stores messages, photos, and profiles flagged by automated screening
    or user reports for moderator review.
    """

    __tablename__ = "moderation_queue"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Content being moderated
    content_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # message, photo, profile
    content_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # For messages
    content_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # For photos

    # User who created the content
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Automated screening scores
    perspective_scores: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )  # Perspective API scores
    rekognition_labels: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )  # AWS Rekognition results
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)

    # Review status
    status: Mapped[ModerationStatus] = mapped_column(
        String(50), default=ModerationStatus.PENDING, nullable=False, index=True
    )

    # Moderator review
    reviewed_by: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    moderator_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_taken: Mapped[ModerationAction | None] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class UserReport(Base):
    """
    User reports of inappropriate content or behavior.

    Allows users to report other users, messages, or profiles.
    """

    __tablename__ = "user_reports"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Reporter
    reporter_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Reported user
    reported_user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # What's being reported
    content_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # message, profile, behavior
    content_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Report details
    reason: Mapped[ReportReason] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Review status
    status: Mapped[ModerationStatus] = mapped_column(
        String(50), default=ModerationStatus.PENDING, nullable=False, index=True
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    moderator_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_taken: Mapped[ModerationAction | None] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class UserBlock(Base):
    """
    User blocking relationships.

    Allows users to block other users from seeing their profile or messaging them.
    """

    __tablename__ = "user_blocks"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Blocking relationship
    blocker_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    blocked_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Optional reason
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Unique constraint on blocker-blocked pair
    __table_args__ = (
        # Add unique constraint and index
        {"schema": None},
    )


class ModerationAppeal(Base):
    """
    Appeals for moderation decisions.

    Allows users to appeal moderation actions taken against their content.
    """

    __tablename__ = "moderation_appeals"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Appeal for
    moderation_queue_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("moderation_queue.id"), nullable=True
    )
    user_report_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_reports.id"), nullable=True
    )

    # Appealing user
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Appeal details
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    additional_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Review status
    status: Mapped[ModerationStatus] = mapped_column(
        String(50), default=ModerationStatus.PENDING, nullable=False, index=True
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision: Mapped[ModerationAction | None] = mapped_column(String(50), nullable=True)
    moderator_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ModerationAuditLog(Base):
    """
    Audit trail of all moderation actions.

    Logs all moderation decisions and actions for compliance and review.
    """

    __tablename__ = "moderation_audit_logs"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Action details
    action_type: Mapped[ModerationAction] = mapped_column(String(50), nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Involved users
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    moderator_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Action details
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
