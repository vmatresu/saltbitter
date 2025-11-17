"""Subscription and payment models for monetization."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID as UUID_TYPE
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Subscription(Base):
    """
    Subscription model for premium tiers.

    Tracks user subscriptions, tiers, and Stripe integration.
    """

    __tablename__ = "subscriptions"

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
        unique=True,  # One active subscription per user
    )

    # Subscription tier: free, premium ($12.99), elite ($29.99)
    tier: Mapped[str] = mapped_column(String(50), nullable=False, default="free")

    # Stripe integration
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Subscription status: active, canceled, past_due, trialing
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)

    # Billing period
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """String representation of Subscription."""
        return f"<Subscription(user_id={self.user_id}, tier={self.tier}, status={self.status})>"


class Payment(Base):
    """
    Payment model for transaction history.

    Tracks all payments including subscriptions and microtransactions.
    """

    __tablename__ = "payments"

    # Primary key
    id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Foreign key to users table
    user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Payment amount (USD)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Payment type: subscription, profile_boost, super_like, ai_icebreaker, event_ticket
    type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Stripe integration
    stripe_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    stripe_invoice_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Payment status: succeeded, pending, failed, refunded
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        """String representation of Payment."""
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount=${self.amount}, type={self.type})>"
