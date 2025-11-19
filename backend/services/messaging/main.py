"""
Messaging service main routes.

Provides REST API endpoints and WebSocket endpoint for real-time messaging.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, status
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import Message, User
from services.auth.routes import get_current_user
from .models import BlockedUser, MessageReport
from .schemas import (
    ConversationListResponse,
    MessageHistoryResponse,
    MessageResponse,
    ReportRequest,
)
from .websocket import handle_websocket_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["messaging"])


@router.websocket("/ws/messages/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, user_id: UUID, db: AsyncSession = Depends(get_db)
) -> None:
    """
    WebSocket endpoint for real-time messaging.

    Handles bidirectional communication for:
    - Sending and receiving messages
    - Typing indicators
    - Read receipts
    - Connection status

    Args:
        websocket: WebSocket connection
        user_id: Authenticated user ID
        db: Database session
    """
    await handle_websocket_connection(websocket, user_id, db)


@router.get("/", response_model=list[ConversationListResponse])
async def get_conversations(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[ConversationListResponse]:
    """
    Get list of conversations for the current user.

    Returns list of users with recent message history, sorted by most recent.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        List of conversations with last message and unread count
    """
    user_id = current_user.id

    # Get all unique conversation partners
    stmt = (
        select(Message)
        .where(or_(Message.from_user_id == user_id, Message.to_user_id == user_id))
        .order_by(desc(Message.sent_at))
    )

    result = await db.execute(stmt)
    messages = result.scalars().all()

    # Group by conversation partner
    conversations: dict[UUID, dict] = {}

    for message in messages:
        partner_id = (
            message.to_user_id if message.from_user_id == user_id else message.from_user_id
        )

        if partner_id not in conversations:
            conversations[partner_id] = {
                "user_id": partner_id,
                "last_message": message,
                "unread_count": 0,
            }

        # Count unread messages from partner
        if message.to_user_id == user_id and message.read_at is None:
            conversations[partner_id]["unread_count"] += 1

    # Convert to response format
    conversation_list = []
    for conv_data in conversations.values():
        conversation_list.append(
            ConversationListResponse(
                user_id=conv_data["user_id"],
                last_message=MessageResponse.model_validate(conv_data["last_message"])
                if conv_data["last_message"]
                else None,
                unread_count=conv_data["unread_count"],
            )
        )

    return conversation_list


@router.get("/{match_id}", response_model=MessageHistoryResponse)
async def get_message_history(
    match_id: UUID,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageHistoryResponse:
    """
    Get paginated message history with a specific match.

    Args:
        match_id: ID of the other user
        page: Page number (1-indexed)
        page_size: Number of messages per page
        current_user: Authenticated user
        db: Database session

    Returns:
        Paginated message history
    """
    user_id = current_user.id

    # Check if users are blocked
    blocked_stmt = select(BlockedUser).where(
        or_(
            and_(BlockedUser.blocker_user_id == user_id, BlockedUser.blocked_user_id == match_id),
            and_(BlockedUser.blocker_user_id == match_id, BlockedUser.blocked_user_id == user_id),
        )
    )
    blocked_result = await db.execute(blocked_stmt)
    if blocked_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view messages with blocked user"
        )

    # Get total count
    count_stmt = select(func.count(Message.id)).where(
        or_(
            and_(Message.from_user_id == user_id, Message.to_user_id == match_id),
            and_(Message.from_user_id == match_id, Message.to_user_id == user_id),
        )
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Get messages
    offset = (page - 1) * page_size
    stmt = (
        select(Message)
        .where(
            or_(
                and_(Message.from_user_id == user_id, Message.to_user_id == match_id),
                and_(Message.from_user_id == match_id, Message.to_user_id == user_id),
            )
        )
        .order_by(desc(Message.sent_at))
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(stmt)
    messages = result.scalars().all()

    # Convert to response
    message_responses = [MessageResponse.model_validate(msg) for msg in messages]

    return MessageHistoryResponse(
        messages=message_responses,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("/{match_id}/report", status_code=status.HTTP_201_CREATED)
async def report_user_or_message(
    match_id: UUID,
    report: ReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Report a user or specific message for inappropriate behavior.

    Args:
        match_id: ID of the user to report
        report: Report details
        current_user: Authenticated user
        db: Database session

    Returns:
        Confirmation message
    """
    # Create report
    message_report = MessageReport(
        reporter_user_id=current_user.id,
        reported_user_id=match_id,
        message_id=report.message_id,
        reason=report.reason,
        status="pending",
    )

    db.add(message_report)
    await db.commit()

    logger.info(
        f"User {current_user.id} reported user {match_id}" + (f", message {report.message_id}" if report.message_id else "")
    )

    return {
        "message": "Report submitted successfully. Our team will review it shortly.",
        "report_id": str(message_report.id),
    }


@router.post("/blocks/{user_id}", status_code=status.HTTP_201_CREATED)
async def block_user(
    user_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """
    Block a user to prevent messaging and profile visibility.

    Args:
        user_id: ID of the user to block
        current_user: Authenticated user
        db: Database session

    Returns:
        Confirmation message
    """
    # Check if already blocked
    stmt = select(BlockedUser).where(
        and_(
            BlockedUser.blocker_user_id == current_user.id, BlockedUser.blocked_user_id == user_id
        )
    )
    result = await db.execute(stmt)
    existing_block = result.scalar_one_or_none()

    if existing_block:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already blocked")

    # Create block
    block = BlockedUser(blocker_user_id=current_user.id, blocked_user_id=user_id)
    db.add(block)
    await db.commit()

    logger.info(f"User {current_user.id} blocked user {user_id}")

    return {"message": "User blocked successfully"}


@router.delete("/blocks/{user_id}", status_code=status.HTTP_200_OK)
async def unblock_user(
    user_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """
    Unblock a previously blocked user.

    Args:
        user_id: ID of the user to unblock
        current_user: Authenticated user
        db: Database session

    Returns:
        Confirmation message
    """
    # Find and delete block
    stmt = select(BlockedUser).where(
        and_(
            BlockedUser.blocker_user_id == current_user.id, BlockedUser.blocked_user_id == user_id
        )
    )
    result = await db.execute(stmt)
    block = result.scalar_one_or_none()

    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block not found")

    await db.delete(block)
    await db.commit()

    logger.info(f"User {current_user.id} unblocked user {user_id}")

    return {"message": "User unblocked successfully"}
