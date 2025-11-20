"""User blocking functionality."""

from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.moderation import ModerationAuditLog, UserBlock, ModerationAction


async def create_block(
    db: AsyncSession, blocker_id: UUID, blocked_id: UUID, reason: str | None = None
) -> UserBlock:
    """
    Create a user block.

    Args:
        db: Database session
        blocker_id: ID of user creating the block
        blocked_id: ID of user being blocked
        reason: Optional reason for blocking

    Returns:
        Created UserBlock instance

    Raises:
        ValueError: If trying to block oneself
    """
    if blocker_id == blocked_id:
        raise ValueError("Cannot block yourself")

    # Check if block already exists
    existing_block = await db.execute(
        select(UserBlock).where(
            and_(UserBlock.blocker_id == blocker_id, UserBlock.blocked_id == blocked_id)
        )
    )
    if existing_block.scalar_one_or_none():
        raise ValueError("User is already blocked")

    # Create block
    block = UserBlock(blocker_id=blocker_id, blocked_id=blocked_id, reason=reason)
    db.add(block)

    # Create audit log entry
    audit_log = ModerationAuditLog(
        action_type=ModerationAction.USER_BLOCKED,
        content_type="user",
        content_id=blocked_id,
        user_id=blocked_id,
        moderator_id=blocker_id,
        reason=reason,
        metadata={"blocker_id": str(blocker_id), "blocked_id": str(blocked_id)},
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(block)

    return block


async def remove_block(db: AsyncSession, blocker_id: UUID, blocked_id: UUID) -> bool:
    """
    Remove a user block.

    Args:
        db: Database session
        blocker_id: ID of user who created the block
        blocked_id: ID of blocked user

    Returns:
        True if block was removed, False if block didn't exist
    """
    # Find existing block
    result = await db.execute(
        select(UserBlock).where(
            and_(UserBlock.blocker_id == blocker_id, UserBlock.blocked_id == blocked_id)
        )
    )
    block = result.scalar_one_or_none()

    if not block:
        return False

    # Delete block
    await db.delete(block)
    await db.commit()

    return True


async def is_blocked(db: AsyncSession, user_id: UUID, other_user_id: UUID) -> bool:
    """
    Check if two users have a blocking relationship.

    Args:
        db: Database session
        user_id: First user ID
        other_user_id: Second user ID

    Returns:
        True if either user has blocked the other
    """
    result = await db.execute(
        select(UserBlock).where(
            or_(
                and_(UserBlock.blocker_id == user_id, UserBlock.blocked_id == other_user_id),
                and_(UserBlock.blocker_id == other_user_id, UserBlock.blocked_id == user_id),
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def get_blocked_users(db: AsyncSession, user_id: UUID) -> list[UUID]:
    """
    Get list of users blocked by a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of blocked user IDs
    """
    result = await db.execute(select(UserBlock.blocked_id).where(UserBlock.blocker_id == user_id))
    return [row[0] for row in result.all()]


async def get_blocked_count(db: AsyncSession, user_id: UUID) -> int:
    """
    Get count of users blocked by a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Number of blocked users
    """
    result = await db.execute(
        select(UserBlock).where(UserBlock.blocker_id == user_id)
    )
    return len(result.all())
