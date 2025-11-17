"""Event models for virtual events and community features."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID as UUID_TYPE
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Event(Base):
    """
    Event model for virtual events and community gatherings.

    Supports both free and paid events for user engagement.
    """

    __tablename__ = "events"

    # Primary key
    id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Event details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Event type: community_chat, speed_dating, workshop, ama
    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Scheduling
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Capacity and pricing
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0.00)

    # Event metadata
    host_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(512), nullable=True)  # Zoom/Google Meet link

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="valid_event_duration"),
        CheckConstraint("capacity > 0", name="positive_capacity"),
        CheckConstraint("price >= 0", name="non_negative_price"),
    )

    def __repr__(self) -> str:
        """String representation of Event."""
        return f"<Event(id={self.id}, title={self.title}, type={self.type}, start={self.start_time})>"


class EventRegistration(Base):
    """
    Event registration model for tracking user attendance.

    Links users to events they've registered for.
    """

    __tablename__ = "event_registrations"

    # Primary key
    id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Foreign keys
    event_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Registration status: registered, attended, no_show, canceled
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="registered")

    # Payment tracking (if paid event)
    payment_id: Mapped[UUID_TYPE | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """String representation of EventRegistration."""
        return f"<EventRegistration(event_id={self.event_id}, user_id={self.user_id}, status={self.status})>"
