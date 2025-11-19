"""Pydantic schemas for moderation service."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from database.models.moderation import ModerationAction, ModerationStatus, ReportReason


# Text screening schemas
class TextScreenRequest(BaseModel):
    """Request to screen text content."""

    text: str = Field(..., min_length=1, max_length=10000, description="Text content to screen")
    context_type: str = Field(
        ..., description="Type of content (message, bio, comment)"
    )  # message, bio, comment


class PerspectiveScore(BaseModel):
    """Perspective API score for a single attribute."""

    score: float = Field(..., ge=0.0, le=1.0, description="Score from 0 to 1")
    summary_score: float = Field(..., ge=0.0, le=1.0, description="Summary score")


class TextScreenResponse(BaseModel):
    """Response from text screening."""

    allowed: bool = Field(..., description="Whether content is allowed")
    flagged: bool = Field(..., description="Whether content was flagged for review")
    auto_blocked: bool = Field(..., description="Whether content was auto-blocked")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall toxicity score")
    scores: dict[str, PerspectiveScore] = Field(..., description="Individual attribute scores")
    reason: str | None = Field(None, description="Reason for blocking/flagging")


# Photo screening schemas
class PhotoScreenRequest(BaseModel):
    """Request to screen photo content."""

    photo_url: str = Field(..., description="URL of photo to screen")
    user_id: UUID = Field(..., description="ID of user uploading photo")


class PhotoScreenResponse(BaseModel):
    """Response from photo screening."""

    allowed: bool = Field(..., description="Whether photo is allowed")
    flagged: bool = Field(..., description="Whether photo was flagged for review")
    labels: list[str] = Field(default_factory=list, description="Detected labels")
    moderation_labels: list[str] = Field(
        default_factory=list, description="Inappropriate content labels"
    )
    confidence: float = Field(..., ge=0.0, le=100.0, description="Detection confidence")
    reason: str | None = Field(None, description="Reason for blocking/flagging")


# User reporting schemas
class CreateReportRequest(BaseModel):
    """Request to create a user report."""

    reported_user_id: UUID = Field(..., description="ID of user being reported")
    content_type: str = Field(..., description="Type of content (message, profile, behavior)")
    content_id: UUID | None = Field(None, description="ID of specific content being reported")
    reason: ReportReason = Field(..., description="Reason for report")
    description: str = Field(
        ..., min_length=10, max_length=1000, description="Description of the issue"
    )


class ReportResponse(BaseModel):
    """Response after creating a report."""

    id: UUID = Field(..., description="Report ID")
    status: ModerationStatus = Field(..., description="Report status")
    created_at: datetime = Field(..., description="When report was created")
    message: str = Field(..., description="Confirmation message")

    class Config:
        from_attributes = True


# User blocking schemas
class CreateBlockRequest(BaseModel):
    """Request to block a user."""

    blocked_user_id: UUID = Field(..., description="ID of user to block")
    reason: str | None = Field(None, max_length=500, description="Optional reason for blocking")


class BlockResponse(BaseModel):
    """Response after blocking a user."""

    id: UUID = Field(..., description="Block ID")
    blocker_id: UUID = Field(..., description="ID of user who blocked")
    blocked_id: UUID = Field(..., description="ID of blocked user")
    created_at: datetime = Field(..., description="When block was created")

    class Config:
        from_attributes = True


# Moderation queue schemas
class QueueItemResponse(BaseModel):
    """Moderation queue item for review."""

    id: UUID = Field(..., description="Queue item ID")
    content_type: str = Field(..., description="Type of content")
    content_id: UUID = Field(..., description="ID of content")
    content_text: str | None = Field(None, description="Text content if applicable")
    content_url: str | None = Field(None, description="URL if applicable")
    user_id: UUID = Field(..., description="User who created content")
    overall_score: float = Field(..., description="Automated screening score")
    perspective_scores: dict | None = Field(None, description="Perspective API scores")
    rekognition_labels: dict | None = Field(None, description="Rekognition labels")
    status: ModerationStatus = Field(..., description="Review status")
    created_at: datetime = Field(..., description="When flagged")

    class Config:
        from_attributes = True


class ReviewDecisionRequest(BaseModel):
    """Request to review a queue item."""

    action: ModerationAction = Field(..., description="Action to take")
    notes: str | None = Field(None, max_length=1000, description="Moderator notes")


class ReviewDecisionResponse(BaseModel):
    """Response after reviewing content."""

    id: UUID = Field(..., description="Queue item ID")
    status: ModerationStatus = Field(..., description="New status")
    action_taken: ModerationAction = Field(..., description="Action taken")
    reviewed_at: datetime = Field(..., description="When reviewed")

    class Config:
        from_attributes = True


# Appeal schemas
class CreateAppealRequest(BaseModel):
    """Request to appeal a moderation decision."""

    moderation_queue_id: UUID | None = Field(
        None, description="ID of moderation queue item if applicable"
    )
    user_report_id: UUID | None = Field(None, description="ID of user report if applicable")
    reason: str = Field(..., min_length=10, max_length=1000, description="Reason for appeal")
    additional_context: str | None = Field(
        None, max_length=2000, description="Additional context"
    )


class AppealResponse(BaseModel):
    """Response after creating an appeal."""

    id: UUID = Field(..., description="Appeal ID")
    status: ModerationStatus = Field(..., description="Appeal status")
    created_at: datetime = Field(..., description="When appeal was created")
    message: str = Field(..., description="Confirmation message")

    class Config:
        from_attributes = True


# Admin dashboard schemas
class ModerationStatsResponse(BaseModel):
    """Statistics for moderation dashboard."""

    pending_queue_items: int = Field(..., description="Items awaiting review")
    pending_reports: int = Field(..., description="Reports awaiting review")
    pending_appeals: int = Field(..., description="Appeals awaiting review")
    auto_blocked_today: int = Field(..., description="Auto-blocked items today")
    manual_reviews_today: int = Field(..., description="Manual reviews today")
    active_blocks: int = Field(..., description="Active user blocks")


class AuditLogEntry(BaseModel):
    """Single audit log entry."""

    id: UUID = Field(..., description="Log entry ID")
    action_type: ModerationAction = Field(..., description="Type of action")
    content_type: str = Field(..., description="Type of content")
    user_id: UUID = Field(..., description="Affected user ID")
    moderator_id: UUID | None = Field(None, description="Moderator who took action")
    reason: str | None = Field(None, description="Reason for action")
    created_at: datetime = Field(..., description="When action occurred")

    class Config:
        from_attributes = True
