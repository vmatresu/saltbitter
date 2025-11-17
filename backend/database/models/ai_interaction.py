"""AI interaction model for transparency and compliance tracking."""

from datetime import datetime
from uuid import UUID as UUID_TYPE
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class AIInteraction(Base):
    """
    AI interaction model for compliance with EU AI Act and California SB 243.

    Tracks all AI companion interactions to ensure transparency and proper disclosure.
    """

    __tablename__ = "ai_interactions"

    # Primary key
    id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Foreign key to users table
    user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # AI type: practice_companion, relationship_coach, icebreaker_generator
    ai_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Compliance tracking
    disclosure_shown: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )  # EU AI Act Article 52
    user_consented: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # Explicit consent tracking

    # Interaction metadata
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # For grouping interactions

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """String representation of AIInteraction."""
        return (
            f"<AIInteraction(id={self.id}, user_id={self.user_id}, "
            f"type={self.ai_type}, disclosed={self.disclosure_shown})>"
        )
