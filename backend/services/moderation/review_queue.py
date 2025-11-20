"""Moderation review queue management."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.moderation import (
    ModerationAction,
    ModerationAppeal,
    ModerationAuditLog,
    ModerationQueue,
    ModerationStatus,
)


async def add_to_queue(
    db: AsyncSession,
    content_type: str,
    content_id: UUID,
    user_id: UUID,
    overall_score: float,
    content_text: str | None = None,
    content_url: str | None = None,
    perspective_scores: dict | None = None,
    rekognition_labels: dict | None = None,
) -> ModerationQueue:
    """
    Add content to moderation queue.

    Args:
        db: Database session
        content_type: Type of content (message, photo, profile)
        content_id: ID of content
        user_id: ID of user who created content
        overall_score: Overall moderation score
        content_text: Optional text content
        content_url: Optional URL content
        perspective_scores: Optional Perspective API scores
        rekognition_labels: Optional Rekognition labels

    Returns:
        Created ModerationQueue instance
    """
    queue_item = ModerationQueue(
        content_type=content_type,
        content_id=content_id,
        user_id=user_id,
        content_text=content_text,
        content_url=content_url,
        overall_score=overall_score,
        perspective_scores=perspective_scores,
        rekognition_labels=rekognition_labels,
        status=ModerationStatus.PENDING,
    )
    db.add(queue_item)

    # Create audit log entry
    audit_log = ModerationAuditLog(
        action_type=ModerationAction.MANUAL_REVIEW,
        content_type=content_type,
        content_id=content_id,
        user_id=user_id,
        reason="Content flagged for manual review",
        metadata={
            "overall_score": overall_score,
            "perspective_scores": perspective_scores,
            "rekognition_labels": rekognition_labels,
        },
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(queue_item)

    return queue_item


async def get_queue_item(db: AsyncSession, item_id: UUID) -> ModerationQueue | None:
    """
    Get a queue item by ID.

    Args:
        db: Database session
        item_id: Queue item ID

    Returns:
        ModerationQueue instance or None if not found
    """
    result = await db.execute(select(ModerationQueue).where(ModerationQueue.id == item_id))
    return result.scalar_one_or_none()


async def get_pending_queue(
    db: AsyncSession, limit: int = 50, offset: int = 0
) -> list[ModerationQueue]:
    """
    Get pending items from moderation queue.

    Args:
        db: Database session
        limit: Maximum number of items to return
        offset: Offset for pagination

    Returns:
        List of pending ModerationQueue instances
    """
    result = await db.execute(
        select(ModerationQueue)
        .where(ModerationQueue.status == ModerationStatus.PENDING)
        .order_by(ModerationQueue.overall_score.desc(), ModerationQueue.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def review_queue_item(
    db: AsyncSession,
    item_id: UUID,
    moderator_id: UUID,
    action: ModerationAction,
    notes: str | None = None,
) -> ModerationQueue:
    """
    Review a queue item.

    Args:
        db: Database session
        item_id: Queue item ID
        moderator_id: ID of moderator reviewing the item
        action: Action taken
        notes: Optional moderator notes

    Returns:
        Updated ModerationQueue instance

    Raises:
        ValueError: If queue item not found
    """
    item = await get_queue_item(db, item_id)
    if not item:
        raise ValueError(f"Queue item {item_id} not found")

    # Update queue item
    item.status = (
        ModerationStatus.APPROVED if action == ModerationAction.APPROVED else ModerationStatus.REJECTED
    )
    item.reviewed_by = moderator_id
    item.reviewed_at = datetime.utcnow()
    item.action_taken = action
    item.moderator_notes = notes

    # Create audit log entry
    audit_log = ModerationAuditLog(
        action_type=action,
        content_type=item.content_type,
        content_id=item.content_id,
        user_id=item.user_id,
        moderator_id=moderator_id,
        reason=notes,
        metadata={
            "queue_item_id": str(item_id),
            "overall_score": item.overall_score,
        },
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(item)

    return item


async def get_moderation_stats(db: AsyncSession) -> dict:
    """
    Get moderation statistics for dashboard.

    Args:
        db: Database session

    Returns:
        Dictionary of moderation statistics
    """
    # Count pending queue items
    pending_queue_result = await db.execute(
        select(func.count(ModerationQueue.id)).where(
            ModerationQueue.status == ModerationStatus.PENDING
        )
    )
    pending_queue = pending_queue_result.scalar() or 0

    # Count items auto-blocked today
    today = datetime.utcnow().date()
    auto_blocked_result = await db.execute(
        select(func.count(ModerationAuditLog.id)).where(
            ModerationAuditLog.action_type == ModerationAction.AUTO_BLOCKED,
            ModerationAuditLog.created_at >= today,
        )
    )
    auto_blocked_today = auto_blocked_result.scalar() or 0

    # Count manual reviews today
    manual_reviews_result = await db.execute(
        select(func.count(ModerationQueue.id)).where(
            ModerationQueue.reviewed_at >= today,
            ModerationQueue.reviewed_at.isnot(None),
        )
    )
    manual_reviews_today = manual_reviews_result.scalar() or 0

    return {
        "pending_queue_items": pending_queue,
        "auto_blocked_today": auto_blocked_today,
        "manual_reviews_today": manual_reviews_today,
    }


async def create_appeal(
    db: AsyncSession,
    user_id: UUID,
    moderation_queue_id: UUID | None,
    reason: str,
    additional_context: str | None = None,
) -> ModerationAppeal:
    """
    Create an appeal for a moderation decision.

    Args:
        db: Database session
        user_id: ID of user creating appeal
        moderation_queue_id: ID of moderation queue item being appealed
        reason: Reason for appeal
        additional_context: Optional additional context

    Returns:
        Created ModerationAppeal instance
    """
    appeal = ModerationAppeal(
        user_id=user_id,
        moderation_queue_id=moderation_queue_id,
        reason=reason,
        additional_context=additional_context,
        status=ModerationStatus.PENDING,
    )
    db.add(appeal)

    # Create audit log entry
    audit_log = ModerationAuditLog(
        action_type=ModerationAction.APPEAL_GRANTED,  # Will be updated when reviewed
        content_type="appeal",
        content_id=moderation_queue_id or user_id,
        user_id=user_id,
        reason="User filed appeal",
        metadata={
            "appeal_reason": reason,
            "additional_context": additional_context,
        },
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(appeal)

    return appeal


async def get_pending_appeals(
    db: AsyncSession, limit: int = 50, offset: int = 0
) -> list[ModerationAppeal]:
    """
    Get pending appeals.

    Args:
        db: Database session
        limit: Maximum number of appeals to return
        offset: Offset for pagination

    Returns:
        List of pending ModerationAppeal instances
    """
    result = await db.execute(
        select(ModerationAppeal)
        .where(ModerationAppeal.status == ModerationStatus.PENDING)
        .order_by(ModerationAppeal.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())
