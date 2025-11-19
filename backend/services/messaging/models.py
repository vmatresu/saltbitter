"""
Messaging service database models.

Additional models for messaging functionality beyond the core Message model.
"""

from datetime import datetime
from uuid import UUID as UUID_TYPE
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.models import Base


class BlockedUser(Base):
    """
    Model for tracking blocked users.

    When a user blocks another, they cannot see each other or exchange messages.
    """

    __tablename__ = "blocked_users"

    # Primary key
    id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # User who initiated the block
    blocker_user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # User who was blocked
    blocked_user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Timestamp
    blocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """String representation of BlockedUser."""
        return f"<BlockedUser(blocker={self.blocker_user_id}, blocked={self.blocked_user_id})>"


class MessageReport(Base):
    """
    Model for reporting inappropriate messages or users.

    Supports content moderation and safety features.
    """

    __tablename__ = "message_reports"

    # Primary key
    id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Reporter
    reporter_user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Reported user
    reported_user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Optional specific message
    message_id: Mapped[UUID_TYPE | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )

    # Report details
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Moderation status
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="pending", server_default="pending"
    )  # pending, reviewed, resolved

    # Timestamps
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        """String representation of MessageReport."""
        return f"<MessageReport(id={self.id}, status={self.status})>"
