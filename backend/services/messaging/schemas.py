"""
Messaging service schemas.

Pydantic schemas for messaging API requests and responses.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for creating a new message."""

    content: str = Field(..., min_length=1, max_length=5000, description="Message content")


class MessageResponse(BaseModel):
    """Schema for message response."""

    id: UUID
    from_user_id: UUID
    to_user_id: UUID
    content: str
    read_at: datetime | None
    sent_at: datetime

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    """Schema for conversation list response."""

    user_id: UUID
    last_message: MessageResponse | None
    unread_count: int


class MessageHistoryResponse(BaseModel):
    """Schema for paginated message history."""

    messages: list[MessageResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class WebSocketMessage(BaseModel):
    """Schema for WebSocket message events."""

    type: str = Field(..., description="Message type: message, typing, read, connection, error")
    data: dict = Field(default_factory=dict, description="Message data")


class TypingEvent(BaseModel):
    """Schema for typing indicator event."""

    user_id: UUID
    is_typing: bool


class ReadReceiptEvent(BaseModel):
    """Schema for read receipt event."""

    message_id: UUID
    read_at: datetime


class ReportRequest(BaseModel):
    """Schema for reporting a user/message."""

    reason: str = Field(..., min_length=10, max_length=500, description="Reason for reporting")
    message_id: UUID | None = Field(None, description="Optional message ID to report")


class ModerationResult(BaseModel):
    """Schema for content moderation result."""

    is_safe: bool
    toxicity_score: float
    flagged_attributes: list[str]
    action: str = Field(..., description="Action taken: pass, review, block")
