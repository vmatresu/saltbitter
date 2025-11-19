"""Pydantic schemas for moderation service."""

from datetime import datetime
from typing import Dict, List
from uuid import UUID

from pydantic import BaseModel, Field

from backend.database.models.moderation import ContentType, ModerationStatus, ReportReason


# Text screening request/response
class TextScreenRequest(BaseModel):
    """Request to screen text content."""

    text: str = Field(..., min_length=1, max_length=20000, description="Text to screen")
    content_type: ContentType = Field(..., description="Type of content")
    user_id: UUID = Field(..., description="ID of user who created the content")


class TextScreenResponse(BaseModel):
    """Response from text screening."""

    allowed: bool = Field(..., description="Whether content is allowed")
    flagged: bool = Field(..., description="Whether content was flagged for review")
    auto_blocked: bool = Field(..., description="Whether content was auto-blocked")
    scores: Dict[str, float] = Field(..., description="Toxicity scores by attribute")
    max_score: float = Field(..., description="Highest toxicity score")
    moderation_record_id: UUID | None = Field(None, description="ID of moderation record")


# Photo screening request/response
class PhotoScreenRequest(BaseModel):
    """Request to screen photo content."""

    photo_url: str = Field(..., description="URL or S3 key of photo")
    user_id: UUID = Field(..., description="ID of user who uploaded the photo")


class PhotoScreenResponse(BaseModel):
    """Response from photo screening."""

    allowed: bool = Field(..., description="Whether photo is allowed")
    flagged: bool = Field(..., description="Whether photo was flagged for review")
    auto_blocked: bool = Field(..., description="Whether photo was auto-blocked")
    labels: Dict[str, List[Dict[str, float]]] = Field(..., description="Moderation labels by category")
    max_confidence: float = Field(..., description="Highest confidence score")
    has_face: bool = Field(..., description="Whether a face was detected")
    moderation_record_id: UUID | None = Field(None, description="ID of moderation record")


# User report schemas
class CreateReportRequest(BaseModel):
    """Request to create a user report."""

    reported_user_id: UUID = Field(..., description="ID of user being reported")
    reason: ReportReason = Field(..., description="Reason for report")
    description: str | None = Field(None, max_length=1000, description="Optional detailed description")
    content_type: ContentType | None = Field(None, description="Type of content being reported")
    content_id: UUID | None = Field(None, description="ID of specific content (message, photo, etc.)")


class ReportResponse(BaseModel):
    """Response after creating a report."""

    id: UUID = Field(..., description="Report ID")
    status: ModerationStatus = Field(..., description="Current status")
    created_at: datetime = Field(..., description="When report was created")

    class Config:
        """Pydantic config."""

        from_attributes = True


# Block user schemas
class BlockUserRequest(BaseModel):
    """Request to block a user."""

    blocked_user_id: UUID = Field(..., description="ID of user to block")
    reason: str | None = Field(None, max_length=255, description="Optional reason for blocking")


class BlockResponse(BaseModel):
    """Response after blocking a user."""

    id: UUID = Field(..., description="Block ID")
    user_id: UUID = Field(..., description="User who initiated the block")
    blocked_user_id: UUID = Field(..., description="User who was blocked")
    created_at: datetime = Field(..., description="When block was created")

    class Config:
        """Pydantic config."""

        from_attributes = True


# Moderation queue schemas
class ModerationQueueItem(BaseModel):
    """Item in moderation review queue."""

    id: UUID = Field(..., description="Moderation record ID")
    content_type: ContentType = Field(..., description="Type of content")
    user_id: UUID = Field(..., description="User who created content")
    content_text: str | None = Field(None, description="Text content (if applicable)")
    content_url: str | None = Field(None, description="Photo URL (if applicable)")
    max_score: float = Field(..., description="Highest toxicity/confidence score")
    flagged: bool = Field(..., description="Whether flagged for review")
    status: ModerationStatus = Field(..., description="Current status")
    created_at: datetime = Field(..., description="When content was screened")

    class Config:
        """Pydantic config."""

        from_attributes = True


class ModerationQueueResponse(BaseModel):
    """Response with moderation queue items."""

    items: List[ModerationQueueItem] = Field(..., description="Queue items")
    total: int = Field(..., description="Total items in queue")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")


# Review decision schemas
class ReviewDecisionRequest(BaseModel):
    """Request to review moderation record."""

    approved: bool = Field(..., description="Whether to approve the content")
    notes: str | None = Field(None, max_length=1000, description="Review notes")


class ReviewDecisionResponse(BaseModel):
    """Response after reviewing content."""

    id: UUID = Field(..., description="Moderation record ID")
    status: ModerationStatus = Field(..., description="Updated status")
    reviewed_at: datetime = Field(..., description="When review was completed")


# Appeal schemas
class CreateAppealRequest(BaseModel):
    """Request to create an appeal."""

    moderation_record_id: UUID | None = Field(None, description="ID of moderation record being appealed")
    user_report_id: UUID | None = Field(None, description="ID of user report being appealed")
    appeal_text: str = Field(..., min_length=10, max_length=2000, description="Explanation for appeal")


class AppealResponse(BaseModel):
    """Response after creating an appeal."""

    id: UUID = Field(..., description="Appeal ID")
    status: ModerationStatus = Field(..., description="Current status")
    created_at: datetime = Field(..., description="When appeal was created")

    class Config:
        """Pydantic config."""

        from_attributes = True


# General response
class MessageResponse(BaseModel):
    """Generic message response."""

    message: str = Field(..., description="Response message")
