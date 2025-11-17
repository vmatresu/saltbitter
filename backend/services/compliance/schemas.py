"""Pydantic schemas for GDPR compliance API requests and responses."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ConsentRequest(BaseModel):
    """Request model for granting or withdrawing consent."""

    consent_type: str = Field(
        ...,
        description="Type of consent: profile_data, psychological_assessment, ai_features, marketing",
    )
    granted: bool = Field(..., description="True to grant consent, False to withdraw")
    consent_text: str | None = Field(None, description="Text of consent shown to user")


class ConsentResponse(BaseModel):
    """Response model for consent status."""

    id: UUID
    user_id: UUID
    consent_type: str
    granted: bool
    timestamp: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class ConsentStatusResponse(BaseModel):
    """Response model for all consent statuses for a user."""

    consents: dict[str, bool] = Field(
        ..., description="Map of consent type to granted status"
    )


class DataExportResponse(BaseModel):
    """Response model for GDPR data export."""

    user_data: dict[str, Any] = Field(..., description="Complete user data export")
    exported_at: datetime
    format_version: str = "1.0"


class AccountDeletionRequest(BaseModel):
    """Request model for account deletion."""

    confirmation_email: EmailStr = Field(
        ..., description="User must confirm email for deletion"
    )
    reason: str | None = Field(None, description="Optional reason for deletion")


class AccountDeletionResponse(BaseModel):
    """Response model for account deletion request."""

    deletion_scheduled: bool
    scheduled_date: datetime
    grace_period_days: int = 30
    message: str


class BreachNotification(BaseModel):
    """Model for data breach notification."""

    breach_id: UUID
    detected_at: datetime
    severity: str = Field(..., description="low, medium, high, critical")
    affected_users_count: int
    data_categories: list[str]
    description: str
    mitigation_steps: str


class PrivacyPolicyResponse(BaseModel):
    """Response model for privacy policy."""

    content: str
    version: str
    effective_date: datetime
    last_updated: datetime


class DPOContactResponse(BaseModel):
    """Response model for Data Protection Officer contact information."""

    name: str
    email: EmailStr
    phone: str | None
    address: str | None
