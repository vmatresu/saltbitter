"""Attachment assessment model for psychology-based matching."""

from datetime import datetime
from uuid import UUID as UUID_TYPE
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class AttachmentAssessment(Base):
    """
    Attachment theory assessment model.

    Stores user's attachment style assessment results based on anxiety and avoidance scores.
    This is core to the platform's psychology-informed matching algorithm.
    """

    __tablename__ = "attachment_assessments"

    # Primary key
    id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Foreign key to users table
    user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,  # One assessment per user (latest version)
    )

    # Attachment theory scores (0-100 scale)
    anxiety_score: Mapped[float] = mapped_column(Float, nullable=False)
    avoidance_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Derived attachment style: secure, anxious, avoidant, fearful-avoidant
    style: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Assessment metadata
    assessment_version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="1.0"
    )  # For tracking assessment iterations
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=25)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """String representation of AttachmentAssessment."""
        return (
            f"<AttachmentAssessment(user_id={self.user_id}, style={self.style}, "
            f"anxiety={self.anxiety_score:.1f}, avoidance={self.avoidance_score:.1f})>"
        )
