"""Match model for user matching and compatibility."""

from datetime import datetime
from uuid import UUID as UUID_TYPE
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Match(Base):
    """
    Match model for compatibility between users.

    Stores match relationships, compatibility scores, and match status.
    """

    __tablename__ = "matches"

    # Primary key
    id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Foreign keys to users (bidirectional match)
    user_a_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_b_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Compatibility score (0-100)
    compatibility_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Match status: pending, liked, passed, matched, unmatched
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("user_a_id != user_b_id", name="different_users"),
        CheckConstraint("compatibility_score >= 0 AND compatibility_score <= 100", name="valid_score"),
    )

    def __repr__(self) -> str:
        """String representation of Match."""
        return (
            f"<Match(id={self.id}, users={self.user_a_id}↔{self.user_b_id}, "
            f"score={self.compatibility_score:.1f}, status={self.status})>"
        )
