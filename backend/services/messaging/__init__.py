"""
Messaging service module.

Provides real-time messaging functionality with WebSocket support,
content moderation, and push notifications.
"""

from .main import router as messaging_router
from .schemas import (
    ConversationListResponse,
    MessageCreate,
    MessageHistoryResponse,
    MessageResponse,
    ReportRequest,
)

__all__ = [
    "messaging_router",
    "MessageCreate",
    "MessageResponse",
    "ConversationListResponse",
    "MessageHistoryResponse",
    "ReportRequest",
]
