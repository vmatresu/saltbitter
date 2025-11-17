"""Message model for user-to-user messaging."""

from datetime import datetime
from uuid import UUID as UUID_TYPE
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Message(Base):
    """
    Message model for direct messaging between matched users.

    Stores message content, sender, recipient, and timestamps.
    """

    __tablename__ = "messages"

    # Primary key
    id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Foreign keys
    from_user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    to_user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Message content (encrypted in production)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Read status
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        """String representation of Message."""
        return f"<Message(id={self.id}, from={self.from_user_id}, to={self.to_user_id})>"
