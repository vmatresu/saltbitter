"""Compliance models for GDPR, EU AI Act, and regulatory tracking."""

from datetime import datetime
from uuid import UUID as UUID_TYPE
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class ConsentLog(Base):
    """
    Consent log model for GDPR compliance.

    Tracks all user consent events for data processing, especially psychological data
    (GDPR Article 9 - special category data).
    """

    __tablename__ = "consent_logs"

    # Primary key
    id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Foreign key to users table
    user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Consent type: profile_data, psychological_assessment, ai_features, marketing, data_sharing
    consent_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Consent granted or withdrawn
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Consent metadata
    consent_text: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Text of consent shown to user
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # For audit trail

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """String representation of ConsentLog."""
        return (
            f"<ConsentLog(user_id={self.user_id}, type={self.consent_type}, "
            f"granted={self.granted}, at={self.timestamp})>"
        )


class ComplianceLog(Base):
    """
    Compliance log model for regulatory audit trail.

    Tracks all compliance-relevant actions including data access, deletion requests,
    AI interactions, and other regulatory events.
    """

    __tablename__ = "compliance_logs"

    # Primary key
    id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Foreign key to users table
    user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Action type: data_export, data_deletion, ai_disclosure, opt_out, breach_notification
    action_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Action metadata stored as JSONB for flexibility
    action_metadata: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.jsonb_build_object()
    )

    # Regulatory framework: gdpr, eu_ai_act, ccpa, sb_243
    regulatory_framework: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        """String representation of ComplianceLog."""
        return (
            f"<ComplianceLog(user_id={self.user_id}, action={self.action_type}, "
            f"framework={self.regulatory_framework}, at={self.timestamp})>"
        )
